''' module beeline '''
import functools
import os
import socket
from contextlib import contextmanager

from libhoney import Client
from beeline.trace import SynchronousTracer
from beeline.version import VERSION
from beeline import internal
# pyflakes
assert internal

USER_AGENT_ADDITION = "beeline-python/%s" % VERSION

# This is the global beeline created by init
_GBL = None

class Beeline(object):
    def __init__(self,
            writekey='', dataset='', service_name='',
            tracer=None, sample_rate=1, api_host='https://api.honeycomb.io',
            max_concurrent_batches=10, max_batch_size=100, send_frequency=0.25,
            block_on_send=False, block_on_response=False,
            transmission_impl=None, sampler_hook=None, presend_hook=None,
            debug=False):

        self.client = None
        self.tracer_impl = None
        self.presend_hook = None
        self.sampler_hook = None

        self.debug = debug
        if debug:
            self._init_logger()

        # allow setting some values from the environment
        if not writekey:
            writekey = os.environ.get('HONEYCOMB_WRITEKEY', '')

        if not dataset:
            dataset = os.environ.get('HONEYCOMB_DATASET', '')

        if not service_name:
            service_name = os.environ.get('HONEYCOMB_SERVICE', dataset)

        self.client = Client(
            writekey=writekey, dataset=dataset, sample_rate=sample_rate,
            api_host=api_host, max_concurrent_batches=max_concurrent_batches,
            max_batch_size=max_batch_size, send_frequency=send_frequency,
            block_on_send=block_on_send, block_on_response=block_on_response,
            transmission_impl=transmission_impl,
            user_agent_addition=USER_AGENT_ADDITION,
            debug=debug,
        )

        self.log('initialized honeycomb client: writekey=%s dataset=%s service_name=%s',
                   writekey, dataset, service_name)
        if not writekey:
            self.log('writekey not set! set the writekey if you want to send data to honeycomb')
        if not dataset:
            self.log('dataset not set! set a value for dataset if you want to send data to honeycomb')

        self.client.add_field('service_name', service_name)
        self.client.add_field('meta.beeline_version', VERSION)
        self.client.add_field('meta.local_hostname', socket.gethostname())

        self.tracer_impl = SynchronousTracer(self.client)
        self.tracer_impl.register_hooks(presend=presend_hook, sampler=sampler_hook)
        self.sampler_hook = sampler_hook
        self.presend_hook = presend_hook

    def send_now(self, data):
        ''' DEPRECATED - to be removed in a future release

        Create an event and enqueue it immediately. Does not work with
        `beeline.add_field` - this is equivalent to calling `libhoney.send_now`
        '''
        ev = self.client.new_event()

        if data:
            ev.add(data)
        self._run_hooks_and_send(ev)

    def add_field(self, name, value):
        ''' Add a field to the currently active span.

        `beeline.add_field("my field", "my value")`

        If a field is being attributed to the wrong span/event,
        make sure that `new_event` and `close_event` calls are matched.
        '''
        # fetch the current event from our tracer
        span = self.tracer_impl.get_active_span()
        # if there are no spans, this is a noop
        if span is None:
            return
        span.add_context_field(name, value)

    def add(self, data):
        '''Similar to add_field(), but allows you to add a number of name:value pairs
        to the currently active event at the same time.

        `beeline.add({ "first_field": "a", "second_field": "b"})`
        '''
        # fetch the current event from the tracer
        span = self.tracer_impl.get_active_span()
        # if there are no spans, this is a noop
        if span is None:
            return

        span.add_context(data)

    def tracer(self, name, trace_id=None, parent_id=None):
        return self.tracer_impl(name=name, trace_id=trace_id, parent_id=parent_id)

    def new_event(self, data=None, trace_name=''):
        ''' DEPRECATED: Helper method that wraps `start_trace` and
        `start_span`. It is better to use these methods as it provides
        better control and context around how traces are implemented in your
        app.

        Creates a new span, populating it with the given data if
        supplied. If no trace is running, a new trace will be started,
        otherwise the event will be added as a span of the existing trace.

        To send the event, call `beeline.send_event()`. There should be a
        `send_event()` for each call to `new_event()`, or tracing and
        `add` and `add_field` will not work correctly.

        If trace_name is specified, will set the "name" field of the current span,
        which is used in the trace visualizer.
        '''
        if trace_name:
            data['name'] = trace_name

        if self.tracer_impl.get_active_trace_id():
            self.tracer_impl.start_span(context=data)
        else:
            self.tracer_impl.start_trace(context=data)

    def send_event(self):
        ''' DEPRECATED: Sends the currently active event (current span),
        if it exists.

        There must be one call to `send_event` for each call to `new_event`.
        '''

        span = self.tracer_impl.get_active_span()
        if span:
            if span.is_root():
                self.tracer_impl.finish_trace(span)
                return
            self.tracer_impl.finish_span(span)

    def send_all(self):
        ''' send all spans in the trace stack, regardless of their
        state
        '''

        span = self.tracer_impl.get_active_span()
        while span:
            if span.is_root():
                self.tracer_impl.finish_trace(span)
                return
            self.tracer_impl.finish_span(span)
            span = self.tracer_impl.get_active_span()

    def traced(self, name, trace_id=None, parent_id=None):
        def wrapped(fn, *args, **kwargs):
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                with self.tracer(name=name, trace_id=trace_id, parent_id=parent_id):
                    return fn(*args, **kwargs)
            return inner

        return wrapped

    def _run_hooks_and_send(self, ev):
        ''' internal - run any defined hooks on the event and send '''
        presampled = False
        if self.sampler_hook:
            self.log("executing sampler hook on event ev = %s", ev.fields())
            keep, new_rate = self.sampler_hook(ev.fields())
            if not keep:
                self.log("skipping event due to sampler hook sampling ev = %s", ev.fields())
                return
            ev.sample_rate = new_rate
            presampled = True

        if self.presend_hook:
            self.log("executing presend hook on event ev = %s", ev.fields())
            self.presend_hook(ev.fields())

        if presampled:
            self.log("enqueuing presampled event ev = %s", ev.fields())
            ev.send_presampled()
        else:
            self.log("enqueuing event ev = %s", ev.fields())
            ev.send()

    def _init_logger(self):
        import logging
        self._logger = logging.getLogger('honeycomb-beeline')
        self._logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    def log(self, msg, *args, **kwargs):
        if self.debug:
            self._logger.debug(msg, *args, **kwargs)

    def get_responses_queue(self):
        return self.client.responses()

    def close(self):
        if self.client:
            self.client.close()

def init(writekey='', dataset='', service_name='', tracer=None,
         sample_rate=1, api_host='https://api.honeycomb.io', transmission_impl=None,
         sampler_hook=None, presend_hook=None, debug=False, *args, **kwargs):
    ''' initialize the honeycomb beeline. This will initialize a libhoney
    client local to this module, and a tracer to track traces and spans.

    Args:
    - `writekey`: the authorization key for your team on Honeycomb. Find your team
            write key at [https://ui.honeycomb.io/account](https://ui.honeycomb.io/account)
    - `dataset`: the name of the default dataset to which to write
    - `sample_rate`: the default sample rate. 1 / `sample_rate` events will be sent.
    - `transmission_impl`: if set, override the default transmission implementation
            (for example, TornadoTransmission)
    - `sampler_hook`: accepts a function to be called just before each event is sent.
            The function should accept a dictionary of event fields, and return a tuple
            of type (bool, int). The first item indicates whether or not the event
            should be sent, and the second indicates the updated sample rate to use.
    - `presend_hook`: accepts a function to be called just before each event is sent.
            The functon should accept a dictionary of event fields, and can be used
            to add new fields, modify/scrub existing fields, or drop fields. This
            function is called after sampler_hook, if sampler_hook is set.

    If in doubt, just set `writekey` and `dataset` and move on!
    '''
    global _GBL
    if _GBL:
        _GBL.log("beeline already initialized! skipping initialization")
        return

    _GBL = Beeline(
        writekey=writekey, dataset=dataset, sample_rate=sample_rate,
        api_host=api_host, transmission_impl=transmission_impl,
        debug=debug, presend_hook=presend_hook, sampler_hook=sampler_hook,
        service_name=service_name,
        # since we've simplified the init function signature a bit,
        # pass on other args for backwards compatibility
        *args, **kwargs
    )

def send_now(data):
    ''' Create an event and enqueue it immediately. Does not work with
    `beeline.add_field` - this is equivalent to calling `libhoney.send_now`

    Args:
    - `data`: dictionary of field names (strings) to field values to include
              in the event
    '''
    # no-op if we're not initialized
    if _GBL:
        _GBL.send_now(data)

def add_field(name, value):
    ''' DEPRECATED: use `add_context_field`

    Args:
    - `data`: dictionary of field names (strings) to field values to add
    '''
    if _GBL:
        _GBL.add_field(name, value)

def add(data):
    '''DEPRECATED: use `add_context`

    Args:
    - `data`: dictionary of field names (strings) to field values to add
    '''
    if _GBL:
        _GBL.add(data)

def add_context(data):
    '''Similar to add_context_field(), but allows you to add a number of name:value pairs
    to the currently active event at the same time.

    `beeline.add_context({ "first_field": "a", "second_field": "b"})`

    Args:
    - `data`: dictionary of field names (strings) to field values to add
    '''
    if _GBL:
        _GBL.tracer_impl.add_context(data=data)

def add_context_field(name, value):
    ''' Add a field to the currently active span. For example, if you are
    using django and wish to add additional context to the current request
    before it is sent to Honeycomb:

    `beeline.add_context_field("my field", "my value")`

    Args:
    - `name`: Name of field to add
    - `value`: Value of new field
    '''
    if _GBL:
        _GBL.tracer_impl.add_context_field(name=name, value=value)

def remove_context_field(name):
    ''' Remove a single field from the current span.

    ```
    beeline.add_context({ "first_field": "a", "second_field": "b"})
    beeline.remove_context_field("second_field")

    Args:
    - `name`: Name of field to remove
    ```
     '''
    if _GBL:
        _GBL.tracer_impl.remove_context_field(name=name)

def add_trace_field(name, value):
    ''' Similar to `add_context_field` - adds a field to the current span, but
    also to all other future spans in this trace. Trace context fields will be
    propagated to downstream services if using instrumented libraries
    like `requests`.

    Args:
    - `name`: Name of field to add
    - `value`: Value of new field
    '''
    if _GBL:
        _GBL.tracer_impl.add_trace_field(name=name, value=value)

def remove_trace_field(name):
    ''' Removes a trace context field from the current span. This will not
    affect  other existing spans, but will prevent the field from being
    propagated to new spans.

    Args:
    - `name`: Name of field to remove
    '''
    if _GBL:
        _GBL.tracer_impl.remove_trace_field(name=name)

def tracer(name, trace_id=None, parent_id=None):
    '''
    When used in a context manager, creates a span for the contained
    code. If a trace is ongoing, will add a new child span under the currently
    running span. If no trace is ongoing, will start a new trace.

    Example use:

    ```
    with tracer(name="my expensive computation"):
        recursive_fib(100)
    ```

    Args:
    - `name`: a descriptive name for the this trace span, i.e. "database query for user"
    - `trace_id`: the trace_id to use. If None, will be automatically generated if no
       current trace is ongoing. Use this if you want to explicitly resume a trace
       in this application that was initiated in another application, and you have
       the upstream trace_id.
    - `parent_id`: If trace_id is set, will populate the root span's parent
        with this id.
    '''
    bl = get_beeline()
    if bl:
        return bl.tracer(name=name, trace_id=trace_id, parent_id=parent_id)

    # if the beeline is not initialized, build a dummy function
    # that will work as a context manager and call that
    @contextmanager
    def _noop_cm():
        yield

    return _noop_cm()

def start_trace(context=None, trace_id=None, parent_span_id=None):
    '''
    Start a trace, returning the root span. To finish the trace, pass the span
    to `finish_trace`. If you are using the beeline middleware plugins, such as for
    django, flask, or AWS lambda, you will want to use `start_span` instead, as
    `start_trace` is called at the start of the request.

    Args:
    - `context`: optional dictionary of event fields to populate the root span with
    - `trace_id`: the trace_id to use. If None, will be automatically generated.
        Use this if you want to explicitly resume trace in this application that was
        initiated in another application, and you have the upstream trace_id.
    - `parent_span_id`: If trace_id is set, will populate the root span's parent
        with this id.
    '''
    if _GBL:
        return _GBL.tracer_impl.start_trace(context=context, trace_id=trace_id, parent_span_id=parent_span_id)

def finish_trace(span):
    ''' Explicitly finish a trace. If you started a trace with `start_trace`, you must call
    this to close the trace and send the root span. If you are using the beeline middleware plugins,
    such as django, flask, or AWS lambda, you can skip this step as the trace will be closed for
    you.

    Args:
    - `span`: Span object that was returned by `start_trace`
    '''
    if _GBL:
        _GBL.tracer_impl.finish_trace(span=span)

def start_span(context=None, parent_id=None):
    '''
    Start a new span and return the span object. Returns None if no trace is active.
    For each `start_span`, there should be one call to `close_span`. Child spans should
    also be closed before parent spans. Closing spans out of order will lead to strange
    results and can break the bookkeeping needed to preserve trace structure. For example:

    ```
    parent_span = beeline.start_span()
    # this span is a child of the last span created
    child_span = beeline.start_span()
    beeline.finish_span(child_span)
    beeline.finish_span(parent_span)
    ```

    Args:
    - `context`: optional dictionary of event fields to populate the span with
    - `parent_id`: ID of parent span - use this only if you have a very good reason to
        do so.
    '''
    if _GBL:
        return _GBL.tracer_impl.start_span(context=context, parent_id=parent_id)

def finish_span(span):
    '''
    Finish the provided span, sending the associated event data to Honeycomb.

    For each `start_span`, there should be one call to `close_span`.

    Args:
    - `span`: Span object that was returned by `start_trace`
    '''
    if _GBL:
        _GBL.tracer_impl.finish_span(span=span)

def marshal_trace_context():
    '''
    Returns a serialized form of the current trace context (including the trace
    id and the current span), encoded as a string. You can use this to propagate
    trace context to other services.

    Example:

    ```
    trace_context = beeline.marshal_trace_context()
    headers = {'X-Honeycomb-Trace': trace_context}
    requests.get("http://...", headers=headers)
    ```
    '''
    if _GBL:
        return _GBL.tracer_impl.marshal_trace_context()


def new_event(data=None, trace_name=''):
    ''' DEPRECATED: Helper method that wraps `start_trace` and
    `start_span`. It is better to use these methods as it provides
    better control and context around how traces are implemented in your
    app.

    Creates a new span, populating it with the given data if
    supplied. If no trace is running, a new trace will be started,
    otherwise the event will be added as a span of the existing trace.

    To send the event, call `beeline.send_event()`. There should be a
    `send_event()` for each call to `new_event()`, or tracing and
    `add` and `add_field` will not work correctly.

    If trace_name is specified, will set the "name" field of the current span,
    which is used in the trace visualizer.
    '''
    if _GBL:
        _GBL.new_event(data=data, trace_name=trace_name)

def send_event():
    ''' DEPRECATED: Sends the currently active event (current span),
    if it exists.

    There must be one call to `send_event` for each call to `new_event`.
    '''
    if _GBL:
        _GBL.send_event()

def send_all():
    ''' send all spans in the trace stack, regardless of their
    state. You might use this in a catch-all error handler
    along with `beeline.close()` to send all events before the program
    terminates abruptly.
    '''
    if _GBL:
        _GBL.send_all()

def get_beeline():
    return _GBL

def get_responses_queue():
    '''
    Returns a queue from which you can read a record of response info from
    each event sent. Responses will be dicts with the following keys:
        - `status_code` - the HTTP response from the api (eg. 200 or 503)
        - `duration` - how long it took to POST this event to the api, in ms
        - `metadata` - pass through the metadata you added on the initial event
        - `body` - the content returned by API (will be empty on success)
        - `error` - in an error condition, this is filled with the error message
    When the Client's `close` method is called, a None will be inserted on
    the queue, indicating that no further responses will be written.
    '''
    if _GBL:
        return _GBL.get_responses_queue()

def close():
    ''' close the beeline and libhoney client, flushing any unsent events. '''
    global _GBL
    if _GBL:
        _GBL.close()

    _GBL = None

def traced(name, trace_id=None, parent_id=None):
    '''
    Function decorator to wrap an entire function in a trace span. If no trace
    is active in the current thread, starts a new trace, and the wrapping span
    will be a root span. If a trace is active, creates a child span of the
    existing trace.

    Example use:

    ```
    @traced(name="my_expensive_function")
    def my_func(n):
        recursive_fib(n)

    my_func(100)
    ```

    Args:
    - `name`: a descriptive name for the this trace span, i.e. "function_name". This is required.
    - `trace_id`: the trace_id to use. If None, will be automatically generated.
        Use this if you want to explicitly resume a trace in this application that was
        initiated in another application, and you have the upstream trace_id.
    - `parent_id`: If trace_id is set, will populate the root span's parent
        with this id.
    '''

    def wrapped(fn, *args, **kwargs):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            with tracer(name=name, trace_id=trace_id, parent_id=parent_id):
                return fn(*args, **kwargs)

        return inner

    return wrapped

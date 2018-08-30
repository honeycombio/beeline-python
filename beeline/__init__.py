''' module beeline '''
import os
import socket

from libhoney import Client
from libhoney.errors import SendError
from beeline.state import ThreadLocalState
from beeline.trace import SynchronousTracer
from beeline.version import VERSION

USER_AGENT_ADDITION = "beeline-python/%s" % VERSION

g_client = None
g_state = None
g_tracer = None
g_sampler_hook = None
g_presend_hook = None

def init(writekey='', dataset='', service_name='', state_manager=None, tracer=None,
         sample_rate=1, api_host='https://api.honeycomb.io', max_concurrent_batches=10,
         max_batch_size=100, send_frequency=0.25,
         block_on_send=False, block_on_response=False, transmission_impl=None,
         sampler_hook=None, presend_hook=None):
    ''' initialize the honeycomb beeline. This will initialize a libhoney
    client local to this module, and a state manager for tracking event context.

    Args:
    - `writekey`: the authorization key for your team on Honeycomb. Find your team
            write key at [https://ui.honeycomb.io/account](https://ui.honeycomb.io/account)
    - `dataset`: the name of the default dataset to which to write
    - `sample_rate`: the default sample rate. 1 / `sample_rate` events will be sent.
    - `max_concurrent_batches`: the maximum number of concurrent threads sending events.
    - `max_batch_size`: the maximum number of events to batch before sendinga.
    - `send_frequency`: how long to wait before sending a batch of events, in seconds.
    - `block_on_send`: if true, block when send queue fills. If false, drop
            events until there's room in the queue
    - `block_on_response`: if true, block when the response queue fills. If
            false, drop response objects.
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
    global g_client, g_state, g_tracer, g_presend_hook, g_sampler_hook
    if g_client:
        return

    # allow setting some values from the environment
    if not writekey:
        writekey = os.environ.get('HONEYCOMB_WRITEKEY', '')

    if not dataset:
        dataset = os.environ.get('HONEYCOMB_DATASET', '')

    if not service_name:
        service_name = os.environ.get('HONEYCOMB_SERVICE', dataset)

    g_client = Client(
        writekey=writekey, dataset=dataset, sample_rate=sample_rate,
        api_host=api_host, max_concurrent_batches=max_concurrent_batches,
        max_batch_size=max_batch_size, send_frequency=send_frequency,
        block_on_send=block_on_send, block_on_response=block_on_response,
        transmission_impl=transmission_impl,
        user_agent_addition=USER_AGENT_ADDITION,
    )

    g_client.add_field('service_name', service_name)
    g_client.add_field('meta.beeline_version', VERSION)
    g_client.add_field('meta.local_hostname', socket.gethostname())

    if state_manager:
        g_state = state_manager
    else:
        g_state = ThreadLocalState()

    g_tracer = SynchronousTracer(g_client, g_state)
    g_sampler_hook = sampler_hook
    g_presend_hook = presend_hook


def send_now(data):
    ''' Create an event and enqueue it immediately. Does not work with
    `beeline.add_field` - this is equivalent to calling `libhoney.send_now`
    '''
    # no-op if we're not initialized
    if not g_client:
        return
    ev = g_client.new_event()

    if data:
        ev.add(data)
    _run_hooks_and_send(ev)


def add_field(name, value):
    ''' Add a field to the currently active event. For example, if you are
    using django and wish to add additional context to the current request
    before it is sent to Honeycomb:

    `beeline.add_field("my field", "my value")`

    The "active event" is determined by the state manager. If a field is being
    attributed to the wrong event, make sure that `_new_event` and `_close_event`
    calls are matched.
    '''
    if not g_state:
        return
    # fetch the current event from our state provider
    ev = g_state.get_current_event()
    # if no event is in state, we're a noop
    if ev is None:
        return

    ev.add_field(name, value)


def add(data):
    '''Similar to add_field(), but allows you to add a number of name:value pairs
    to the currently active event at the same time.

    `beeline.add({ "first_field": "a", "second_field": "b"})`
    '''
    if not g_state:
        return
    # fetch the current event from our state provider
    ev = g_state.get_current_event()
    # if no event is in state, we're a noop
    if ev is None:
        return

    ev.add(data)


def tracer(name):
    '''
    When used in a context manager, creates a trace event for the contained
    code. If existing trace context data is available, will mark the event as a
    child of the most recent trace span.

    Example use:

    ```
    with tracer(name="my expensive computation"):
        recursive_fib(100)
    ```

    Args:
    - `name`: a descriptive name for the this trace span, i.e. "database query for user"
    '''
    return g_tracer(name=name)


def _new_event(data=None, trace_name='', top_level=False):
    ''' internal - create a new event, populating it with the given data if
    supplied. The event is added to the given State manager. To send the
    event, call _send_event(). There should be a _send_event() for each
    call to _new_event(), or tracing and `add` and `add_field` will not
    work correctly.

    If `trace_name` is set, generate trace metadata and measure the time
    between when the event is created and when the event is sent as
    `duration_ms`.

    If top_level is True, resets any previous event state. Set this in
    top-level events (example: start of a request) to ensure that state
    and trace data are cleaned up from a previous execution.
    '''
    if not g_client or not g_state:
        return

    if top_level:
        g_state.reset()

    if trace_name:
        ev = g_tracer.new_traced_event(trace_name)
    else:
        ev = g_client.new_event()

    if data:
        ev.add(data)

    g_state.add_event(ev)


def _send_event():
    ''' internal - send the current event in the state manager, if one exists.
    '''
    if not g_client or not g_state:
        return

    ev = g_state.pop_event()

    if ev is None:
        return

    _run_hooks_and_send(ev)

def _send_all():
    ''' internal - send all events in the event stack, regardless of their
    state
    '''
    if not g_client or not g_state:
        return

    ev = g_state.pop_event()
    while ev:
        try:
            _run_hooks_and_send(ev)
        except SendError:
            # disregard any errors due to uninitialized events
            pass

        ev = g_state.pop_event()

def _run_hooks_and_send(ev):
    ''' internal - run any defined hooks on the event and send '''
    presampled = False
    if g_sampler_hook:
        keep, new_rate = g_sampler_hook(ev.fields())
        if not keep:
            return
        ev.sample_rate = new_rate
        presampled = True
    
    if g_presend_hook:
        g_presend_hook(ev.fields())
    
    if hasattr(ev, 'traced_event'):
        g_tracer.send_traced_event(ev, presampled=presampled)
    elif presampled:
        ev.send_presampled()
    else:
        ev.send()

def close():
    ''' close the beeline client, flushing any unsent events. '''
    global g_client
    if g_client:
        g_client.close()

    g_client = None

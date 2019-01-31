import base64
import datetime
import hashlib
import json
import math
import struct
import threading
import uuid
from functools import wraps

from contextlib import contextmanager

from beeline.internal import log, stringify_exception

MAX_INT32 = math.pow(2, 32) - 1

def init_state(f):
    ''' Ensure thread local state is initialized in each thread '''
    @wraps(f)
    def d(self, *args, **kwargs):
        if not hasattr(self._state, 'trace_id'):
            self._state.trace_id = None
            self._state.stack = []
            self._state.trace_fields = {}

        return f(self, *args, **kwargs)
    return d

class Tracer(object):
    pass

class SynchronousTracer(Tracer):
    def __init__(self, client):
        self._client = client
        self._state = threading.local()

        self.presend_hook = None
        self.sampler_hook = None

    @contextmanager
    def __call__(self, name, trace_id=None, parent_id=None):
        try:
            span = None
            if self.get_active_trace_id() and trace_id is None:
                span = self.start_span(context={'name': name}, parent_id=parent_id)
                if span:
                    log('tracer context manager started new span, id = %s',
                        span.id)
            else:
                span = self.start_trace(context={'name': name}, trace_id=trace_id, parent_span_id=parent_id)
                if span:
                    log('tracer context manager started new trace, id = %s',
                        span.trace_id)
            yield span
        except Exception as e:
            if span:
                span.add_context({
                    "app.exception_type": str(type(e)),
                    "app.exception_string": stringify_exception(e),
                })
            raise
        finally:
            if span:
                if span.is_root():
                    log('tracer context manager ending trace, id = %s',
                        span.trace_id)
                    self.finish_trace(span)
                else:
                    log('tracer context manager ending span, id = %s',
                        span.id)
                    self.finish_span(span)
            else:
                log('tracer context manager span for %s was unexpectedly None', name)

    @init_state
    def start_trace(self, context=None, trace_id=None, parent_span_id=None):
        if trace_id:
            if self._state.trace_id:
                log('warning: start_trace got explicit trace_id but we are already in a trace. '
                    'starting new trace with id = %s', trace_id)
            self._state.trace_id = trace_id
        else:
            self._state.trace_id = str(uuid.uuid4())

        # reset our stack and context on new traces
        self._state.stack = []
        self._state.trace_fields = {}

        # start the root span
        return self.start_span(context=context, parent_id=parent_span_id)

    @init_state
    def start_span(self, context=None, parent_id=None):
        if not self._state.trace_id:
            log('start_span called but no trace is active')
            return None

        span_id = str(uuid.uuid4())
        if parent_id:
            parent_span_id = parent_id
        else:
            parent_span_id = self._state.stack[-1].id if self._state.stack else None
        ev = self._client.new_event(data=self._state.trace_fields)
        if context:
            ev.add(data=context)

        ev.add(data={
            'trace.trace_id': self._state.trace_id,
            'trace.parent_id': parent_span_id,
            'trace.span_id': span_id,
        })
        is_root = len(self._state.stack) == 0
        span = Span(trace_id=self._state.trace_id, parent_id=parent_span_id,
                    id=span_id, event=ev, is_root=is_root)
        self._state.stack.append(span)

        return span

    @init_state
    def finish_span(self, span):
        # send the span's event. Even if the stack is in an unhealthy state,
        # it's probably better to send event data than not
        if span.event:
            # propagate trace fields that may have been added in later spans
            for k, v in self._state.trace_fields.items():
                # don't overwrite existing values because they may be different
                if k not in span.event.fields():
                    span.event.add_field(k, v)

            duration = datetime.datetime.now() - span.event.start_time
            duration_ms = duration.total_seconds() * 1000.0
            span.event.add_field('duration_ms', duration_ms)

            self._run_hooks_and_send(span)
        else:
            log('warning: span has no event, was it initialized correctly?')

        if span.trace_id != self._state.trace_id:
            log('warning: finished span called for span in inactive trace. '
                'current trace_id = %s, span trace_id = %s', self._state.trace_id, span.trace_id)
            return

        if not self._state.stack:
            log('warning: finish span called but stack is empty')
            return

        if self._state.stack[-1].id != span.id:
            log('warning: finished span is not the currently active span')
            return

        self._state.stack.pop()

    @init_state
    def finish_trace(self, span):
        self.finish_span(span)
        self._state.trace_id = None

    @init_state
    def get_active_trace_id(self):
        return self._state.trace_id

    @init_state
    def get_active_span(self):
        if self._state.stack:
            return self._state.stack[-1]

    def add_context_field(self, name, value):
        span = self.get_active_span()
        if span:
            span.add_context_field(name=name, value=value)

    def add_context(self, data):
        span = self.get_active_span()
        if span:
            span.add_context(data=data)

    def remove_context_field(self, name):
        span = self.get_active_span()
        if span:
            span.remove_context_field(name=name)

    @init_state
    def add_trace_field(self, name, value):
        # prefix with app to avoid key conflicts
        key = "app.%s" % name
        self._state.trace_fields[key] = value
        # also add to current span
        self.add_context_field(key, value)

    @init_state
    def remove_trace_field(self, name):
        key = "app.%s" % name
        if key in self._state.trace_fields:
            del self._state.trace_fields[key]
        self.remove_context_field(key)

    @init_state
    def marshal_trace_context(self):
        if not self._state.trace_id:
            log('warning: marshal_trace_context called, but no active trace')
            return

        return marshal_trace_context(
            self._state.trace_id,
            self._state.stack[-1].id,
            self._state.trace_fields
        )

    def register_hooks(self, presend=None, sampler=None):
        self.presend_hook = presend
        self.sampler_hook = sampler

    def _run_hooks_and_send(self, span):
        ''' internal - run any defined hooks on the event and send

        kind of hacky: we fetch the hooks from the beeline, but they are only
        used here. Pass them to the tracer implementation?
        '''
        presampled = False
        if self.sampler_hook:
            log("executing sampler hook on event ev = %s", span.event.fields())
            keep, new_rate = self.sampler_hook(span.event.fields())
            if not keep:
                log("skipping event due to sampler hook sampling ev = %s", span.event.fields())
                return
            span.event.sample_rate = new_rate
            presampled = True

        if self.presend_hook:
            log("executing presend hook on event ev = %s", span.event.fields())
            self.presend_hook(span.event.fields())

        if presampled:
            log("enqueuing presampled event ev = %s", span.event.fields())
            span.event.send_presampled()
        elif _should_sample(span.trace_id, span.event.sample_rate):
            # if our sampler hook wasn't used, use deterministic sampling
            span.event.send_presampled()

class Span(object):
    ''' Span represents an active span. Should not be initialized directly, but
    through a Tracer object's `start_span` method. '''
    def __init__(self, trace_id, parent_id, id, event, is_root=False):
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.id = id
        self.event = event
        self.event.start_time = datetime.datetime.now()
        self._is_root = is_root

    def add_context_field(self, name, value):
        self.event.add_field(name, value)

    def add_context(self, data):
        self.event.add(data)

    def remove_context_field(self, name):
        if name in self.event.fields():
            del self.event.fields()[name]

    def is_root(self):
        return self._is_root

def _should_sample(trace_id, sample_rate):
    sample_upper_bound = MAX_INT32 / sample_rate
    # compute a sha1
    sha1 = hashlib.sha1()
    sha1.update(trace_id.encode('utf-8'))
    # convert last 4 digits to int
    value, = struct.unpack('<I', sha1.digest()[-4:])
    if value < sample_upper_bound:
        return True
    return False

def marshal_trace_context(trace_id, parent_id, context):
    version = 1
    trace_fields = base64.b64encode(json.dumps(context).encode()).decode()
    trace_context = "{};trace_id={},parent_id={},context={}".format(
        version, trace_id, parent_id, trace_fields
    )

    return trace_context

def unmarshal_trace_context(trace_context):
    # the first value is the trace payload version
    # at this time there is only one version, but we should warn
    # if another version comes through
    version, data = trace_context.split(';', 1)
    if version != "1":
        log('warning: trace_context version %s is unsupported', version)
        return None, None, None

    kv_pairs = data.split(',')

    trace_id, parent_id, context = None, None, None
    # For version 1, we expect three kv pairs. If there's anything else, the
    # payload is malformed and we do nothing.
    if len(kv_pairs) == 3:
        for pair in kv_pairs:
            k, v = pair.split('=', 1)
            if k == 'trace_id':
                trace_id = v
            elif k == 'parent_id':
                parent_id = v
            elif k == 'context':
                context = json.loads(base64.b64decode(v.encode()).decode())

    return trace_id, parent_id, context

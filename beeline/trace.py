import base64
import copy
import datetime
import functools
import hashlib
import json
import math
import random
import struct
import sys
import threading
import inspect
from collections import defaultdict

from contextlib import contextmanager

from beeline.internal import log, stringify_exception

import beeline.propagation
import beeline.propagation.honeycomb

MAX_INT32 = math.pow(2, 32) - 1
SPAN_ID_BYTES = 8
TRACE_ID_BYTES = 16


class Trace(object):
    '''Object encapsulating all state of an ongoing trace.'''

    def __init__(self, trace_id, dataset=None):
        self.id = trace_id
        self.dataset = dataset
        self.stack = []
        self.fields = {}
        self.rollup_fields = defaultdict(float)

    def copy(self):
        '''Copy the trace state for use in another thread or context.'''
        result = Trace(self.id)
        result.stack = copy.copy(self.stack)
        result.fields = copy.copy(self.fields)
        return result


class Tracer(object):
    def __init__(self, client):
        self._client = client

        self.presend_hook = None
        self.sampler_hook = None
        self.http_trace_parser_hook = beeline.propagation.honeycomb.http_trace_parser_hook
        self.http_trace_propagation_hook = beeline.propagation.honeycomb.http_trace_propagation_hook

    @contextmanager
    def __call__(self, name, trace_id=None, parent_id=None):
        try:
            span = None
            if self.get_active_trace_id() and trace_id is None:
                span = self.start_span(
                    context={'name': name}, parent_id=parent_id)
                if span:
                    log('tracer context manager started new span, id = %s',
                        span.id)
            else:
                span = self.start_trace(
                    context={'name': name}, trace_id=trace_id, parent_span_id=parent_id)
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

    def start_trace(self, context=None, trace_id=None, parent_span_id=None, dataset=None):
        if trace_id:
            if self._trace:
                log('warning: start_trace got explicit trace_id but we are already in a trace. '
                    'starting new trace with id = %s', trace_id)
            self._trace = Trace(trace_id, dataset)
        else:
            self._trace = Trace(generate_trace_id(), dataset)

        # start the root span
        return self.start_span(context=context, parent_id=parent_span_id)

    def start_span(self, context=None, parent_id=None):
        if not self._trace:
            log('start_span called but no trace is active')
            return None

        span_id = generate_span_id()
        if parent_id:
            parent_span_id = parent_id
        else:
            parent_span_id = self._trace.stack[-1].id if self._trace.stack else None
        ev = self._client.new_event(data=self._trace.fields)
        if context:
            ev.add(data=context)

        ev.add(data={
            'trace.trace_id': self._trace.id,
            'trace.parent_id': parent_span_id,
            'trace.span_id': span_id,
        })
        is_root = len(self._trace.stack) == 0
        span = Span(trace_id=self._trace.id, parent_id=parent_span_id,
                    id=span_id, event=ev, is_root=is_root)
        self._trace.stack.append(span)

        return span

    def finish_span(self, span):
        # avoid exception if called with None
        if span is None:
            return

        # send the span's event. Even if the stack is in an unhealthy state,
        # it's probably better to send event data than not
        if span.event:
            if self._trace:
                if self._trace.dataset:
                    span.event.dataset = self._trace.dataset

                # add the trace's rollup fields to the root span
                if span.is_root():
                    for k, v in self._trace.rollup_fields.items():
                        span.event.add_field(k, v)

                for k, v in span.rollup_fields.items():
                    span.event.add_field(k, v)

                # propagate trace fields that may have been added in later spans
                for k, v in self._trace.fields.items():
                    # don't overwrite existing values because they may be different
                    if k not in span.event.fields():
                        span.event.add_field(k, v)

            duration = datetime.datetime.now() - span.event.start_time
            duration_ms = duration.total_seconds() * 1000.0
            span.event.add_field('duration_ms', duration_ms)

            self._run_hooks_and_send(span)
        else:
            log('warning: span has no event, was it initialized correctly?')

        if not self._trace:
            log('warning: span finished without an active trace')
            return

        if span.trace_id != self._trace.id:
            log('warning: finished span called for span in inactive trace. '
                'current trace_id = %s, span trace_id = %s', self._trace.id, span.trace_id)
            return

        if not self._trace.stack:
            log('warning: finish span called but stack is empty')
            return

        if self._trace.stack[-1].id != span.id:
            log('warning: finished span is not the currently active span')
            return

        self._trace.stack.pop()

    def finish_trace(self, span):
        self.finish_span(span)
        self._trace = None

    def parse_http_trace(self, request):
        if not self.http_trace_parser_hook:
            return None
        return self.http_trace_parser_hook(request)

    def propagate_and_start_trace(self, context, request):
        err = None
        propagation_context = None
        try:
            propagation_context = self.parse_http_trace(request)
        except Exception:
            err = sys.exc_info()[0]
            log('error: http_trace_parser_hook returned exception: %s',
                sys.exc_info()[0])

        if propagation_context:
            return self.start_trace(context=context, trace_id=propagation_context.trace_id,
                                    parent_span_id=propagation_context.parent_id,
                                    dataset=propagation_context.dataset)
            for k, v in propagation_context.trace_fields:
                self.add_trace_field(k, v)
        else:
            # Initialize a new trace from scratch
            if err is not None:
                context['parser_hook_error'] = repr(err)
            return self.start_trace(context, trace_id=None, parent_span_id=None)
        pass

    def get_propagation_context(self):
        if not self._trace:
            return None

        return beeline.propagation.PropagationContext(
            self.get_active_trace_id(),
            self.get_active_span().id,
            self._trace.fields)

    def get_active_trace_id(self):
        if self._trace:
            return self._trace.id
        return None

    def get_active_span(self):
        if self._trace and self._trace.stack:
            return self._trace.stack[-1]
        return None

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

    def add_rollup_field(self, name, value):
        value = float(value)

        span = self.get_active_span()
        if span:
            span.rollup_fields[name] += value

        if not self._trace:
            log('warning: adding rollup field without an active trace')
            return

        self._trace.rollup_fields["rollup.%s" % name] += value

    def add_trace_field(self, name, value):
        # prefix with app to avoid key conflicts
        # add the app prefix if it's missing

        if (type(name) == str and not name.startswith("app.")) or type(name) != str:
            key = "app.%s" % name
        else:
            key = name

        # also add to current span
        self.add_context_field(key, value)

        if not self._trace:
            log('warning: adding trace field without an active trace')
            return
        self._trace.fields[key] = value

    def remove_trace_field(self, name):
        key = "app.%s" % name
        self.remove_context_field(key)
        if not self._trace:
            log('warning: removing trace field without an active trace')
            return
        self._trace.fields.pop(key)

    def marshal_trace_context(self):
        if not self._trace:
            log('warning: marshal_trace_context called, but no active trace')
            return

        return marshal_trace_context(
            self._trace.id,
            self._trace.stack[-1].id,
            self._trace.fields
        )

    def register_hooks(self, presend=None, sampler=None, http_trace_parser=None, http_trace_propagation=None):
        self.presend_hook = presend
        self.sampler_hook = sampler
        self.http_trace_parser_hook = http_trace_parser
        self.http_trace_propagation_hook = http_trace_propagation

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
                log("skipping event due to sampler hook sampling ev = %s",
                    span.event.fields())
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


class SynchronousTracer(Tracer):
    def __init__(self, client):
        super(SynchronousTracer, self).__init__(client)
        self._state = threading.local()

    @property
    def _trace(self):
        return getattr(self._state, 'trace', None)

    @_trace.setter
    def _trace(self, new_trace):
        self._state.trace = new_trace


class Span(object):
    ''' Span represents an active span. Should not be initialized directly, but
    through a Tracer object's `start_span` method. '''

    def __init__(self, trace_id, parent_id, id, event, is_root=False):
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.id = id
        self.event = event
        self.event.start_time = datetime.datetime.now()
        self.rollup_fields = defaultdict(float)
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
    # convert first 4 digits to int
    value, = struct.unpack('>I', sha1.digest()[:4])
    if value < sample_upper_bound:
        return True
    return False


def marshal_trace_context(trace_id, parent_id, context):
    """Deprecated: Use beeline.propagation.honeycomb.marshal_trace_context instead"""
    version = 1
    trace_fields = base64.b64encode(json.dumps(context).encode()).decode()
    trace_context = "{};trace_id={},parent_id={},context={}".format(
        version, trace_id, parent_id, trace_fields
    )

    return trace_context


def unmarshal_trace_context(trace_header):
    """
    Deprecated: Use beeline.propagation.honeycomb.unmarshal_trace_context instead
    """
    return beeline.propagation.honeycomb.unmarshal_propagation_context(trace_header)


def traced_impl(tracer_fn, name, trace_id, parent_id):
    """Implementation of the traced decorator without async support."""
    def wrapped(fn):
        if inspect.isgeneratorfunction(fn):
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                inner_generator = fn(*args, **kwargs)
                with tracer_fn(name=name, trace_id=trace_id, parent_id=parent_id):
                    for value in inner_generator:
                        yield value
            return inner
        else:
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                with tracer_fn(name=name, trace_id=trace_id, parent_id=parent_id):
                    return fn(*args, **kwargs)
            return inner
    return wrapped


# Use system random instead of default psuedorandom generator
system_random = random.SystemRandom()


def generate_span_id():
    """Generate span ID compatible with w3c tracing spec."""
    format_str = "{{:0{:d}x}}".format(SPAN_ID_BYTES*2)
    return format_str.format(system_random.getrandbits(SPAN_ID_BYTES*8))


def generate_trace_id():
    """Generate trace ID compatible with w3c tracing spec."""
    format_str = "{{:0{:d}x}}".format(TRACE_ID_BYTES*2)
    return format_str.format(system_random.getrandbits(TRACE_ID_BYTES*8))

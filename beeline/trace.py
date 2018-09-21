import datetime
import hashlib
import math
import struct

from contextlib import contextmanager

from beeline.internal import log

MAX_INT32 = math.pow(2, 32) - 1


class Tracer(object):
    pass


class SynchronousTracer(Tracer):
    def __init__(self, client, state):
        self._client = client
        self._state = state

    @contextmanager
    def __call__(self, name, trace_id=None, parent_id=None):
        try:
            ev = self.new_traced_event(name, trace_id, parent_id)
            self._state.add_event(ev)
            yield
        finally:
            ev = self._state.pop_event()
            log("enqueuing traced event ev = %s", ev.fields())
            self.send_traced_event(ev)

    def new_traced_event(self, name, trace_id=None, parent_id=None):
        '''
        Create an event decorated with trace IDs. Initiates a new trace if none
        is in progress, or appends the event to the trace stack.

        You must call `send_traced_event` to clean up the trace stack, or
        the trace will not work correctly
        '''
        ev = self._client.new_event()
        trace_id, parent_id, span_id = self._state.start_trace(
            trace_id, parent_id)
        ev.add({
            'trace.trace_id': trace_id,
            'trace.parent_id': parent_id,
            'trace.span_id': span_id,
            'name': name,
        })
        log("started new traced event ev = %s", ev.fields())
        ev.start_time = datetime.datetime.now()
        ev.traced_event = True
        return ev

    def send_traced_event(self, ev, presampled=False):
        ''' Applies deterministic sampling to the event before sending. This allows
        us to sample entire traces '''
        # we shouldn't get called for non-trace events, so do nothing.
        if not hasattr(ev, 'traced_event'):
            return

        duration = datetime.datetime.now() - ev.start_time
        duration_ms = duration.total_seconds() * 1000.0
        ev.add_field('duration_ms', duration_ms)

        trace_id = ev.fields().get('trace.trace_id')

        if presampled:
            ev.send_presampled()
        elif trace_id and _should_sample(trace_id, ev.sample_rate):
            ev.send_presampled()
        else:
            ev.send()

        self._state.end_trace()


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

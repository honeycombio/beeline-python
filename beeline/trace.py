import datetime
from contextlib import contextmanager

class Tracer(object):
    pass

class SynchronousTracer(Tracer):
    def __init__(self, client, state):
        self._client = client
        self._state = state

    @contextmanager
    def __call__(self, name):
        ev = self._client.new_event()
        trace_id, parent_id, span_id = self._state.start_trace()
        ev.add({
            'trace.trace_id': trace_id,
            'trace.parent_id': parent_id,
            'trace.span_id': span_id,
            'name': name,
        })
        self._state.add_event(ev)
        time_start = datetime.datetime.now()
        yield
        duration = datetime.datetime.now() - time_start
        duration_ms = duration.total_seconds() * 1000.0
        ev = self._state.pop_event()
        if ev:
            ev.add_field('duration_ms', duration_ms)
            ev.send()
        self._state.end_trace()
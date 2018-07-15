import threading
import uuid

class State(object):
    def get_current_event(self):
        raise NotImplementedError

    def add_event(self, ev):
        raise NotImplementedError

    def pop_event(self):
        raise NotImplementedError

class ThreadLocalState(State):
    ''' Simple state manager that uses threadlocals to store state for pending
    Honeycomb events. Uses a stack to track nested events within the same
    thread. This will not work in asynchronous runtimes like asyncio or tornado.
    '''
    def __init__(self):
        self._state = threading.local()

    def reset(self):
        self._state.trace_stack = []
        self._state.event_stack = []

    def _trace_stack(self):
        if not hasattr(self._state, 'trace_stack'):
            self._state.trace_stack = []
        return self._state.trace_stack

    def _event_stack(self):
        # if we enter a new thread, we won't have an existing event stack
        if not hasattr(self._state, 'event_stack'):
            self._state.event_stack = []
        return self._state.event_stack

    def _trace_id(self):
        if not hasattr(self._state, 'trace_id'):
            self._state.trace_id = ''
        return self._state.trace_id

    def start_trace(self, trace_id=None, parent_id=None):
        if trace_id:
            self._state.trace_id = trace_id
        if not self._trace_id():
            self._state.trace_id = str(uuid.uuid4())
        trace_stack = self._trace_stack()
        if not parent_id:
            parent_id = trace_stack[-1] if trace_stack else None
        span_id = str(uuid.uuid4())
        self._trace_stack().append(span_id)

        return self._trace_id(), parent_id, span_id

    def end_trace(self):
        if self._trace_stack():
            self._trace_stack().pop()
        # if we cleared out the trace stack, this trace is over
        if not self._trace_stack():
            self._state.trace_id = None

    def get_current_event(self):
        stack = self._event_stack()
        return stack[-1] if stack else None

    def add_event(self, ev):
        self._event_stack().append(ev)
        
    def pop_event(self):
        event_stack = self._event_stack()
        if event_stack:
            return event_stack.pop()
        return None

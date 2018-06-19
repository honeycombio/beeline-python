import threading

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
    thread. This will not work in asynchronous runtimes like asyncio or tornado
    '''
    def __init__(self):
        self._state = threading.local()

    def _event_stack(self):
        # if we enter a new thread, we won't have an existing event stack
        if not hasattr(self._state, 'event_stack'):
            self._state.event_stack = []
        return self._state.event_stack

    def get_current_event(self):
        stack = self._event_stack()
        return stack[-1] if stack else None

    def add_event(self, ev):
        self._event_stack().append(ev)

    def pop_event(self):
        stack = self._event_stack()
        if stack:
            return stack.pop()
        return None

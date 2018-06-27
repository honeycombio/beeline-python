import threading
import unittest
from mock import Mock, patch
from beeline.state import ThreadLocalState

class TestThreadLocalState(unittest.TestCase):
    def test_thread_local(self):
        ''' ensure that state is separate kept separate between threads '''
        state = ThreadLocalState()
        e1, e2 = Mock(), Mock()
        def f1():
            state.add_event(e1)
            # verify that the event made it into the threadlocal state
            self.assertEqual(state.get_current_event(), e1)
        def f2():
            state.add_event(e2)
            self.assertEqual(state.get_current_event(), e2)

        t1, t2 = threading.Thread(target=f1), threading.Thread(target=f2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # parent thread should see no events, because events were added in
        # another thread
        self.assertEqual(state.get_current_event(), None)

    def test_trace_state(self):
        ''' ensure correct behavior of trace tracking '''
        state = ThreadLocalState()
        with patch('beeline.state.uuid.uuid4') as m_uuid:
            m_uuid.side_effect = ["1", "2", "3", "4", "5", "6"]

            # first request generates a trace id and span id
            # parent id is None since this is the start
            trace_id, parent_id, span_id = state.start_trace()
            self.assertEqual(trace_id, "1")
            self.assertEqual(parent_id, None)
            self.assertEqual(span_id, "2")

            # start a second trace - this will be a child of the first
            # trace
            trace_id, parent_id, span_id = state.start_trace()
            self.assertEqual(trace_id, "1")
            self.assertEqual(parent_id, "2")
            self.assertEqual(span_id, "3")

            # start a third trace, will be a child of the second trace
            trace_id, parent_id, span_id = state.start_trace()
            self.assertEqual(trace_id, "1")
            self.assertEqual(parent_id, "3")
            self.assertEqual(span_id, "4")

            # stop the last trace
            state.end_trace()

            # start a fourth trace, which will be a child of the second trace
            trace_id, parent_id, span_id = state.start_trace()
            self.assertEqual(trace_id, "1")
            self.assertEqual(parent_id, "3")
            self.assertEqual(span_id, "5")

    def test_event_state(self):
        ''' ensure correct stack-like behavior of event state '''
        e1, e2, e3, e4 = Mock(), Mock(), Mock(), Mock()
        state = ThreadLocalState()

        state.add_event(e1)
        self.assertEqual(state.get_current_event(), e1)
        state.add_event(e2)
        self.assertEqual(state.get_current_event(), e2)
        state.add_event(e3)
        self.assertEqual(state.get_current_event(), e3)
        # pop_event always returns the last event
        e = state.pop_event()
        self.assertEqual(e, e3)
        state.add_event(e4)
        self.assertEqual(state.get_current_event(), e4)
        e = state.pop_event()
        self.assertEqual(e, e4)
        e = state.pop_event()
        self.assertEqual(e, e2)
        e = state.pop_event()
        self.assertEqual(e, e1)

    def test_event_state_reset(self):
        e1 = Mock()
        state = ThreadLocalState()

        state.add_event(e1)
        self.assertEqual(state.get_current_event(), e1)
        state.reset()
        self.assertEqual(state.get_current_event(), None)

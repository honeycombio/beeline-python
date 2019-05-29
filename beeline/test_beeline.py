import threading
import unittest
from mock import Mock, patch, call

import beeline
import libhoney
assert libhoney

class TestBeeline(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline._GBL').start()

    def test_send_event(self):
        ''' test correct behavior for send_event '''
        _beeline = beeline.Beeline()
        _beeline.tracer_impl = Mock()
        m_span = Mock()
        _beeline.tracer_impl.get_active_span.return_value = m_span
        _beeline.send_event()
        _beeline.tracer_impl.get_active_span.assert_called_once_with()
        _beeline.tracer_impl.finish_trace.assert_called_once_with(m_span)

    def test_send_no_events(self):
        ''' ensure nothing crashes when we try to send with no events in the
        stack '''
        _beeline = beeline.Beeline()
        _beeline.tracer_impl = Mock()
        _beeline.tracer_impl.get_active_span.return_value = None
        _beeline.send_event()
        _beeline.tracer_impl.get_active_span.assert_called_once_with()

    def test_send_all(self):
        ''' ensure events are flushed, and that the root span is handled with
        finish_trace '''
        s1, s2, s3 = Mock(), Mock(), Mock()
        s1.is_root.return_value = False
        s2.is_root.return_value = False
        s3.is_root.return_value = True
        _beeline = beeline.Beeline()
        _beeline.tracer_impl = Mock()
        _beeline.tracer_impl.get_active_span.side_effect = [s1, s2, s3, None]

        _beeline.send_all()

        _beeline.tracer_impl.finish_span.assert_has_calls([
            call(s1),
            call(s2),
        ])
        _beeline.tracer_impl.finish_trace.assert_called_once_with(s3)

    def test_run_hooks_and_send_no_hooks(self):
        ''' ensure send works when no hooks defined '''
        ev = Mock()
        _beeline = beeline.Beeline()
        _beeline.tracer_impl = Mock()
        _beeline._run_hooks_and_send(ev)

        # no hooks, not a traced event - call send
        ev.send.assert_called_once_with()
        ev.send_presampled.assert_not_called()

    def test_run_hooks_and_send_sampler(self):
        ''' ensure send works with a sampler hook defined '''
        def _sampler_drop_all(fields):
            return False, 0
        m_sampler_hook = Mock()
        m_sampler_hook.side_effect = _sampler_drop_all
        _beeline = beeline.Beeline(sampler_hook=m_sampler_hook)
        _beeline.tracer_impl = Mock()
        ev = Mock()

        _beeline._run_hooks_and_send(ev)
        m_sampler_hook.assert_called_once_with(ev.fields())
        ev.send_presampled.assert_not_called()
        ev.send.assert_not_called()

        def _sampler_drop_none(fields):
            return True, 100

        ev = Mock()
        m_sampler_hook.reset_mock()

        m_sampler_hook.side_effect = _sampler_drop_none

        _beeline._run_hooks_and_send(ev)
        m_sampler_hook.assert_called_once_with(ev.fields())
        self.assertEqual(ev.sample_rate, 100)
        ev.send_presampled.assert_called_once_with()
        ev.send.assert_not_called()

    def test_run_hooks_and_send_presend_hook(self):
        ''' ensure send works when presend hook is defined '''
        def _presend_hook(fields):
            fields["thing i want"] = "put it there"
            del fields["thing i don't want"]
        m_presend_hook = Mock()
        m_presend_hook.side_effect = _presend_hook
        _beeline = beeline.Beeline(presend_hook=m_presend_hook)
        _beeline.tracer_impl = Mock()

        ev = Mock()
        ev.fields.return_value = {
            "thing i don't want": "get it out of here",
            "happy data": "so happy",
        }

        _beeline._run_hooks_and_send(ev)
        ev.send_presampled.assert_not_called()
        ev.send.assert_called_once_with()
        self.assertDictEqual(
            ev.fields(),
            {
                "thing i want": "put it there",
                "happy data": "so happy",
            },
        )

    def test_start_trace_returns_value(self):
        ''' ensure the top-level start_span and start_trace APIs return the value
        form their calls to the tracer '''
        self.m_gbl.tracer_impl.start_span.return_value = 'wooimaspan'
        val = beeline.start_span()
        self.assertEqual(val, 'wooimaspan')

        self.m_gbl.tracer_impl.start_trace.return_value = 'wooimatrace'
        val = beeline.start_trace()
        self.assertEqual(val, 'wooimatrace')

    def test_marshal_trace_context_returns_value(self):
        ''' ensure the top-level definition of marshal_trace_context returns a value '''
        self.m_gbl.tracer_impl.marshal_trace_context.return_value = 'asdf'
        val = beeline.marshal_trace_context()
        self.assertEqual(val, 'asdf')

    def test_trace_wrapper(self):
        ''' ensure that the trace wrapper decorates a function and starts a trace '''
        _beeline = beeline.Beeline()
        with patch('beeline.get_beeline') as m_gbl:
            m_gbl.return_value = _beeline
            _beeline.tracer_impl._run_hooks_and_send = Mock()

            @beeline.traced(name="my_sum")
            def my_sum(a, b):
                return a + b

            # this should accept the function's arguments normally and return the function's value
            # if there is one
            self.assertEqual(my_sum(1, 2), 3)
            # check that an event was sent, from which we can infer that the function was wrapped
            self.assertTrue(_beeline.tracer_impl._run_hooks_and_send.called)

    def test_treaded_trace(self):
        _beeline = beeline.Beeline()

        with patch('beeline.get_beeline') as m_gbl:
            m_gbl.return_value = _beeline
            _beeline.tracer_impl._run_hooks_and_send = Mock()

            _beeline.tracer_impl.start_trace(trace_id="asdf")
            self.assertEqual(_beeline.tracer_impl._state.trace_id, "asdf")

            def thread_func():
                # confirm no trace state in new thread
                self.assertFalse(hasattr(_beeline.tracer_impl._state, 'trace_id'))

            t = threading.Thread(target=thread_func)
            t.start()  
            t.join()

            @beeline.traced_thread
            def traced_thread_func():
                self.assertEqual(_beeline.tracer_impl._state.trace_id, "asdf")

                with _beeline.tracer(name="foo") as span:
                    self.assertEqual(span.trace_id, "asdf")
                    self.assertEqual(span.parent_id, _beeline.tracer_impl._state.stack[0].id)

            t = threading.Thread(target=traced_thread_func)
            t.start()
            t.join()

            # test use of beeline client
            @_beeline.traced_thread
            def traced_thread_func_2():
                self.assertEqual(_beeline.tracer_impl._state.trace_id, "asdf")

                with _beeline.tracer(name="foo2") as span:
                    self.assertEqual(span.trace_id, "asdf")
                    self.assertEqual(span.parent_id, _beeline.tracer_impl._state.stack[0].id)

            t = threading.Thread(target=traced_thread_func_2)
            t.start()
            t.join()

class TestBeelineNotInitialized(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline.get_beeline').start()
        self.m_gbl.return_value = None

    def test_trace_wrapper(self):
        ''' ensure the trace wrapper doesn't break if the beeline is not initialized '''
        self.assertIsNone(beeline.get_beeline())
        @beeline.traced(name="my_sum")
        def my_sum(a, b):
            return a + b

        # this should not crash if the beeline isn't initialized
        # it should also accept arguments normally and return the function's value
        self.assertEqual(my_sum(1, 2), 3)

    def test_tracer_context_manager(self):
        ''' ensure the tracer context manager doesn't break if the beeline is not initialized '''
        self.assertIsNone(beeline.get_beeline())
        def my_sum(a, b):
            with beeline.tracer(name="my_sum"):
                return a + b

        # this should not crash if the beeline isn't initialized
        # it should also accept arguments normally and return the function's value
        self.assertEqual(my_sum(1, 2), 3)

    def test_traced_thread(self):
        self.assertIsNone(beeline.get_beeline())
        @beeline.traced_thread
        def my_sum(a, b):
            return a + b

        # this should not crash if the beeline isn't initialized
        # it should also accept arguments normally and return the function's value
        self.assertEqual(my_sum(1, 2), 3)
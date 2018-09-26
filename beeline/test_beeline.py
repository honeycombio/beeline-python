import unittest
from mock import Mock, patch, call

import beeline
import libhoney
assert libhoney

class TestBeeline(unittest.TestCase):
    def setUp(self):
        self.m_gbl = patch('beeline._GBL').start()

    def tearDown(self):
        self.m_gbl.stop()

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
        delattr(ev, 'traced_event')
        _beeline = beeline.Beeline()
        _beeline.tracer_impl = Mock()
        _beeline._run_hooks_and_send(ev)

        # no hooks, not a traced event - call send
        ev.send.assert_called_once_with()
        ev.send_presampled.assert_not_called()
        _beeline.tracer_impl.send_traced_event.assert_not_called()

        # traced_event is an implicit attribute on Mock, so send_traced_event
        # should be called
        traced_ev = Mock()
        _beeline._run_hooks_and_send(traced_ev)
        _beeline.tracer_impl.send_traced_event.assert_called_once_with(traced_ev, presampled=False)

    def test_run_hooks_and_send_sampler(self):
        ''' ensure send works with a sampler hook defined '''
        def _sampler_drop_all(fields):
            return False, 0
        m_sampler_hook = Mock()
        m_sampler_hook.side_effect = _sampler_drop_all
        _beeline = beeline.Beeline(sampler_hook=m_sampler_hook)
        _beeline.tracer_impl = Mock()
        ev = Mock()
        # non-traced event
        delattr(ev, 'traced_event')

        _beeline._run_hooks_and_send(ev)
        m_sampler_hook.assert_called_once_with(ev.fields())
        ev.send_presampled.assert_not_called()
        ev.send.assert_not_called()

        def _sampler_drop_none(fields):
            return True, 100

        ev = Mock()
        # non-traced event
        delattr(ev, 'traced_event')
        m_sampler_hook.reset_mock()

        m_sampler_hook.side_effect = _sampler_drop_none

        _beeline._run_hooks_and_send(ev)
        m_sampler_hook.assert_called_once_with(ev.fields())
        self.assertEqual(ev.sample_rate, 100)
        ev.send_presampled.assert_called_once_with()
        ev.send.assert_not_called()

        # traced event
        ev = Mock()
        m_sampler_hook.reset_mock()

        _beeline._run_hooks_and_send(ev)
        m_sampler_hook.assert_called_once_with(ev.fields())
        self.assertEqual(ev.sample_rate, 100)
        _beeline.tracer_impl.send_traced_event.assert_called_once_with(ev, presampled=True)
        ev.send_presampled.assert_not_called()
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
        delattr(ev, 'traced_event')
        ev.fields.return_value = {
            "thing i don't want": "get it out of here",
            "happy data": "so happy",
        }

        _beeline._run_hooks_and_send(ev)
        _beeline.tracer_impl.send_traced_event.assert_not_called()
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

import unittest
from mock import Mock, patch

import beeline
import libhoney

class TestBeelineSendEvent(unittest.TestCase):
    def setUp(self):
        self.m_gbl = patch('beeline._GBL').start()

    def tearDown(self):
        self.m_gbl.stop()

    def test_send_event(self):
        ''' test correct behavior for send_event '''
        ev = Mock()
        delattr(ev, 'traced_event')
        _beeline = beeline.Beeline()
        _beeline.state = Mock()
        _beeline.state.pop_event.return_value = ev
        _beeline.send_event()
        _beeline.state.pop_event.assert_called_once_with()
        ev.send.assert_called_once_with()

    def test_send_no_events(self):
        ''' ensure nothing crashes when we try to send with no events in the
        stack '''
        _beeline = beeline.Beeline()
        _beeline.state = Mock()
        _beeline.state.pop_event.return_value = None
        _beeline.send_event()
        _beeline.state.pop_event.assert_called_once_with()

    def send_traced_event(self):
        ''' test send_event behavior when event is traced '''
        ev = Mock()
        ev.traced_event = True
        self.m_state.pop_event.return_value = ev
        beeline._send_event()
        self.m_state.pop_event.assert_called_once_with()
        self.m_tracer.send_traced_event.assert_called_once_with(ev)

    def test_send_all(self):
        ''' ensure events are flushed '''
        ev1, ev2, ev3 = Mock(), Mock(), Mock()
        ev3.send.side_effect = libhoney.SendError("bad thing!")
        delattr(ev1, 'traced_event')
        delattr(ev2, 'traced_event')
        delattr(ev3, 'traced_event')
        _beeline = beeline.Beeline()
        _beeline.state = Mock()
        _beeline.state.pop_event.side_effect = [ev1, ev2, ev3, None]

        _beeline.send_all()

        ev1.send.assert_called_once_with()
        ev2.send.assert_called_once_with()
        ev3.send.assert_called_once_with()

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

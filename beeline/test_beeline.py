import unittest
from mock import Mock, patch

import beeline
import libhoney

class TestBeelineSendEvent(unittest.TestCase):
    def setUp(self):
        self.m_client = patch('beeline.g_client').start()
        self.m_state = patch('beeline.g_state').start()
        self.m_tracer = patch('beeline.g_tracer').start()

    def tearDown(self):
        self.m_client.stop()
        self.m_state.stop()
        self.m_tracer.stop()

    def test_send_event(self):
        ''' test correct behavior for send_event '''
        ev = Mock()
        delattr(ev, 'traced_event')
        self.m_state.pop_event.return_value = ev
        beeline._send_event()
        self.m_state.pop_event.assert_called_once_with()
        ev.send.assert_called_once_with()

    def test_send_no_events(self):
        ''' ensure nothing crashes when we try to send with no events in the
        stack '''
        self.m_state.pop_event.return_value = None
        beeline._send_event()
        self.m_state.pop_event.assert_called_once_with()

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
        self.m_state.pop_event.side_effect = [ev1, ev2, ev3, None]

        beeline._send_all()

        ev1.send.assert_called_once_with()
        ev2.send.assert_called_once_with()
        ev3.send.assert_called_once_with()

    def test_run_hooks_and_send_no_hooks(self):
        ''' ensure send works when no hooks defined '''
        ev = Mock()
        delattr(ev, 'traced_event')
        beeline._run_hooks_and_send(ev)

        # no hooks, not a traced event - call send
        ev.send.assert_called_once_with()
        ev.send_presampled.assert_not_called()
        self.m_tracer.send_traced_event.assert_not_called()

        # traced_event is an implicit attribute on Mock, so send_traced_event
        # should be called
        traced_ev = Mock()
        beeline._run_hooks_and_send(traced_ev)
        self.m_tracer.send_traced_event.assert_called_once_with(traced_ev, presampled=False)

    def test_run_hooks_and_send_sampler(self):
        ''' ensure send works with a sampler hook defined '''
        with patch('beeline.g_sampler_hook') as m_sampler:
            def _sampler_drop_all(fields):
                return False, 0
            m_sampler.side_effect = _sampler_drop_all
            ev = Mock()
            # non-traced event
            delattr(ev, 'traced_event')

            beeline._run_hooks_and_send(ev)
            m_sampler.assert_called_once_with(ev.fields())
            ev.send_presampled.assert_not_called()
            ev.send.assert_not_called()

            def _sampler_drop_none(fields):
                return True, 100

            ev = Mock()
            # non-traced event
            delattr(ev, 'traced_event')
            m_sampler.reset_mock()

            m_sampler.side_effect = _sampler_drop_none

            beeline._run_hooks_and_send(ev)
            m_sampler.assert_called_once_with(ev.fields())
            self.assertEqual(ev.sample_rate, 100)
            ev.send_presampled.assert_called_once_with()
            ev.send.assert_not_called()

            # traced event
            ev = Mock()
            m_sampler.reset_mock()

            beeline._run_hooks_and_send(ev)
            m_sampler.assert_called_once_with(ev.fields())
            self.assertEqual(ev.sample_rate, 100)
            self.m_tracer.send_traced_event.assert_called_once_with(ev, presampled=True)
            ev.send_presampled.assert_not_called()
            ev.send.assert_not_called()

    def test_run_hooks_and_send_presend_hook(self):
        ''' ensure send works when presend hook is defined '''
        with patch('beeline.g_presend_hook') as m_presend:
            def _presend_hook(fields):
                fields["thing i want"] = "put it there"
                del fields["thing i don't want"]
            m_presend.side_effect = _presend_hook

            ev = Mock()
            delattr(ev, 'traced_event')
            ev.fields.return_value = {
                "thing i don't want": "get it out of here",
                "happy data": "so happy",
            }

            beeline._run_hooks_and_send(ev)
            self.m_tracer.send_traced_event.assert_not_called()
            ev.send_presampled.assert_not_called()
            ev.send.assert_called_once_with()
            self.assertDictEqual(
                ev.fields(),
                {
                    "thing i want": "put it there",
                    "happy data": "so happy",
                },
            )

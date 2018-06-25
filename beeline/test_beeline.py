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

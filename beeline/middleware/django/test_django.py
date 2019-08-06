import unittest
from mock import Mock, patch

from beeline.middleware.django import HoneyMiddlewareBase

class SimpleWSGITest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline.middleware.django.beeline').start()

    def test_call_middleware(self):
        ''' Just call the middleware and ensure that the code runs '''
        mock_req = Mock()
        mock_resp = Mock()
        mock_trace = Mock()
        self.m_gbl.start_trace.return_value = mock_trace

        mw = HoneyMiddlewareBase(mock_resp)
        resp = mw(mock_req)
        self.m_gbl.start_trace.assert_called_once()

        mock_resp.assert_called_once_with(mock_req)

        self.m_gbl.finish_trace.assert_called_once_with(mock_trace)
        self.assertEqual(resp, mock_resp.return_value)
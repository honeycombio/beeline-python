import unittest
from mock import Mock, patch

class TestRequestsPatch(unittest.TestCase):
    def test_request_fn_injects_headers_and_returns(self):
        from beeline.patch.requests import request

        with patch('beeline.get_beeline') as m_bl:
            bl = Mock()
            m_bl.return_value = bl

            trace_context = "1;trace_id=foo,parent_id=bar,context=base64value=="

            bl.tracer_impl.marshal_trace_context.return_value = trace_context

            # this is the class instance (Session object) that is passed to our request function
            # by wrapt
            m_session = Mock()
            m_session.headers = {}

            # this is our request call that's being wrapped
            m_request = Mock()
            m_request.return_value = Mock(headers={'content-type': 'application/json', 'content-length': 23}, status_code=500)
            args = ['get']
            kwargs = {'url': 'http://example.com'}
            ret = request(m_request, m_session, args, kwargs)

            m_request.assert_called_once_with(*args, **kwargs)
            self.assertEqual(ret, m_request.return_value)
            self.assertEqual(m_session.headers['X-Honeycomb-Trace'], trace_context)

from __future__ import absolute_import
import six
import unittest
from mock import Mock, patch

import urllib


class TestUrllibPatch(unittest.TestCase):
    @unittest.skipIf(six.PY2, "urllib not compatible with python2")
    def test_request_fn_injects_headers_and_returns(self):
        from beeline.patch.urllib import _urllibopen  # pylint: disable=bad-option-value,import-outside-toplevel

        with patch('beeline.get_beeline') as m_bl:
            bl = Mock()
            m_bl.return_value = bl

            trace_context = "1;trace_id=foo,parent_id=bar,context=base64value=="

            bl.tracer_impl.http_trace_propagation_hook.return_value = {
                'X-Honeycomb-Trace': trace_context
            }
            # this is our request call that's being wrapped
            m_urlopen = Mock()
            m_urlopen.return_value = Mock(
                headers={'content-type': 'application/json', 'content-length': 23}, status_code=500)
            args = ('https://example.com',)
            kwargs = {}
            ret = _urllibopen(m_urlopen, None, args, kwargs)

            # ensure our arg gets modified and header set before the real function is called
            self.assertEqual(
                type(m_urlopen.call_args.args[0]), urllib.request.Request)
            self.assertEqual(
                m_urlopen.call_args.args[0].headers['X-Honeycomb-Trace'], trace_context)
            m_urlopen.asset_called_once()
            m_urlopen.reset_mock()

            # ensure we return a response
            self.assertEqual(ret, m_urlopen.return_value)

            # test case with Request object
            m_urlopen.return_value = Mock(
                headers={'content-type': 'application/json', 'content-length': 23}, status_code=500)
            req = urllib.request.Request('https://example.com/2')
            args = [req]
            ret = _urllibopen(m_urlopen, None, args, kwargs)
            self.assertEqual(type(args[0]), urllib.request.Request)
            self.assertEqual(args[0].full_url, 'https://example.com/2')
            self.assertEqual(
                args[0].headers['X-Honeycomb-Trace'], trace_context)
            self.assertEqual(ret, m_urlopen.return_value)
            m_urlopen.assert_called_once_with(*args, **kwargs)

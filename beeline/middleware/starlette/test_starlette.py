import asyncio
import unittest
from unittest.mock import AsyncMock
from mock import Mock, call, patch

from beeline.middleware.starlette import HoneyMiddleware


class SimpleWSGITest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline.middleware.starlette.beeline').start()

    def test_call_middleware(self):
        ''' Just call the middleware and ensure that the code runs '''
        mock_req = Mock()
        mock_resp = AsyncMock()

        mw = HoneyMiddleware(mock_resp)
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'scheme': 'https',
            'query_string': b'foo=bar',
            'headers': [],
        }
        resp = asyncio.run(mw(scope, mock_req, mock_resp))
        self.m_gbl.start_trace.assert_called_once()

        mock_resp.assert_called_once()

        self.m_gbl.finish_trace.assert_called_once()
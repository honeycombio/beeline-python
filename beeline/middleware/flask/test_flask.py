import unittest
from mock import Mock, patch, ANY

from beeline.middleware.flask import HoneyWSGIMiddleware, HoneyDBMiddleware


class SimpleWSGITest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline.middleware.flask.beeline').start()

    def test_call_middleware(self):
        ''' Just call the middleware and ensure that the code runs '''
        mock_app = Mock()
        mock_resp = Mock()
        mock_trace = Mock()
        mock_environ = {}
        self.m_gbl.propagate_and_start_trace.return_value = mock_trace

        mw = HoneyWSGIMiddleware(mock_app)
        mw({}, mock_resp)
        self.m_gbl.propagate_and_start_trace.assert_called_once()

        mock_app.assert_called_once_with(mock_environ, ANY)

        # get the response function passed to the app
        resp_func = mock_app.mock_calls[0][1][1]
        # call it to make sure it does what we want
        # the values here don't really matter
        resp_func("200", 2)

        mock_resp.assert_called_once_with("200", 2)
        self.m_gbl.finish_trace.assert_called_once_with(mock_trace)


class HoneyDBMiddlewareTest(unittest.TestCase):
    @patch("beeline.middleware.flask.current_app")
    def test_before_cursor_execute(self, current_app):
        with patch("beeline.middleware.flask.beeline") as beeline:
            mw = HoneyDBMiddleware(current_app)
            mw.before_cursor_execute(
                conn=Mock(name="conn"),
                cursor=Mock(name="cursor"),
                statement="SELECT * FROM widgets WHERE ID IN :widget_ids",
                parameters={'widget_ids': (1, 2)},
                context=Mock(name="context"),
                executemany=False
            )
            beeline.start_span.assert_called_with(
                context={
                    'name': 'flask_db_query',
                    'type': 'db',
                    'db.query': 'SELECT * FROM widgets WHERE ID IN :widget_ids',
                    'db.query_args': ['widget_ids=(1, 2)']
                }
            )

import unittest
from mock import Mock, call, patch

import django
from django.http import HttpResponse
from django.test.client import Client
from django.conf.urls import url

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
        self.m_gbl.propagate_and_start_trace.return_value = mock_trace

        mw = HoneyMiddlewareBase(mock_resp)
        resp = mw(mock_req)
        self.m_gbl.propagate_and_start_trace.assert_called_once()

        mock_resp.assert_called_once_with(mock_req)

        self.m_gbl.finish_trace.assert_called_once_with(mock_trace)
        self.assertEqual(resp, mock_resp.return_value)


@unittest.skipIf(django.VERSION < (2, 2), "Routes are only supported on Django 2.2 and higher")
class FullViewTestCase(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.m_gbl = patch('beeline.middleware.django.beeline').start()

        # Unfortunately we need to import these quite late, because if we use a
        # top-level import, the test discovery procedure checks if `settings`
        # is a subclass of `TestCase`, causing the settings to be initialized,
        # which isn't possible.
        from django.conf import settings  # pylint: disable=bad-option-value,import-outside-toplevel
        from django.utils.functional import empty  # pylint: disable=bad-option-value,import-outside-toplevel
        assert not settings.configured
        # On shutdown:
        self.addCleanup(lambda: setattr(settings, "_wrapped", empty))
        settings.configure(
            MIDDLEWARE=['beeline.middleware.django.HoneyMiddlewareHttp'],
            ALLOWED_HOSTS=['testserver'],
            ROOT_URLCONF=(
                url("^hello/(?P<greetee>[^/]+)/$", self._view, name="greet"),
            ),
        )

    def _view(self, request, *args, **kwargs):
        return HttpResponse(kwargs["greetee"], status=200)

    def test_middleware(self):
        mock_trace = Mock()
        self.m_gbl.propagate_and_start_trace.return_value = mock_trace

        response = Client().get('/hello/world/')
        self.assertEqual(response.content, b"world")

        self.m_gbl.add_context_field.assert_has_calls([
            call("django.view_func", "_view"),
            call("request.route", "^hello/(?P<greetee>[^/]+)/$"),
        ])
        self.m_gbl.finish_trace.assert_called_once_with(mock_trace)

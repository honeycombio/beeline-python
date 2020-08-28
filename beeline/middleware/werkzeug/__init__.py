import beeline
from beeline.propagation import Request
from beeline.middleware.wsgi import WSGIRequest


class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        wr = WSGIRequest("werkzeug", environ)

        root_span = beeline.propagate_and_start_trace(wr.request_context(), wr)

        def _start_response(status, headers, *args):
            beeline.add_context_field("response.status_code", status)
            beeline.finish_trace(root_span)

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)

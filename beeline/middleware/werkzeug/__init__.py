import beeline
from beeline.propagation import Request


class WerkzeugRequest(Request):
    def __init__(self, environ):
        self._environ = environ

    def header(self, key):
        # FIXME: Is this .upper strictly necessary? Does environ already do it for us?
        lookup_key = key.upper().replace('-', '_')
        return self._environ.get(lookup_key)

    def method(self):
        return self._environ.get('REQUEST_METHOD')

    def scheme(self):
        return self._environ.get('wsgi.url_scheme')

    def host(self):
        return self._environ.get('HTTP_HOST')

    def path(self):
        return self._environ.get('PATH_INFO')

    def query(self):
        return self._environ.get('QUERY_STRING')

    def middleware_request(self):
        return self._environ


class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        wr = WerkzeugRequest(environ)

        request_context = self.get_context_from_environ(environ)
        root_span = beeline.propagate_and_start_trace(request_context, wr)

        def _start_response(status, headers, *args):
            beeline.add_context_field("response.status_code", status)
            beeline.finish_trace(root_span)

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)

    def get_context_from_environ(self, environ):
        request_method = environ.get('REQUEST_METHOD')
        if request_method:
            trace_name = "werkzeug_http_%s" % request_method.lower()
        else:
            trace_name = "werkzeug_http"

        return {
            "name": trace_name,
            "type": "http_server",
            "request.host": environ.get('HTTP_HOST'),
            "request.method": request_method,
            "request.path": environ.get('PATH_INFO'),
            "request.remote_addr": environ.get('REMOTE_ADDR'),
            "request.content_length": environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": environ.get('HTTP_USER_AGENT'),
            "request.scheme": environ.get('wsgi.url_scheme'),
            "request.query": environ.get('QUERY_STRING')
        }

from beeline.propagation import Request


class WSGIRequest(Request):
    def __init__(self, mwname, environ):
        self._mwname = mwname
        self._environ = environ

    def header(self, key):
        # FIXME: Is this .upper strictly necessary? Does environ already do it for us?
        lookup_key = "HTTP_" + key.upper().replace('-', '_')
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

    def request_context(self):
        request_method = self._environ.get('REQUEST_METHOD')
        if request_method:
            trace_name = "%s_http_%s" % (self._mwname, request_method.lower())
        else:
            trace_name = "%s_http" % self._mwname

        return {
            "name": trace_name,
            "type": "http_server",
            "request.host": self._environ.get('HTTP_HOST'),
            "request.method": request_method,
            "request.path": self._environ.get('PATH_INFO'),
            "request.remote_addr": self._environ.get('REMOTE_ADDR'),
            "request.content_length": self._environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": self._environ.get('HTTP_USER_AGENT'),
            "request.scheme": self._environ.get('wsgi.url_scheme'),
            "request.query": self._environ.get('QUERY_STRING')
        }

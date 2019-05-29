import beeline

class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_method = environ.get('REQUEST_METHOD')
        if request_method:
            trace_name = "werkzeug_http_%s" % request_method.lower()
        else:
            trace_name = "werkzeug_http"
        trace = beeline.start_trace(context={
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
        })

        def _start_response(status, headers, *args):
            beeline.add_context_field("response.status_code", status)
            beeline.finish_trace(trace)

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)

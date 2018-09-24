import beeline

class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        trace_name = "bottle_http_%s" % environ['REQUEST_METHOD'].lower()
        trace = beeline.start_trace(context={
            "name": trace_name,
            "type": "http_server",
            "request.host": environ['HTTP_HOST'],
            "request.method": environ['REQUEST_METHOD'],
            "request.path": environ['PATH_INFO'],
            "request.remote_addr": environ['REMOTE_ADDR'],
            "request.content_length": environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": environ['HTTP_USER_AGENT'],
            "request.scheme": environ['wsgi.url_scheme'],
            "request.query": environ['QUERY_STRING']
        })

        def _start_response(status, headers, *args):
            beeline.add_context_field("response.status_code", status)
            beeline.finish_trace(trace)

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)
import datetime
import threading

import beeline
from beeline.trace import unmarshal_trace_context
from flask import current_app, signals
# needed to build a request object from environ in the middleware
from werkzeug.wrappers import Request

def _get_trace_context(environ):
    ''' returns trace_id, parent_id, context '''
    # http://werkzeug.pocoo.org/docs/0.14/wrappers/#base-wrappers
    req = Request(environ, shallow=True)



    trace_context = req.headers.get('x-honeycomb-trace')
    beeline.internal.log("got trace context: %s", trace_context)
    if trace_context:
        try:
            return unmarshal_trace_context(trace_context)
        except Exception as e:
            beeline.internal.log('error attempting to extract trace context: %s', beeline.internal.stringify_exception(e))

    return None, None, None

class HoneyMiddleware(object):

    def __init__(self, app, db_events=True):
        self.app = app
        if signals.signals_available:
            self.app.teardown_request(self._teardown_request)
        app.wsgi_app = HoneyWSGIMiddleware(app.wsgi_app)
        if db_events:
            app = HoneyDBMiddleware(app)

    def _teardown_request(self, exception):
        if exception:
            beeline.add_field('request.error_detail', beeline.internal.stringify_exception(exception))
            beeline.add_field('request.error', str(type(exception)))
            beeline.internal.send_event()


class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_method = environ.get('REQUEST_METHOD')
        if request_method:
            trace_name = "flask_http_%s" % request_method.lower()
        else:
            trace_name = "flask_http"

        trace_id, parent_id, context = _get_trace_context(environ)

        root_span = beeline.start_trace(context={
            "type": "http_server",
            "name": trace_name,
            "request.host": environ.get('HTTP_HOST'),
            "request.method": request_method,
            "request.path": environ.get('PATH_INFO'),
            "request.remote_addr": environ.get('REMOTE_ADDR'),
            "request.content_length": environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": environ.get('HTTP_USER_AGENT'),
            "request.scheme": environ.get('wsgi.url_scheme'),
            "request.query": environ.get('QUERY_STRING')
        }, trace_id=trace_id, parent_span_id=parent_id)

        # populate any propagated custom context
        if isinstance(context, dict):
            for k, v in context.items():
                beeline.add_trace_field(k, v)

        def _start_response(status, headers, *args):
            status_code = int(status[0:4])
            beeline.add_context_field("response.status_code", status_code)
            if status_code != 500:
                beeline.finish_trace(root_span)
            elif status_code == 500 and not signals.signals_available:
                beeline.finish_trace(root_span)

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)


class HoneyDBMiddleware(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

        self.state = threading.local()
        self.state.span = None

    def init_app(self, app):
        try:
            from sqlalchemy.engine import Engine
            from sqlalchemy.event import listen

            listen(Engine, 'before_cursor_execute', self.before_cursor_execute)
            listen(Engine, 'after_cursor_execute', self.after_cursor_execute)
            listen(Engine, 'handle_error', self.handle_error)
        except ImportError:
            pass

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        params = []

        # the type of parameters passed in varies depending on DB - handle list, dict, and tuple
        if type(parameters) == tuple or type(parameters) == list:
            for param in parameters:
                if type(param) == datetime.datetime:
                    param = param.isoformat()
                params.append(param)
        elif type(parameters) == dict:
            for k,v in parameters.items():
                param = "%s=" % k
                if type(v) == datetime.datetime:
                     v = v.isoformat()
                param += "%s" % v
                params.append(param)

        self.state.span = beeline.start_span(context={
            "name": "flask_db_query",
            "type": "db",
            "db.query": statement,
            "db.query_args": params,
        })

        self.query_start_time = datetime.datetime.now()

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        query_duration = datetime.datetime.now() - self.query_start_time

        beeline.add_context({
            "db.duration": query_duration.total_seconds() * 1000,
            "db.last_insert_id": cursor.lastrowid,
            "db.rows_affected": cursor.rowcount,
        })
        if self.state.span:
            beeline.finish_span(self.state.span)
        self.state.span = None

    def handle_error(self, context):
        beeline.add_context_field("db.error", beeline.internal.stringify_exception(context.original_exception))
        if self.state.span:
            beeline.finish_span(self.state.span)
        self.state.span = None

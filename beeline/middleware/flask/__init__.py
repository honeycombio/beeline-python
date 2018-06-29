import datetime
import beeline
from flask import current_app, signals


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
            beeline.add_field('request.error_detail', str(exception))
            beeline.add_field('request.error', str(type(exception)))
            beeline._send_event()


class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        trace_name = "flask_http_%s" % environ['REQUEST_METHOD'].lower()
        beeline._new_event(data={
            "type": "http_server",
            "request.host": environ['HTTP_HOST'],
            "request.method": environ['REQUEST_METHOD'],
            "request.path": environ['PATH_INFO'],
            "request.remote_addr": environ['REMOTE_ADDR'],
            "request.content_length": environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": environ['HTTP_USER_AGENT'],
            "request.scheme": environ['wsgi.url_scheme'],
            "request.query": environ['QUERY_STRING']
        }, trace_name=trace_name, top_level=True)

        def _start_response(status, headers, *args):
            status_code = int(status[0:4])
            beeline.add_field("response.status_code", status_code)
            if status_code != 500:
                beeline._send_event()
            elif status_code == 500 and not signals.signals_available:
                beeline._send_event()

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)


class HoneyDBMiddleware(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

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
        for param in parameters:
            if type(param) == datetime.datetime:
                param = param.isoformat()
            params.append(param)

        beeline._new_event(data={
            "type": "db",
            "db.query": statement,
            "db.query_args": params,
        }, trace_name="flask_db_query")

        self.query_start_time = datetime.datetime.now()

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        query_duration = datetime.datetime.now() - self.query_start_time

        beeline.add({
            "db.duration": query_duration.total_seconds() * 1000,
            "db.last_insert_id": cursor.lastrowid,
            "db.rows_affected": cursor.rowcount,
        })
        beeline._send_event()

    def handle_error(self, context):
        beeline.add_field("db.error", str(context.original_exception))
        beeline._send_event()

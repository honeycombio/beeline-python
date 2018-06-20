import datetime
import beeline
from flask import current_app


class HoneyWSGIMiddleWare(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        self.start = datetime.datetime.now()
        beeline._new_event(data={
            "request.host": environ['HTTP_HOST'],
            "request.method": environ['REQUEST_METHOD'],
            "request.path": environ['PATH_INFO'],
            "request.remote_addr": environ['REMOTE_ADDR'],
            "request.content_length": environ.get('CONTENT_LENGTH', 0),
            "request.user_agent": environ['HTTP_USER_AGENT'],
            "request.scheme": environ['wsgi.url_scheme'],
            "request.query": environ['QUERY_STRING']
        }, trace_name="flask_request", top_level=True)

        def _start_response(status, headers, *args):
            beeline.add_field("response.status_code", status)
            diff = datetime.datetime.now() - self.start
            beeline.add_field("duration_ms", diff.total_seconds() * 1000)
            beeline._send_event()

            return start_response(status, headers, *args)

        return self.app(environ, _start_response)


class HoneyMiddleware(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.wsgi_app = HoneyWSGIMiddleWare(app.wsgi_app)

        try:
            from sqlalchemy.engine import Engine
            from sqlalchemy.event import listen

            listen(Engine, 'before_cursor_execute', self.before_cursor_execute)
            listen(Engine, 'after_cursor_execute', self.after_cursor_execute)
        except ImportError:
            pass

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        beeline._new_event(data={
            "db.query": statement,
            "db.query_args": parameters,
        }, trace_name="flask_db_query")

        self.query_start_time = datetime.datetime.now()

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        query_duration = datetime.datetime.now() - self.query_start_time

        beeline.add_field("db.duration", query_duration.total_seconds() * 1000)
        beeline.add_field("db.last_insert_id", cursor.lastrowid)
        beeline.add_field("db.rows_affected", cursor.rowcount)
        beeline._send_event()

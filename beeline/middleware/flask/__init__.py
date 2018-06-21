import datetime
import beeline
from flask import current_app


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
            beeline.add_field("response.status_code", status)
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
        except ImportError:
            pass

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not current_app:
            return

        beeline._new_event(data={
            "type": "db",
            "db.query": statement,
            "db.query_args": parameters,
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

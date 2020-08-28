import datetime
import threading

import beeline
import flask  # to avoid namespace collision with request vs Request
from beeline.propagation import Request
from flask import current_app, signals
# needed to build a request object from environ in the middleware
from werkzeug.wrappers import Request
from beeline.middleware.wsgi import WSGIRequest


class HoneyMiddleware(object):

    def __init__(self, app, db_events=True):
        self.app = app
        self.app.before_request(self._before_request)
        if signals.signals_available:
            self.app.teardown_request(self._teardown_request)
        app.wsgi_app = HoneyWSGIMiddleware(app.wsgi_app)
        if db_events:
            app = HoneyDBMiddleware(app)

    def _before_request(self):
        beeline.add_field("request.route", flask.request.endpoint)

    def _teardown_request(self, exception):
        if exception:
            beeline.add_field('request.error_detail',
                              beeline.internal.stringify_exception(exception))
            beeline.add_field('request.error', str(type(exception)))
            beeline.internal.send_event()


class HoneyWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ, shallow=True)
        wr = WSGIRequest("flask", environ)

        root_span = beeline.propagate_and_start_trace(wr.request_context(), wr)

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
            from sqlalchemy.engine import Engine  # pylint: disable=bad-option-value,import-outside-toplevel
            from sqlalchemy.event import listen  # pylint: disable=bad-option-value,import-outside-toplevel

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
            for k, v in parameters.items():
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
            "db.last_insert_id": getattr(cursor, 'lastrowid', None),
            "db.rows_affected": cursor.rowcount,
        })
        if self.state.span:
            beeline.finish_span(self.state.span)
        self.state.span = None

    def handle_error(self, context):
        if not current_app:
            return

        beeline.add_context_field(
            "db.error", beeline.internal.stringify_exception(context.original_exception))
        if self.state.span:
            beeline.finish_span(self.state.span)
        self.state.span = None

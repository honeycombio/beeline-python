import os
import libhoney
import datetime
from django.db import connection
import uuid


class DBWrapper(object):
    def __init__(self, trace_id):
        self.trace_id = trace_id
        self.parent_id = trace_id
        self.span_id = uuid.uuid4()

    def __call__(self, execute, sql, params, many, context):
        span_start = datetime.datetime.now()

        event = libhoney.Event(data={
            "trace.parent_id": str(self.parent_id),
            "trace.trace_id": str(self.trace_id),
            "trace.span_id": str(self.span_id),
            "db.query": sql,
            "db.query_args": params,
        })

        self.span_id = uuid.uuid4()

        try:
            db_call_start = datetime.datetime.now()
            result = execute(sql, params, many, context)
            db_call_diff = datetime.datetime.now() - db_call_start
            event.add_field("db.duration", db_call_diff.total_seconds() * 1000)
        except Exception as e:
            event.add_field("db.error", e)
            raise
        else:
            return result
        finally:
            vendor = context['connection'].vendor

            if vendor == "postgresql" or vendor == "mysql":
                event.add_field("db.last_insert_id",
                                context['cursor'].cursor.lastrowid)
                event.add_field("db.rows_affected",
                                context['cursor'].cursor.rowcount)

            span_diff = datetime.datetime.now() - span_start
            event.add_field("duration_ms", span_diff.total_seconds() * 1000)
            event.send()


class HoneyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        libhoney.init(writekey=os.environ["HONEYCOMB_WRITE_KEY"],
                      dataset=os.environ["HONEYCOMB_DATASET_NAME"])

    def __call__(self, request):

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        trace_id = uuid.uuid4()

        db_wrapper = DBWrapper(trace_id)
        with connection.execute_wrapper(db_wrapper):
            start = datetime.datetime.now()
            event = libhoney.Event(data={
                "trace.parent_id": None,
                "trace.trace_id": str(trace_id),
                "trace.span_id": str(trace_id),
                "request.host": request.get_host(),
                "request.method": request.method,
                "request.path": request.path,
                "request.remote_addr": request.META['REMOTE_ADDR'],
                "request.content_length": request.META['CONTENT_LENGTH'],
                "request.user_agent": request.META['HTTP_USER_AGENT'],
                "request.scheme": request.scheme,
                "request.secure": request.is_secure(),
                "request.query": request.GET,
                "request.xhr": request.is_ajax(),
                "request.post": request.POST
            })

            response = self.get_response(request)

            # Code to be executed for each request/response after
            # the view is called.

            event.add_field("response.status_code", response.status_code)
            diff = datetime.datetime.now() - start
            event.add_field("duration_ms", diff.total_seconds() * 1000)
            event.send()

            return response

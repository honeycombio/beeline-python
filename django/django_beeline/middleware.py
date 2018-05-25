import os
import datetime
import libhoney
from django.db import connection


def db_wrapper(execute, sql, params, many, context):
    start = datetime.datetime.now()

    event = libhoney.Event(data={
        "db.query": sql,
        "db.query_args": params,
    })

    try:
        result = execute(sql, params, many, context)
    except Exception as e:
        event.add_field("db.error", e)
        raise
    else:
        return result
    finally:
        diff = datetime.datetime.now() - start
        vendor = context['connection'].vendor

        if vendor == "postgresql" or vendor == "mysql":
            event.add_field("db.last_insert_id",
                            context['cursor'].cursor.lastrowid)
            event.add_field("db.rows_affected",
                            context['cursor'].cursor.rowcount)

        event.add_field("db.duration", diff.total_seconds() * 1000)
        event.send()


class HoneyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        libhoney.init(writekey=os.environ["HONEYCOMB_WRITE_KEY"],
                      dataset=os.environ["HONEYCOMB_DATASET_NAME"])

    def __call__(self, request):

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        with connection.execute_wrapper(db_wrapper):
            start = datetime.datetime.now()
            event = libhoney.Event(data={
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

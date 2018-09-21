import datetime
import beeline
from django.db import connection


class HoneyDBWrapper(object):

    def __call__(self, execute, sql, params, many, context):
        vendor = context['connection'].vendor
        trace_name = "django_%s_query" % vendor

        with beeline.tracer(trace_name):
            beeline.add({
                "type": "db",
                "db.query": sql,
                "db.query_args": params,
            })

            try:
                db_call_start = datetime.datetime.now()
                result = execute(sql, params, many, context)
                db_call_diff = datetime.datetime.now() - db_call_start
                beeline.add_field(
                    "db.duration", db_call_diff.total_seconds() * 1000)
            except Exception as e:
                beeline.add_field("db.error", str(type(e)))
                beeline.add_field("db.error_detail", str(e))
                raise
            else:
                return result
            finally:
                if vendor == "postgresql" or vendor == "mysql":
                    beeline.add({
                        "db.last_insert_id": context['cursor'].cursor.lastrowid,
                        "db.rows_affected": context['cursor'].cursor.rowcount,
                    })


class HoneyMiddlewareBase(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.create_http_event(request)
        return response

    def create_http_event(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        trace_name = "django_http_%s" % request.method.lower()
        beeline.internal.new_event(data={
            "type": "http_server",
            "request.host": request.get_host(),
            "request.method": request.method,
            "request.path": request.path,
            "request.remote_addr": request.META['REMOTE_ADDR'],
            "request.content_length": request.META['CONTENT_LENGTH'],
            "request.user_agent": request.META['HTTP_USER_AGENT'],
            "request.scheme": request.scheme,
            "request.secure": request.is_secure(),
            "request.query": request.GET.dict(),
            "request.xhr": request.is_ajax(),
            "request.post": request.POST.dict()
        }, trace_name=trace_name, top_level=True)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        beeline.add_field("response.status_code", response.status_code)
        beeline.internal.send_event()

        return response

    def process_exception(self, request, exception):
        beeline.add_field("request.error_detail", str(exception))


class HoneyMiddlewareHttp(HoneyMiddlewareBase):
    pass


class HoneyMiddleware(HoneyMiddlewareBase):
    def __call__(self, request):
        try:
            db_wrapper = HoneyDBWrapper()
            # db instrumentation is only present in Django > 2.0
            with connection.execute_wrapper(db_wrapper):
                response = self.create_http_event(request)
        except AttributeError:
            response = self.create_http_event(request)

        return response

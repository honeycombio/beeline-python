''' patches base tornado classes to add honeycomb instrumentation '''

from wrapt import wrap_function_wrapper
import beeline
import tornado
assert tornado  # for pyflakes


def log_request(_log_request, instance, args, kwargs):
    try:
        # expecting signature `log_request(self, handler)`
        if len(args) == 1:
            handler = args[0]
            beeline.send_now({
                "duration_ms": handler.request.request_time() * 1000.0,
                "request.method": handler.request.method,
                "request.remote_addr": handler.request.remote_ip,
                "request.path": handler.request.uri,
                "request.query": handler.request.query,
                "request.host": handler.request.headers.get('Host'),
                "response.status_code": handler.get_status(),
            })
    except Exception:
        pass
    finally:
        _log_request(*args, **kwargs)


def log_exception(_log_exception, instance, args, kwargs):
    try:
        # expecting signature `log_exception(self, typ, value, tb)``
        if len(args) == 3:
            value = args[2]
            beeline.send_now({
                "request.method": instance.request.method,
                "request.path": instance.request.uri,
                "request.remote_addr": instance.request.remote_ip,
                "request.query": instance.request.query,
                "request.host": instance.request.get('Host'),
                "request.error": type(value).__name__,
                "request.error_detail": beeline.internal.stringify_exception(value),
            })
    except Exception:
        pass
    finally:
        _log_exception(*args, **kwargs)


wrap_function_wrapper('tornado.web', 'Application.log_request', log_request)
wrap_function_wrapper(
    'tornado.web', 'RequestHandler.log_exception', log_exception)

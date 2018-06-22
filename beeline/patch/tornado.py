''' patches base tornado classes to add honeycomb instrumentation '''

import beeline
import tornado
assert tornado # for pyflakes
from wrapt import wrap_function_wrapper

def log_request(_log_request, instance, args, kwargs):
    try:
        # expecting signature `log_request(self, handler)`
        if len(args) == 1:
            handler = args[0]
            beeline.send_now({
                "request_duration_ms": handler.request.request_time() * 1000.0,
                "method": handler.request.method,
                "uri": handler.request.uri,
                "remote_ip": handler.request.remote_ip,
                "path": handler.request.uri,
                "query": handler.request.query,
                "http_status": handler.get_status(),
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
                "method": instance.request.method,
                "uri": instance.request.uri,
                "remote_ip": instance.request.remote_ip,
                "path": instance.request.uri,
                "query": instance.request.query,
                "exception_type": type(value).__name__,
                "exception_message": str(value),
            })
    except Exception:
        pass
    finally:
        _log_exception(*args, **kwargs)

wrap_function_wrapper('tornado.web', 'Application.log_request', log_request)
wrap_function_wrapper('tornado.web', 'RequestHandler.log_exception', log_exception)

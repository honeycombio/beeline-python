from wrapt import wrap_function_wrapper
import requests
# needed for pyflakes
assert requests
import beeline

def request(_request, instance, args, kwargs):
    try:
        b = beeline.get_beeline()
        if b:
            context = b.tracer_impl.marshal_trace_context()
            if context:
                b.log("requests lib - adding trace context to outbound request: %s", context)
                instance.headers['X-Honeycomb-Trace'] = context
            else:
                b.log("requests lib - no trace context found")
    except Exception:
        pass
    finally:
        return _request(*args, **kwargs)

wrap_function_wrapper('requests.sessions', 'Session.request', request)

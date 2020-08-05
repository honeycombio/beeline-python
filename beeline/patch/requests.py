import beeline
from wrapt import wrap_function_wrapper
import requests
# needed for pyflakes
assert requests


def request(_request, instance, args, kwargs):
    span = beeline.start_span(context={"meta.type": "http_client"})

    b = beeline.get_beeline()
    if b and b.http_trace_propagation_hook is not None:
        new_headers = beeline.http_trace_propagation_hook()
        if new_headers:
            b.log(
                "requests lib - adding trace context to outbound request: %s", new_headers)
            instance.headers.update(new_headers)
        else:
            b.log("requests lib - no trace context found")

    try:
        resp = None
        beeline.add_context({
            "name": "requests_%s" % kwargs.get('method') or args[0],
            "request.method": kwargs.get('method') or args[0],
            "request.url": kwargs.get('url') or args[1],
        })
        resp = _request(*args, **kwargs)
        return resp
    except Exception as e:
        beeline.add_context({
            "request.error_type": str(type(e)),
            "request.error": beeline.internal.stringify_exception(e),
        })
        raise
    finally:
        if resp:
            content_type = resp.headers.get('content-type')
            if content_type:
                beeline.add_context_field(
                    "response.content_type", content_type)
            content_length = resp.headers.get('content-length')
            if content_length:
                beeline.add_context_field(
                    "response.content_length", content_length)
            if hasattr(resp, 'status_code'):
                beeline.add_context_field(
                    "response.status_code", resp.status_code)
        beeline.finish_span(span)


wrap_function_wrapper('requests.sessions', 'Session.request', request)

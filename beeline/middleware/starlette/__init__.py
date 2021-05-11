import beeline
from starlette.exceptions import HTTPException

from starlette.datastructures import Headers


__all__ = ("HoneyMiddleware",)


class HoneyMiddleware:
    """A middleware for using Honeycomb with Starlette.

    To use, add it to the list of middlewares for your application.

    You'll also want to ensure beeline is initialized and cleaned up following
    the lifetime of your application. You can do this with ``on_startup`` and
    ``on_shutdown`` handlers:

    >>> import beeline
    >>> from starlette.applications import Starlette
    >>> from starlette.middleware import Middleware
    >>> async def on_startup():
    ...     beeline.init(...)
    >>> async def on_shutdown():
    ...     beeline.close()
    >>> app = Starlette(
    ...     middleware=[Middleware(HoneyMiddleware)],
    ...     on_startup=[on_startup],
    ...     on_shutdown=[on_shutdown],
    ... )
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Don't trace non http/websocket types
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        status_code = None

        async def wrapper(response):
            nonlocal status_code
            if response["type"] == "http.response.start":
                status_code = response["status"]
            return await send(response)

        trace = beeline.start_trace(context=self.get_context(scope))
        try:
            await self.app(scope, receive, wrapper)
        except HTTPException as exc:
            status_code = exc.status_code
            raise
        except Exception:
            status_code = 500
            raise
        finally:
            trace.add_context_field(
                "response.status_code", status_code
            )
            beeline.finish_trace(trace)

    def get_context(self, scope):
        """Get a trace context from the current scope"""
        request_method = scope.get('method')
        if request_method:
            trace_name = "starlette_http_{}".format(request_method.lower())
        else:
            trace_name = "starlette_http"

        headers = Headers(scope=scope)

        return {
            "name": trace_name,
            "type": "http_server",
            "request.host": headers.get('host'),
            "request.method": request_method,
            "request.path": scope.get('path'),
            "request.content_length": int(headers.get('content-length', 0)),
            "request.user_agent": headers.get('user-agent'),
            "request.scheme": scope.get('scheme'),
            "request.query": scope.get('query_string').decode("ascii")
        }

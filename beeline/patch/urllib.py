from wrapt import wrap_function_wrapper
import beeline
import urllib.request

def _urllibopen(_urlopen, instance, args, kwargs):
    # urlopen accepts either a string URL or a Request object as its first arg
    # It's easier to process the info contained in the request and modify it
    # by converting the URL string into a Request
    if type(args[0]) != urllib.request.Request:
        args[0] = urllib.request.Request(args[0])
    
    span = beeline.start_span(context={"meta.type": "http_client"})
    
    b = beeline.get_beeline()
    if b:
        context = b.tracer_impl.marshal_trace_context()
        if context:
            b.log("urllib lib - adding trace context to outbound request: %s", context)
            args[0].headers['X-Honeycomb-Trace'] = context
        else:
            b.log("urllib lib - no trace context found")
    
    try:
        resp = None
        beeline.add_context({
            "name": "urllib_%s" % args[0].get_method(),
            "request.method": args[0].get_method(),
            "request.uri": args[0].full_url
        })
        resp = _urlopen(*args, **kwargs)
        return resp
    except Exception as e:
        beeline.add_context({
            "request.error_type": str(type(e)),
            "request.error": beeline.internal.stringify_exception(e),
        })
        raise
    finally:
        if resp:
            beeline.add_context_field("response.status_code", resp.status)
            content_type = resp.getheader('content-type')
            if content_type:
                beeline.add_context_field("response.content_type", content_type)
            content_length = resp.getheader('content-length')
            if content_length:
                beeline.add_context_field("response.content_length", content_length)
            
        beeline.finish_span(span)

# Note that this only patches urllib.request.urlopen, not
# http.client.HTTPConnection.  The latter is a lot more of a pain to figure
# out what, exactly, the lifetime of the span ought to be -- but most people
# who plan to block and do nothing else use urlopen, anyway.
wrap_function_wrapper('urllib.request', 'urlopen', _urllibopen)

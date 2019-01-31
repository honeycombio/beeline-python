import beeline
from beeline.trace import unmarshal_trace_context

# In Lambda, a cold start is when Lambda has to spin up a new instance of a
# function to satisfy a request, rather than re-use an existing instance.
# This usually has a non-trivial effect on latency for the request and is
# worth instrumenting.
COLD_START = True

def _get_trace_data(event):
    ''' Extract trace/parent ids and context object that are threaded through
    in various ways from other beelines'''
    trace_id, parent_id, context = None, None, None

    # If API gateway is triggering the Lambda, the event will have headers
    # and we can look for our trace headers
    if isinstance(event, dict):
        if 'headers' in event:
            if isinstance(event['headers'], dict):
                # deal with possible case issues
                keymap = {k.lower(): k  for k in event['headers'].keys()}
                if 'x-honeycomb-trace' in keymap:
                    trace_id, parent_id, context = unmarshal_trace_context(
                        event['headers'][keymap['x-honeycomb-trace']]
                    )

    return trace_id, parent_id, context

def beeline_wrapper(handler):
    ''' Honeycomb Beeline decorator for Lambda functions. Expects a handler
    function with the signature:

    `def handler(event, context)`

    Example use:

    ```
    @beeline_wrapper
    def my_handler(event, context):
        # ...
    ```

    '''

    def _beeline_wrapper(event, context):
        global COLD_START

        # don't blow up the world if the beeline has not been initialized
        if not beeline.get_beeline():
            return handler(event, context)

        try:
            # assume we're going to get bad values sometimes in our headers
            trace_id, parent_id, trace_context = None, None, None
            try:
                trace_id, parent_id, trace_context = _get_trace_data(event)
            except Exception as e:
                beeline.internal.log('error attempting to extract trace context: %s', beeline.internal.stringify_exception(e))
                pass
            with beeline.tracer(name=handler.__name__,
                    trace_id=trace_id, parent_id=parent_id):
                beeline.add_context({
                    "app.function_name": context.function_name,
                    "app.function_version": context.function_version,
                    "app.request_id": context.aws_request_id,
                    "app.event": event,
                    "meta.cold_start": COLD_START,
                })

                # if there is custom context attached from upstream, add that now
                if isinstance(trace_context, dict):
                    for k, v in trace_context.items():
                        beeline.add_trace_field(k, v)

                resp = handler(event, context)

                if resp is not None:
                    beeline.add_context_field('app.response', resp)

                return resp
        finally:
            # This remains false for the lifetime of the module
            COLD_START = False
            # we have to flush events before the lambda returns
            beeline.get_beeline().client.flush()

    return _beeline_wrapper
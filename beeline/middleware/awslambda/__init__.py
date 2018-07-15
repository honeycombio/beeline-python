import beeline

def _get_trace_ids(event):
    ''' Extract trace/parent ids that are threaded through in various ways '''
    trace_id, parent_id = None, None

    # If API gateway is triggering the Lambda, the event will have headers
    # and we can look for our trace headers
    if isinstance(event, dict):
        if 'headers' in event:
            if isinstance(event['headers'], dict):
                # deal with possible case issues
                keymap = {k.lower(): k  for k in event['headers'].keys()}
                if 'x-honeycomb-trace-id' in keymap:
                    trace_id = event['headers'][keymap['x-honeycomb-trace-id']]
                if 'x-honeycomb-parent-id' in keymap:
                    parent_id = event['headers'][keymap['x-honeycomb-parent-id']]

    return trace_id, parent_id

def wrap(handler, event, context):
    # don't blow up the world if the beeline has not been initialized
    if not beeline.g_client or not beeline.g_tracer:
        return handler(event, context)

    try:
        # if we've passed a trace id from a previous lambda, it will
        # be here
        trace_id, parent_id = _get_trace_ids(event)
        with beeline.g_tracer(name=handler.__name__,
                trace_id=trace_id, parent_id=parent_id):
            beeline.add({
                "app.function_name": context.function_name,
                "app.function_version": context.function_version,
                "app.request_id": context.aws_request_id,
                "app.event": event,
            })
            resp = handler(event, context)

            if resp is not None:
                beeline.add_field('app.response', resp)

            return resp
    finally:
        # we have to flush events before the lambda returns
        beeline.g_client.flush()

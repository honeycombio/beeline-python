
import base64
import json


def http_trace_parser_hook(headers):
    '''
    Retrieves the honeycomb trace context out of the headers.
    headers must implement the beeline.propagation.Headers abstract base class
    '''
    trace_header = headers.Get('X-Honeycomb-Trace')
    if trace_header:
        try:
            trace_id, parent_id, context = unmarshal_propagation_context(
                trace_header)
            return PropagationContext(trace_id, parent_id, context)
        except Exception as e:
            beeline.internal.log(
                'error attempting to extract trace context: %s', beeline.internal.stringify_exception(e))
    return None


def http_trace_propagation_hook(propagation_context):
    '''
    Given a propagation context, returns a dictionary of key value pairs that should be
    added to outbound requests (usually HTTP headers)
    '''
    return {"X-Honeycomb-Trace": marshal_propagation_context(propagation_context)}


def marshal_propagation_context(propagation_context):
    '''
    Given a propagation context, returns the contents of a trace header to be
    injected by middleware.
    '''
    # FIXME: Since ALL trace fields are in propagation_context, we may want to strip
    # some automatically added trace fields that we DON'T want to propagate - e.g. request.*
    version = 1
    trace_fields = base64.b64encode(json.dumps(
        propagation_context.trace_fields).encode()).decode()
    trace_header = "{};trace_id={},parent_id={},context={}".format(
        version, propagation_context.trace_id, propagation_context.parent_id, trace_fields
    )

    return trace_header


def unmarshal_propagation_context(trace_header):
    # the first value is the trace payload version
    # at this time there is only one version, but we should warn
    # if another version comes through
    version, data = trace_header.split(';', 1)
    if version != "1":
        log('warning: trace_header version %s is unsupported', version)
        return None, None, None

    kv_pairs = data.split(',')

    trace_id, parent_id, context = None, None, None
    # Some beelines send "dataset" but we do not handle that yet
    for pair in kv_pairs:
        k, v = pair.split('=', 1)
        if k == 'trace_id':
            trace_id = v
        elif k == 'parent_id':
            parent_id = v
        elif k == 'context':
            context = json.loads(base64.b64decode(v.encode()).decode())

    # context should be a dict
    if context is None:
        context = {}

    return trace_id, parent_id, context

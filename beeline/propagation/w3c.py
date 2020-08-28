import beeline
from beeline.propagation import PropagationContext
import re

# Cribbed from OpenTelemetry python implementation.
_TRACEPARENT_HEADER_FORMAT = (
    "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
    + "(-.*)?[ \t]*$"
)
_TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
_EMPTY_TRACE_ID = "0" * 32
_EMPTY_PARENT_ID = "0" * 16


def http_trace_parser_hook(request):
    '''
    Retrieves the w3c propagation context out of the request.
    request must implement the beeline.propagation.Request abstract base class
    '''
    traceparent_header = request.header('traceparent')
    if not traceparent_header:
        return None
    tracestate_header = request.header('tracestate')

    trace_id = None
    parent_id = None
    try:
        trace_id, parent_id, trace_flags = unmarshal_traceparent(
            traceparent_header)
        tracestate = unmarshal_tracestate(tracestate_header)
        trace_fields = {}
        trace_fields['traceflags'] = trace_flags
        trace_fields['tracestate'] = tracestate
        return PropagationContext(trace_id, parent_id, trace_fields)
    except Exception as e:
        beeline.internal.log(
            'error attempting to extract w3c trace: %s', beeline.internal.stringify_exception(e))
    return None


def http_trace_propagation_hook(propagation_context):
    '''
    Given a propagation context, returns a dictionary of key value pairs that should be
    added to outbound requests (usually HTTP headers)
    '''
    if not propagation_context:
        return None

    traceparent_header = marshal_traceparent(propagation_context)
    if not traceparent_header:
        return {}

    headers = {}
    headers["traceparent"] = traceparent_header

    tracestate_header = marshal_tracestate(propagation_context)

    if tracestate_header:
        headers['tracestate'] = tracestate_header
    return headers


def marshal_traceparent(propagation_context):
    '''
    Given a propagation context, returns the contents of a trace header to be
    injected by middleware.
    '''
    if not propagation_context:
        return None

    trace_flags = propagation_context.trace_fields.get('traceflags')
    if not trace_flags:
        trace_flags = "00"

    traceparent_header = "00-{}-{}-{}".format(
        propagation_context.trace_id,
        propagation_context.parent_id,
        trace_flags,
    )

    return traceparent_header


def marshal_tracestate(propagation_context):
    '''
    '''
    if not propagation_context:
        return None

    tracestate_header = propagation_context.trace_fields.get('tracestate')
    return tracestate_header


def unmarshal_traceparent(header):
    match = re.search(_TRACEPARENT_HEADER_FORMAT_RE, header)
    if not match:
        # Raise exception?
        return None
    version = match.group(1)
    trace_id = match.group(2)
    parent_id = match.group(3)
    trace_flags = match.group(4)

    if trace_id == _EMPTY_TRACE_ID or parent_id == _EMPTY_PARENT_ID:
        return None

    if version == "00":
        if match.group(5):
            return None
    if version == "ff":
        return None

    return trace_id, parent_id, trace_flags


def unmarshal_tracestate(header):
    # We treat the tracestate header as an opaque blob, and don't parse it at all.
    return header

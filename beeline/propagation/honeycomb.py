import beeline
from beeline.propagation import PropagationContext
import base64
import json
from urllib.parse import quote, unquote


def http_trace_parser_hook(request):
    '''
    Retrieves the honeycomb propagation context out of the request.
    request must implement the beeline.propagation.Request abstract base class
    '''
    trace_header = request.header('X-Honeycomb-Trace')
    if trace_header:
        try:
            trace_id, parent_id, context, dataset = unmarshal_propagation_context_with_dataset(
                trace_header)
            return PropagationContext(trace_id, parent_id, context, dataset)
        except Exception as e:
            beeline.internal.log(
                'error attempting to extract trace context: %s', beeline.internal.stringify_exception(e))
    return None


def http_trace_propagation_hook(propagation_context):
    '''
    Given a propagation context, returns a dictionary of key value pairs that should be
    added to outbound requests (usually HTTP headers)
    '''
    if not propagation_context:
        return None

    return {"X-Honeycomb-Trace": marshal_propagation_context(propagation_context)}


def marshal_propagation_context(propagation_context):
    '''
    Given a propagation context, returns the contents of a trace header to be
    injected by middleware.
    '''
    if not propagation_context:
        return None

    # FIXME: Since ALL trace fields are in propagation_context, we may want to strip
    # some automatically added trace fields that we DON'T want to propagate - e.g. request.*
    version = 1
    trace_fields = base64.b64encode(json.dumps(
        propagation_context.trace_fields).encode()).decode()

    components = [f"trace_id={propagation_context.trace_id}",
                  f"parent_id={propagation_context.parent_id}",
                  f"context={trace_fields}"]

    if beeline.propagation.propagate_dataset and propagation_context.dataset:
        components.insert(0, f"dataset={quote(propagation_context.dataset)}")

    join_components = ",".join(components)
    trace_header = f"{version};{join_components}"

    return trace_header


def unmarshal_propagation_context(trace_header):
    """
    Deprecated: Use beeline.propagation.honeycomb.unmarshal_propagation_context_with_dataset instead
    """
    trace_id, parent_id, context, _dataset = unmarshal_propagation_context_with_dataset(trace_header)

    return trace_id, parent_id, context


def unmarshal_propagation_context_with_dataset(trace_header):
    '''
    Given the body of the `X-Honeycomb-Trace` header, returns the trace_id,
    parent_id, "context" and dataset.
    '''
    # the first value is the trace payload version
    # at this time there is only one version, but we should warn
    # if another version comes through
    version, data = trace_header.split(';', 1)
    if version != "1":
        beeline.internal.log(
            'warning: trace_header version %s is unsupported', version)
        return None, None, None, None

    kv_pairs = data.split(',')

    trace_id, parent_id, context, dataset = None, None, None, None
    # Some beelines send "dataset" but we do not handle that yet
    for pair in kv_pairs:
        k, v = pair.split('=', 1)
        if k == 'trace_id':
            trace_id = v
        elif k == 'parent_id':
            parent_id = v
        elif k == 'context':
            context = json.loads(base64.b64decode(v.encode()).decode())
        elif k == 'dataset' and beeline.propagation.propagate_dataset:
            dataset = unquote(v)

    # context should be a dict
    if context is None:
        context = {}

    return trace_id, parent_id, context, dataset

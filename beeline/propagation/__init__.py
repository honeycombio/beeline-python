import abc
import beeline
import base64
import json


class PropagationContext(object):
    def __init__(self, trace_id, parent_id, trace_fields):
        # FIXME: Better name for context
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.trace_fields = trace_fields

    def mergeContext(self, context):
        """
        Given a context, merge the trace_fields into the context. If a field is in both,
        always use the field from the incoming context. Return the new context.
        """
        return self.trace_fields.copy().update(context)


class PropagationHeaders(object):
    @abc.abstractmethod
    def Get(self, key):
        """
        Get the value associated with the specified key, transformed as necessary for the
        transport and middleware.
        """
        return


def honeycomb_http_trace_parser_hook(headers):
    '''
    Retrieves the honeycomb trace context out of the headers.
    headers must implement the beeline.propagation.Headers abstract base class
    '''
    trace_context = headers.Get('X-Honeycomb-Trace')
    if trace_context:
        try:
            trace_id, parent_id, context = honeycomb_unmarshal_trace_header(
                trace_context)
            return PropagationContext(trace_id, parent_id, context)
        except Exception as e:
            beeline.internal.log(
                'error attempting to extract trace context: %s', beeline.internal.stringify_exception(e))
    return None


def honeycomb_http_trace_propagation_hook(propagation_context):
    '''
    Given a propagation context, returns a dictionary of key value pairs that should be
    added to outbound requests (usually HTTP headers)
    '''
    print("honeycomb_http_trace_propagation_hook")
    return {"X-Honeycomb-Trace": honeycomb_marshal_trace_context(propagation_context)}


def honeycomb_marshal_trace_context(propagation_context):
    '''
    Given a propagation context, returns the contents of a trace header to be
    injected by middleware.
    '''
    # FIXME: Since ALL trace fields are in propagation_context, we may want to strip
    # some automatically added trace fields that we DON'T want to propagate - e.g. request.*
    version = 1
    trace_fields = base64.b64encode(json.dumps(
        propagation_context.trace_fields).encode()).decode()
    trace_context = "{};trace_id={},parent_id={},context={}".format(
        version, propagation_context.trace_id, propagation_context.parent_id, trace_fields
    )

    return trace_context


def honeycomb_unmarshal_trace_context(trace_header):
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

from beeline.propagation import honeycomb, w3c


def http_trace_parser_hook(request):
    """
    Retrieves the propagation context out of the request. Uses the honeycomb header, with W3C header as fallback.
    """
    honeycomb_header_value = honeycomb.http_trace_parser_hook(request)
    w3c_header_value = w3c.http_trace_parser_hook(request)
    if honeycomb_header_value:
        return honeycomb_header_value
    else:
        return w3c_header_value


def http_trace_propagation_hook(propagation_context):
    """
    Given a propagation context, returns a dictionary of key value pairs that should be
    added to outbound requests (usually HTTP headers). Uses the honeycomb format.
    """
    return honeycomb.http_trace_propagation_hook(propagation_context)

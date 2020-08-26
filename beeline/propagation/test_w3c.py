import unittest
from beeline.propagation import DictRequest, PropagationContext
import beeline.propagation.honeycomb as hc
import beeline.propagation.w3c as w3c

traceparent_header = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-00"
tracestate_header = "foo=bar,bar=baz"

headers = {
    "traceparent": traceparent_header,
    "tracestate": tracestate_header
}
trace_id = "0af7651916cd43dd8448eb211c80319c"
parent_id = "b7ad6b7169203331"
trace_flags = "00"
tracestate = "foo=bar,bar=baz"


class TestW3CMarshalUnmarshal(unittest.TestCase):
    def test_roundtrip(self):
        '''Verify that we can successfully roundtrip (marshal and unmarshal)'''
        trace_fields = {"traceflags": trace_flags,
                        "tracestate": tracestate}

        pc = PropagationContext(trace_id, parent_id, trace_fields)

        traceparent_header = w3c.marshal_traceparent(pc)
        self.assertEquals(traceparent_header, traceparent_header)

        tracestate_header = w3c.marshal_tracestate(pc)
        self.assertEquals(tracestate_header, tracestate_header)

        new_trace_id, new_parent_id, new_trace_flags = w3c.unmarshal_traceparent(
            traceparent_header)
        self.assertEquals(trace_id, new_trace_id)
        self.assertEquals(parent_id, new_parent_id)
        self.assertEquals(trace_flags, new_trace_flags)

        new_tracestate = w3c.unmarshal_tracestate(tracestate_header)
        self.assertEquals(tracestate, new_tracestate)


class TestW3CHTTPTraceParserHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses honeycomb trace headers'''
        req = DictRequest(headers)
        pc = w3c.http_trace_parser_hook(req)
        self.assertEquals(pc.trace_id, trace_id)
        self.assertEquals(pc.parent_id, parent_id)
        self.assertEquals(pc.trace_fields, {
            "tracestate": tracestate,
            "traceflags": trace_flags
        })

    def test_no_header(self):
        req = DictRequest({})
        pc = w3c.http_trace_parser_hook(req)
        self.assertIsNone(pc)


class TestW3CHTTPTracePropagationHook(unittest.TestCase):
    def test_generates_correct_headers(self):
        pc = PropagationContext(
            trace_id, parent_id, {"traceflags": trace_flags,
                                  "tracestate": tracestate}
        )
        headers = w3c.http_trace_propagation_hook(pc)
        self.assertIn('traceparent', headers)
        self.assertIn('tracestate', headers)
        self.assertEquals(headers['traceparent'],
                          traceparent_header)
        self.assertEquals(headers['tracestate'],
                          tracestate_header)

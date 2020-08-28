import unittest
from beeline.propagation import DictRequest, PropagationContext
import beeline.propagation.honeycomb as hc
import beeline.propagation.w3c as w3c

_TEST_TRACEPARENT_HEADER = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-00"
_TEST_TRACESTATE_HEADER = "foo=bar,bar=baz"

_TEST_HEADERS = {
    "traceparent": _TEST_TRACEPARENT_HEADER,
    "tracestate": _TEST_TRACESTATE_HEADER
}
_TEST_TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
_TEST_PARENT_ID = "b7ad6b7169203331"
_TEST_TRACE_FLAGS = "00"
_TEST_TRACESTATE = "foo=bar,bar=baz"


class TestW3CMarshalUnmarshal(unittest.TestCase):
    def test_roundtrip(self):
        '''Verify that we can successfully roundtrip (marshal and unmarshal)'''
        trace_fields = {"traceflags": _TEST_TRACE_FLAGS,
                        "tracestate": _TEST_TRACESTATE}

        pc = PropagationContext(_TEST_TRACE_ID, _TEST_PARENT_ID, trace_fields)

        traceparent_header = w3c.marshal_traceparent(pc)
        tracestate_header = w3c.marshal_tracestate(pc)

        # Make sure marshalled headers are as we expect.
        self.assertEquals(_TEST_TRACEPARENT_HEADER, traceparent_header)
        self.assertEquals(_TEST_TRACESTATE_HEADER, tracestate_header)

        new_trace_id, new_parent_id, new_trace_flags = w3c.unmarshal_traceparent(
            traceparent_header)
        new_tracestate = w3c.unmarshal_tracestate(tracestate_header)

        # Check round-trip values are the same as start values.
        self.assertEquals(_TEST_TRACE_ID, new_trace_id)
        self.assertEquals(_TEST_PARENT_ID, new_parent_id)
        self.assertEquals(_TEST_TRACE_FLAGS, new_trace_flags)
        self.assertEquals(_TEST_TRACESTATE, new_tracestate)


class TestW3CHTTPTraceParserHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses W3C trace headers'''
        req = DictRequest(_TEST_HEADERS)
        pc = w3c.http_trace_parser_hook(req)
        self.assertEquals(pc.trace_id, _TEST_TRACE_ID)
        self.assertEquals(pc.parent_id, _TEST_PARENT_ID)
        self.assertEquals(pc.trace_fields, {
            "tracestate": _TEST_TRACESTATE,
            "traceflags": _TEST_TRACE_FLAGS
        })

    def test_no_header(self):
        req = DictRequest({})
        pc = w3c.http_trace_parser_hook(req)
        self.assertIsNone(pc)


class TestW3CHTTPTracePropagationHook(unittest.TestCase):
    def test_generates_correct_headers(self):
        pc = PropagationContext(
            _TEST_TRACE_ID, _TEST_PARENT_ID, {"traceflags": _TEST_TRACE_FLAGS,
                                              "tracestate": _TEST_TRACESTATE}
        )
        headers = w3c.http_trace_propagation_hook(pc)
        self.assertIn('traceparent', headers)
        self.assertIn('tracestate', headers)
        self.assertEquals(headers['traceparent'],
                          _TEST_TRACEPARENT_HEADER)
        self.assertEquals(headers['tracestate'],
                          _TEST_TRACESTATE_HEADER)

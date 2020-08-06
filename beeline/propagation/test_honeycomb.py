import unittest
from beeline.propagation import DictRequest, PropagationContext
import beeline.propagation.honeycomb

header_value = '1;trace_id=bloop,parent_id=scoop,context=e30K'


class TestMarshalUnmarshal(unittest.TestCase):
    def test_roundtrip(self):
        '''Verify that we can successfully roundtrip (marshal and unmarshal)'''
        trace_id = "bloop"
        parent_id = "scoop"
        trace_fields = {"key": "value"}
        pc = PropagationContext(trace_id, parent_id, trace_fields)
        header = beeline.propagation.honeycomb.marshal_propagation_context(pc)
        new_trace_id, new_parent_id, new_trace_fields = beeline.propagation.honeycomb.unmarshal_propagation_context(
            header)
        self.assertEquals(trace_id, new_trace_id)
        self.assertEquals(parent_id, new_parent_id)
        self.assertEquals(trace_fields, new_trace_fields)


class TestHoneycombHTTPTraceParserHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses honeycomb trace headers'''
        headers = beeline.propagation.DictRequest({
            # case shouldn't matter
            'X-HoNEyComb-TrACE': header_value,
        })
        pc = beeline.propagation.honeycomb.http_trace_parser_hook(headers)
        self.assertEquals(pc.trace_id, "bloop")
        self.assertEquals(pc.parent_id, "scoop")
        # FIXME: We should have a legitimate header with trace_field and dataset_id set

    def test_no_header(self):
        headers = beeline.propagation.DictRequest({})
        pc = beeline.propagation.honeycomb.http_trace_parser_hook(headers)
        self.assertIsNone(pc)


class TestHoneycombHTTPTracePropagationHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses honeycomb trace headers'''
        pass

    def test_no_header(self):
        # pc = beeline.propagation.honeycomb_http_trace_parser_hook()
        pass

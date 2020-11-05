import unittest
from beeline.propagation import DictRequest, PropagationContext
import beeline.propagation.honeycomb as hc

header_value = '1;trace_id=bloop,parent_id=scoop,context=e30K'


class TestMarshalUnmarshal(unittest.TestCase):
    def test_roundtrip(self):
        '''Verify that we can successfully roundtrip (marshal and unmarshal)'''
        trace_id = "bloop"
        parent_id = "scoop"
        trace_fields = {"key": "value"}
        pc = PropagationContext(trace_id, parent_id, trace_fields)
        header = hc.marshal_propagation_context(pc)
        new_trace_id, new_parent_id, new_trace_fields = hc.unmarshal_propagation_context(
            header)
        self.assertEquals(trace_id, new_trace_id)
        self.assertEquals(parent_id, new_parent_id)
        self.assertEquals(trace_fields, new_trace_fields)

    def test_roundtrip_with_dataset(self):
        '''Verify that we can successfully roundtrip (marshal and unmarshal)'''
        dataset = "blorp blorp"
        trace_id = "bloop"
        parent_id = "scoop"
        trace_fields = {"key": "value"}
        pc = PropagationContext(trace_id, parent_id, trace_fields, dataset)
        header = hc.marshal_propagation_context(pc)
        new_trace_id, new_parent_id, new_trace_fields, new_dataset = hc.unmarshal_propagation_context_with_dataset(
            header)
        self.assertEquals(dataset, new_dataset)
        self.assertEquals(trace_id, new_trace_id)
        self.assertEquals(parent_id, new_parent_id)
        self.assertEquals(trace_fields, new_trace_fields)


class TestHoneycombHTTPTraceParserHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses honeycomb trace headers'''
        req = DictRequest({
            # case shouldn't matter
            'X-HoNEyComb-TrACE': header_value,
        })
        pc = hc.http_trace_parser_hook(req)
        self.assertEquals(pc.trace_id, "bloop")
        self.assertEquals(pc.parent_id, "scoop")
        # FIXME: We should have a legitimate header with trace_field and dataset_id set

    def test_no_header(self):
        req = DictRequest({})
        pc = hc.http_trace_parser_hook(req)
        self.assertIsNone(pc)


class TestHoneycombHTTPTracePropagationHook(unittest.TestCase):
    def test_generates_correct_header(self):
        dataset = "blorp blorp"
        trace_id = "bloop"
        parent_id = "scoop"
        trace_fields = {"key": "value"}
        pc = PropagationContext(
            trace_id, parent_id, trace_fields, dataset)
        headers = hc.http_trace_propagation_hook(pc)
        self.assertIn('X-Honeycomb-Trace', headers)
        self.assertEquals(headers['X-Honeycomb-Trace'],
                          "1;dataset=blorp%20blorp,trace_id=bloop,parent_id=scoop,context=eyJrZXkiOiAidmFsdWUifQ==")

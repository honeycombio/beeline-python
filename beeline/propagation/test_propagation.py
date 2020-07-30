import unittest
import beeline.propagation


class TestPropagationContext(unittest.TestCase):
    def test_merge_context(self):
        '''Test that we properly merge'''


class TestHoneycombHTTPTraceParserHook(unittest.TestCase):
    def test_has_header(self):
        '''Test that the hook properly parses honeycomb trace headers'''
        pass

    def test_no_header(self):
        # pc = beeline.propagation.honeycomb_http_trace_parser_hook()
        pass

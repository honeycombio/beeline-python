import unittest

from beeline.middleware import awslambda

class TestGetTraceIds(unittest.TestCase):
    def test_get_trace_ids_from_header(self):
        ''' test that trace_id and parent_id are extracted regardless of case '''
        event = {
            'headers': {
                # case shouldn't matter
                'X-HoNEyComb-TrACE-id': 'bloop',
                'x-HoNEyComb-PARENT-ID': 'scoop',
            },
        }

        trace_id, parent_id = awslambda._get_trace_ids(event)
        self.assertEqual(trace_id, 'bloop')
        self.assertEqual(parent_id, 'scoop')

    def test_get_trace_ids_no_header(self):
        ''' ensure that we handle events with no header key '''
        event = {
            'foo': 1,
        }

        trace_id, parent_id = awslambda._get_trace_ids(event)
        self.assertIsNone(trace_id)
        self.assertIsNone(parent_id)

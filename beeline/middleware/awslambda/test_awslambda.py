import unittest
from mock import Mock, patch

from beeline.middleware import awslambda

class TestGetTraceIds(unittest.TestCase):
    def test_get_trace_ids_from_header(self):
        ''' test that trace_id and parent_id are extracted regardless of case '''
        event = {
            'headers': {
                # case shouldn't matter
                'X-HoNEyComb-TrACE': '1;trace_id=bloop,parent_id=scoop,context=e30K',
            },
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertEqual(trace_id, 'bloop')
        self.assertEqual(parent_id, 'scoop')
        self.assertEqual(context, {})

    def test_get_trace_ids_no_header(self):
        ''' ensure that we handle events with no header key '''
        event = {
            'foo': 1,
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertIsNone(trace_id)
        self.assertIsNone(parent_id)
        self.assertIsNone(context)

    def test_get_trace_ids_sns_none(self):
        ''' ensure that we handle SNS events with no honeycomb key '''
        event = {
            "Records":
            [
                {
                    "EventSource": "aws:sns",
                    "Sns": {
                        "Message": "Hello from SNS!",
                        "MessageAttributes": {}
                    }
                }
            ],
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertIsNone(trace_id)
        self.assertIsNone(parent_id)
        self.assertIsNone(context)

    def test_get_trace_ids_sns_attribute(self):
        ''' ensure that we extract SNS data from message attributes'''
        event = {
            "Records":
            [
                {
                    "EventSource": "aws:sns",
                    "Sns": {
                        "Message": "Hello from SNS!",
                        "MessageAttributes": {
                            'X-HoNEyComb-TrACE': {
                                "Type": "String",
                                "Value": "1;trace_id=bloop,parent_id=scoop,context=e30K",
                            }
                        }
                    }
                }
            ],
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertEqual(trace_id, 'bloop')
        self.assertEqual(parent_id, 'scoop')
        self.assertEqual(context, {})

    def test_get_trace_ids_sqs_none(self):
        ''' ensure that we handle SQS events with no honeycomb key '''
        event = {
            "Records":
            [
                {
                    "body": "Hello from SQS!",
                    "messageAttributes": {},
                    "eventSource": "aws:sqs",
                },
            ],
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertIsNone(trace_id)
        self.assertIsNone(parent_id)
        self.assertIsNone(context)

    def test_get_trace_ids_sqs_attributes(self):
        ''' ensure that we extract SQS data from message attributes'''
        event = {
            "Records":
            [
                {
                    "body": "Hello from SQS!",
                    "messageAttributes": {
                        'X-HoNEyComb-TrACE': {
                            "Type":"String",
                            "stringValue": "1;trace_id=bloop,parent_id=scoop,context=e30K",
                        },
                        'foo': {
                            "Type": "String",
                            "stringValue": "bar",
                        },
                    },
                    "eventSource": "aws:sqs",
                },
            ],
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertEqual(trace_id, 'bloop')
        self.assertEqual(parent_id, 'scoop')
        self.assertEqual(context, {})

    def test_message_batch_is_ignored(self):
        ''' ensure that we don't process batches'''
        event = {
            "Records":
            [
                {
                    "body": "Hello from SQS!",
                    "messageAttributes": {
                        'X-HoNEyComb-TrACE': {
                            "Type": "String",
                            "stringValue": "1;trace_id=beep,parent_id=moop,context=e29K",
                        },
                        'foo': {
                            "Type": "String",
                            "stringValue": "bar",
                        },
                    },
                    "eventSource": "aws:sqs",
                },
                {
                    "body": "Another hello from SQS!",
                    "messageAttributes": {
                        'X-HoNEyComb-TrACE': {
                            "Type": "String",
                            "stringValue": "1;trace_id=bloop,parent_id=scoop,context=e30K",
                        },
                        'foo': {
                            "Type": "String",
                            "stringValue": "baz",
                        },
                    },
                    "eventSource": "aws:sqs",
                },
            ],
        }

        trace_id, parent_id, context = awslambda._get_trace_data(event)
        self.assertIsNone(trace_id)
        self.assertIsNone(parent_id)
        self.assertIsNone(context)

class TestLambdaWrapper(unittest.TestCase):
    def test_wrapper_works_no_init(self):
        ''' ensure that the wrapper doesn't break anything if used before
        beeline.init is called
        '''
        with patch('beeline.get_beeline') as p:
            p.return_value = None
            @awslambda.beeline_wrapper
            def foo(event, context):
                return 1

            self.assertEqual(foo(None, None), 1)

    def test_basic_instrumentation(self):
        ''' ensure basic event fields get instrumented '''
        with patch('beeline.middleware.awslambda.beeline.add_context') as m_add,\
                patch('beeline.middleware.awslambda.beeline._GBL'),\
                patch('beeline.middleware.awslambda.COLD_START') as m_cold_start:
            m_event = Mock()
            m_context = Mock(function_name='fn', function_version="1.1.1",
                             aws_request_id='12345')

            @awslambda.beeline_wrapper
            def handler(event, context):
                return 1

            self.assertEqual(handler(m_event, m_context), 1)
            m_add.assert_called_once_with({
                "app.function_name": m_context.function_name,
                "app.function_version": m_context.function_version,
                "app.request_id": m_context.aws_request_id,
                "app.event": m_event,
                "meta.cold_start": m_cold_start,
            })

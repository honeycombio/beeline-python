import unittest
from mock import Mock, patch, ANY

from beeline.middleware import awslambda

header_value = '1;trace_id=bloop,parent_id=scoop,context=e30K'


class TestLambdaRequest(unittest.TestCase):
    def test_get_header_from_headers(self):
        '''
        Test that if headers is set, we have case-insensitive match.
        '''
        event = {
            'headers': {
                # case shouldn't matter
                'X-HoNEyComb-TrACE': header_value,
            },
        }

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertEqual(lr.header('X-Honeycomb-Trace'), header_value)

    def test_handle_no_headers(self):
        ''' ensure that we handle events with no header key '''
        event = {
            'foo': 1,
        }

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertIsNone(lr.header('X-Honeycomb-Trace'))

    def test_handle_sns_none(self):
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

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertIsNone(lr.header('X-Honeycomb-Trace'))

    def test_handle_sns_attribute(self):
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
                                "Value": header_value,
                            }
                        }
                    }
                }
            ],
        }

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertEqual(lr.header('X-Honeycomb-Trace'), header_value)

    def test_handle_sqs_none(self):
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

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertIsNone(lr.header('X-Honeycomb-Trace'))

    def test_handle_sqs_attributes(self):
        ''' ensure that we extract SQS data from message attributes'''
        event = {
            "Records":
            [
                {
                    "body": "Hello from SQS!",
                    "messageAttributes": {
                        'X-HoNEyComb-TrACE': {
                            "Type": "String",
                            "stringValue": header_value,
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

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertEqual(lr.header('X-Honeycomb-Trace'), header_value)

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

        lr = awslambda.LambdaRequest(event)
        self.assertIsNotNone(lr)
        self.assertIsNone(lr.header('X-Honeycomb-Trace'))


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
        with patch('beeline.propagate_and_start_trace') as m_propagate,\
                patch('beeline.middleware.awslambda.beeline._GBL'),\
                patch('beeline.middleware.awslambda.COLD_START') as m_cold_start:
            m_event = Mock()
            m_context = Mock(function_name='fn', function_version="1.1.1",
                             aws_request_id='12345')

            @awslambda.beeline_wrapper
            def handler(event, context):
                return 1

            self.assertEqual(handler(m_event, m_context), 1)
            m_propagate.assert_called_once_with({
                'app.function_name': 'fn',
                'app.function_version': '1.1.1',
                'app.request_id': '12345',
                'app.event': ANY,
                'meta.cold_start': ANY,
                'name': 'handler'}, ANY)

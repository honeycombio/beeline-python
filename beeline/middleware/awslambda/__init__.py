import beeline
from beeline.propagation import Request
# In Lambda, a cold start is when Lambda has to spin up a new instance of a
# function to satisfy a request, rather than re-use an existing instance.
# This usually has a non-trivial effect on latency for the request and is
# worth instrumenting.
COLD_START = True


class LambdaRequest(Request):
    '''
    Look for header values in SNS/SQS Message Attributes
    '''

    def __init__(self, event):
        # Look for headers (or equivalents) in common places
        self._type = None
        self._event = event
        if isinstance(event, dict):
            # If API gateway is triggering the Lambda, the event will have headers
            # and we can look for our trace headers
            # https://docs.aws.amazon.com/lambda/latest/dg/with-on-demand-https.html
            if 'headers' in event:
                if isinstance(event['headers'], dict):
                    self._attributes = event['headers']
                    self._type = 'headers'

            # If a message source is triggering the Lambda, the event may have
            # our trace data in the message attributes
            elif 'Records' in event:
                # Only process batches of exactly 1
                #  Higher batch sizes would have multiple messages thus
                #  generating multiple traces and requiring manual instrumentation
                if len(event['Records']) == 1:
                    # If SNS is triggering the Lambda
                    # https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
                    if 'EventSource' in event['Records'][0]:
                        if event['Records'][0]['EventSource'] == 'aws:sns':
                            self._attributes = event['Records'][0]['Sns']['MessageAttributes']
                            self._type = 'sns'
                    # If SQS is triggering the Lambda
                    # https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
                    elif 'eventSource' in event['Records'][0]:
                        if event['Records'][0]['eventSource'] == 'aws:sqs':
                            self._attributes = event['Records'][0]['messageAttributes']
                            self._type = 'sqs'
            if self._type:
                self._keymap = {k.lower(): k for k in self._attributes.keys()}

    def header(self, key):
        if not self._type:
            return None
        lookup_key = key.lower()
        if lookup_key not in self._keymap:
            return None
        lookup_key = self._keymap[lookup_key]
        if self._type == 'headers':
            return self._attributes[lookup_key]
        elif self._type == 'sns':
            return self._attributes[lookup_key]['Value']
        elif self._type == 'sqs':
            return self._attributes[lookup_key]['stringValue']
        return None

    def method(self):
        '''
        For a lambda request, method is an irrelevant parameter.
        '''
        return None

    def scheme(self):
        '''
        For a lambda request, scheme is an irrelevant parameter.
        '''
        return None

    def host(self):
        '''
        For a lambda request, host is an irrelevant parameter.
        '''
        return None

    def path(self):
        '''
        For a lambda request, path is an irrelevant parameter.
        '''
        return None

    def query(self):
        '''
        For a lambda request, query is an irrelevant parameter.
        '''
        return None

    def middleware_request(self):
        return self._event


def beeline_wrapper(handler=None, record_input=True, record_output=True):
    ''' Honeycomb Beeline decorator for Lambda functions. Expects a handler
    function with the signature:

    `def handler(event, context)`

    Example use:

    ```
    @beeline_wrapper
    def my_handler(event, context):
        # ...

    @beeline_wrapper(record_input=False, record_output=False)
    def my_handler_with_large_inputs_and_outputs(event, context):
        # ...
    ```

    '''

    def _beeline_wrapper(event, context):
        global COLD_START

        # don't blow up the world if the beeline has not been initialized
        if not beeline.get_beeline():
            return handler(event, context)

        root_span = None
        try:
            # Create request context
            request_context = {
                "app.function_name": getattr(context, 'function_name', ""),
                "app.function_version": getattr(context, 'function_version', ""),
                "app.request_id": getattr(context, 'aws_request_id', ""),
                "meta.cold_start": COLD_START,
                "name": handler.__name__
            }
            if record_input:
                request_context["app.event"] = event

            lr = LambdaRequest(event)
            root_span = beeline.propagate_and_start_trace(request_context, lr)

            # Actually run the handler
            resp = handler(event, context)

            if resp is not None and record_output:
                beeline.add_context_field('app.response', resp)

            return resp
        finally:
            # This remains false for the lifetime of the module
            COLD_START = False
            beeline.finish_trace(root_span)
            # we have to flush events before the lambda returns
            beeline.get_beeline().client.flush()

    def outer_wrapper(*args, **kwargs):
        return beeline_wrapper(*args, record_input=record_input, record_output=record_output, **kwargs)

    if handler:
        return _beeline_wrapper
    return outer_wrapper

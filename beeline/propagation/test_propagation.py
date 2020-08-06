import unittest
import beeline.propagation

header_value = '1;trace_id=bloop,parent_id=scoop,context=e30K'


class TestDictRequest(unittest.TestCase):
    def test_headers(self):
        '''Test that we correctly deal with case sensitivity'''
        request = beeline.propagation.DictRequest({
            # case shouldn't matter
            'MixedCaseHeader': "value",
            'UPPERCASEHEADER': "value"
        },
            {})
        value = request.header('mixedcaseheader')
        self.assertEqual(value, "value")
        value = request.header('upperCaseHeader')
        self.assertEqual(value, "value")

    def test_request_props(self):
        '''Test we correctly return request props'''
        request = beeline.propagation.DictRequest({
            # case shouldn't matter
            'MixedCaseHeader': "value",
            'UPPERCASEHEADER': "value"
        },
            {
                'method': "GET",
                'scheme': "http",
                'host': "api.honeycomb.io",
                'path': "/1/event",
                'query': "key=value"
        })

        self.assertEqual(request.method(), "GET")
        self.assertEqual(request.scheme(), "http")
        self.assertEqual(request.host(), "api.honeycomb.io")
        self.assertEqual(request.path(), "/1/event")
        self.assertEqual(request.query(), "key=value")

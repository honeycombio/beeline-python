import unittest

from beeline.internal import stringify_exception


class TestInternal(unittest.TestCase):
    def test_stringify_exception(self):
        '''ensure we don't crash handling utf-8 exceptions'''
        e = Exception("foo")
        self.assertEqual('foo', stringify_exception(e))

        e = Exception("\u1024abcdef")
        self.assertEqual('\u1024abcdef', stringify_exception(e))

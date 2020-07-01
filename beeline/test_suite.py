from __future__ import absolute_import
import unittest
import unittest.loader
import sys


def get_test_suite():
    """Return the set of tests suitable for the current Python version"""
    # FIXME: Automatically discover tests and strip out async

    test_suite = unittest.defaultTestLoader.discover(".")

    filtered_test_suite = unittest.TestSuite()
    for test_group in test_suite:
        ts = unittest.TestSuite()
        for inner_test_group in test_group:
            # Skip the async tests which fail to import on old versions of python
            if inner_test_group.__class__.__name__ == "ModuleImportFailure" and inner_test_group._testMethodName == "beeline.test_async":
                print(
                    "Skipping beeline.test_async module tests due to old Python version")
            else:
                ts.addTest(inner_test_group)
        filtered_test_suite.addTest(ts)

    return filtered_test_suite


def run_tests():
    runner = unittest.TextTestRunner()
    return runner.run(get_test_suite())


if __name__ == "__main__":
    result = run_tests()
    sys.exit(not result.wasSuccessful())

from unittest import defaultTestLoader

try:
    # The async functionality uses the contextvars module, added in
    # Python 3.7
    import contextvars
except ImportError:
    contextvars = None


def get_test_suite():
    """Return the set of tests suitable for the current Python version"""
    test_suite = defaultTestLoader.loadTestsFromNames(
        ("beeline.test_beeline", "beeline.test_internal", "beeline.test_trace")
    )
    if contextvars:
        async_suite = defaultTestLoader.loadTestsFromName("beeline.test_async")
        test_suite.addTest(async_suite)

    return test_suite

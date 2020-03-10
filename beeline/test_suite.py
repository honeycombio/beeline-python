from __future__ import absolute_import
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
        ("beeline.test_beeline",
         "beeline.test_internal",
         "beeline.test_trace",
         "beeline.patch.test_jinja2",
         "beeline.patch.test_requests",
         "beeline.patch.test_urllib",
         "beeline.middleware.awslambda.test_awslambda",
         "beeline.middleware.django.test_django",
         "beeline.middleware.bottle.test_bottle",
         "beeline.middleware.flask.test_flask",
         "beeline.middleware.werkzeug.test_werkzeug",
        )
    )
    if contextvars:
        async_suite = defaultTestLoader.loadTestsFromName("beeline.test_async")
        test_suite.addTest(async_suite)

    return test_suite

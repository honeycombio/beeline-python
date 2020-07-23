# Honeycomb Beeline for Python

[![Build Status](https://circleci.com/gh/honeycombio/beeline-python.svg?style=svg)](https://app.circleci.com/pipelines/github/honeycombio/beeline-python)

This package makes it easy to instrument your Python web application to send useful events to [Honeycomb](https://honeycomb.io), a service for debugging your software in production.

- [Usage and Examples](https://docs.honeycomb.io/getting-data-in/beelines/beeline-python/)
- [API Reference](https://honeycombio.github.io/beeline-python/)

## Compatible with

Currently supports Django (>1.10), Flask, Bottle, and Tornado.

Compatible with both Python 2.7 and Python 3.

## Get in touch

Please reach out to [support@honeycomb.io](mailto:support@honeycomb.io) or ping
us with the chat bubble on [our website](https://www.honeycomb.io) for any
assistance. We also welcome [bug reports](https://github.com/honeycombio/beeline-python/issues).

## Contributions

Features, bug fixes and other changes to `beeline-python` are gladly accepted. Please
open issues or a pull request with your change. Remember to add your name to the
CONTRIBUTORS file!

If you add a new test module, be sure and update `beeline.test_suite` to pick up the new tests.

All contributions will be released under the Apache License 2.0.

## Releases

You may need to install the `bump2version` utility by running `pip install bump2version`.

To update the version number, do

```
bump2version [major|minor|patch|release|build]
```

If you want to release the version publicly, you will need to manually create a tag `v<x.y.z>` and push it in order to
cause CircleCI to automatically push builds to github releases and PyPI.

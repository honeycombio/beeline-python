# Honeycomb Beeline for Python

[![OSS Lifecycle](https://img.shields.io/osslifecycle/honeycombio/beeline-python?color=pink)](https://github.com/honeycombio/home/blob/main/honeycomb-oss-lifecycle-and-practices.md)
[![Build Status](https://circleci.com/gh/honeycombio/beeline-python.svg?style=svg)](https://app.circleci.com/pipelines/github/honeycombio/beeline-python)

⚠️**STATUS**: This project is being Sunset. See [this issue](https://github.com/honeycombio/beeline-python/issues/302) for more details.

⚠️**Note**: Beelines are Honeycomb's legacy instrumentation libraries. We embrace OpenTelemetry as the effective way to instrument applications. For any new observability efforts, we recommend [instrumenting with OpenTelemetry](https://docs.honeycomb.io/send-data/python/opentelemetry-sdk/).

This package makes it easy to instrument your Python web application to send useful events to [Honeycomb](https://honeycomb.io), a service for debugging your software in production.

- [Usage and Examples](https://docs.honeycomb.io/getting-data-in/beelines/beeline-python/)
- [API Reference](https://honeycombio.github.io/beeline-python/)

## Compatible with

Currently, supports Django (>3.2), Flask(<2.4), Bottle, and Tornado.

Compatible with Python >3.7.

## Updating to 3.3.0

Version 3.3.0 added support for Environment & Services, which changes sending behavior based on API Key.

If you are using the [FileTransmission](https://github.com/honeycombio/libhoney-py/blob/main/libhoney/transmission.py#L448) method and setting a false API key - and still working in Classic mode - you must update the key to be 32 characters in length to keep the same behavior.

## Contributions

Features, bug fixes and other changes to `beeline-python` are gladly accepted.

If you add a new test module, be sure and update `beeline.test_suite` to pick up the new tests.

All contributions will be released under the Apache License 2.0.

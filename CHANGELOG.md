# beeline-python changelog
## 3.5.0 2022-09-09

⚠️  Minimum supported Python version is now 3.7 ⚠️ 
### Maintenance

- Drop Python 3.5, 3.6 Support (#233) | [@emilyashley](https://github.com/emilyashley)
- Bump minimum libhoney version to 2.3 (for python >=3.7)(#234) | [@emilyashley](https://github.com/emilyashley)

## 3.4.2 2022-09-06

### Fixes

- Django < 2.2 does not have request.headers (#231) | [@vreynolds](https://github.com/vreynolds)

## 3.4.1 2022-07-15

### Maintenance

- drop unnecessary backwards compatibility (remove six) (#228) | [@robbkidd](https://github.com/robbkidd)
- Bump minimum libhoney from 1.7.0 to 2.1.1 (#226) | [@danvendia](https://github.com/danvendia)
- Bump wrapt from 1.14.0 to 1.14.1 (#224) | [dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/configuring-dependabot-security-updates)

## 3.4.0 2022-05-04

### Enhancements

- Add meta.span_type to root/subroot spans (#219) | [@MikeGoldsmith](https://github.com/MikeGoldsmith)

### Maintenance

- docs: using FileTransmission with classic requires 32 character key (#220) | [@JamieDanielson](https://github.com/JamieDanielson)
- Bump django from 2.2.27 to 2.2.28 (#217)
- Bump libhoney from 2.0.0 to 2.1.0 (#221)

## 3.3.1 2022-04-12

### Maintenance

- Bump libhoney from 1.11.2 to 2.0.0 (#209)
- Bump wrapt from 1.13.3 to 1.14.0 (#215)
- Bump django from 2.2.26 to 2.2.27 (#210)

## 3.3.0 2022-03-21

### Enhancements

**NOTE** If you are using the [FileTransmission](https://github.com/honeycombio/libhoney-py/blob/main/libhoney/transmission.py#L448) method and setting a false API key - and still working in Classic mode - you must update the key to be 32 characters in length to keep the same behavior.

- feat: Add Environment & Services support (#213) | [@JamieDanielson](https://github.com/JamieDanielson)

## 3.2.0 2022-02-10

### Enhancements

- add rollup SQL duration time to Django traces (#207) | [@jmhodges-color](https://github.com/jmhodges-color)

## 3.1.0 2022-01-20

### Improvements

- add a count of SQL queries to root span in django (#205) | [@jmhodges](https://github.com/jmhodges)

## 3.0.0 2022-01-13

### !!! Breaking Changes !!!

Minimum supported Python version is now 3.5

### Maintenance

- drop python < 3.5 support, update vulnerable deps (#202) | | [@vreynolds](https://github.com/vreynolds)
- gh: add re-triage workflow (#201) | | [@vreynolds](https://github.com/vreynolds)

## 2.18.0 2021-12-23

### Improvements

- accept both w3c and honeycomb propagation headers by default (#199) | [@vreynolds](https://github.com/vreynolds)

## 2.17.3 2021-12-01

### Fixes

- Remove condition on status code (#191) | [@JamieDanielson](https://github.com/JamieDanielson)
- Close trace regardless of exception (#190) | [@vreynolds](https://github.com/vreynolds)

### Maintenance

- Update dependabot to monthly (#194) | [@vreynolds](https://github.com/vreynolds)
- Add python 3.9 and 3.10 to test matrix (#192) | [@vreynolds](https://github.com/vreynolds)
- Add example app using Flask (#189) | [@JamieDanielson](https://github.com/JamieDanielson)
- Empower apply-labels action to apply labels (#187) | [robbkidd](https://github.com/robbkidd)

## 2.17.2 2021-10-19

### Fixes

- Always return True for sampling when sample rate is 1 (#185) | [@MikeGoldsmith](https://github.com/MikeGoldsmith)

### Maintenance

- Change maintenance badge to maintained (#182) | [@JamieDanielson](https://github.com/JamieDanielson)
- Add Stalebot (#183) | [@JamieDanielson](https://github.com/JamieDanielson)

## 2.17.1 2021-09-01

### Fixes:

- Fix stringifying tuple parameters in flask DB middleware (#177) [@anselm-helbig](https://github.com/anselm-helbig) & [@mnemonikk](https://github.com/mnemonikk)

## 2.17.0 2021-05-28

## Improvements:

- Added support for Django streaming responses (#166)

## Fixes:

- Avoid using deprecated Django request.is_ajax() (#160)

## 2.16.2 2021-01-22

### Fixes

- Capture exception details in AWS Lambda middleware (#154)
- Default w3c sampled flag to 01 (#152)

## 2.16.1 2021-01-08

### Fixed
- Fix missing content_type, content_length, and status_code in spans from error responses (#145) [@vbarua](https://github.com/vbarua)

## 2.16.0

### Improvements:

- Add app.exception_stacktrace to context when an exception is thrown (#135)

### Fixes:

- Fix requests patch to correctly build span name (#142)
- Fix deprecations related to unittest usage (#141)

## 2.15.0

- Update Lambda wrapper to allow omission of input/output fields #130 (thank you, @fitzoh!)
- Add "request.route" field for Django middleware (thank you, @sjoerdjob!)

## 2.14.0

Improvements:

- Adds support for dataset when parsing honeycomb propagation headers #133

## 2.13.1

This is a maintenace release to fix a bug in the django middleware that can happen in testing environments when a beeling has
not been initialised.

- Don't attempt to use a non-initialised beeline instance in django middleware #126.
- Adds a .editorconfig to help apply consistent styling across IDEs #127.

## 2.13.0

### Features

We have added new functionality for `http_trace_parse_hook` and `http_trace_propagation_hook`. These hooks allow beeline users
to parse incoming headers, as well as add outgoing headers, allowing for interoperability between Honeycomb,
OpenTelemetry (W3C) and other tracing formats.

- New `beeline` configuration parameters for `http_trace_parse_hook` and `http_trace_propagation_hook`
- New `propagate_and_start_trace` function for use by middleware to invoke the `http_trace_parse_hook`
- New `beeline.propagation` package to centralize propagation-related classes and functions.
- `beeline.propagation.honeycomb` package contains hooks to support parsing and propagation using honeycomb headers.
- `beeline.propagation.w3c` package contains hooks to support parsing and propagation using w3c headers.

### Deprecation Notice

- Deprecated the existing `beeline.marshal_trace_context`, and migrated all usage to new
  `beeline.propagation.honeycomb` functions. `beeline.marshal_trace_context` will be removed when the next major version of the beeline is released.

### Implementation details

- Implemented `beeline.propagation.Request` classes for middleware to aid in support of header and propagation hooks.
- Migrateed existing middleware to use new `beeline.propagation` classes and functions to support `http_trace_parse_hooks`.
- Centralized duplicated code for WSGI variants (Flask, Bottle, Werkzeug) into a single location.
- Added `http_trace_propagation_hook` support to requests and urllib.

### Fixes

- Fixed a bug where `urllib.request.urlopen` would fail if given a string URL as an argument.

## 2.12.2

Improvements

- Trace IDs and Span IDs now correspond to W3C trace context specification. See https://www.w3.org/TR/trace-context/
- Now using [poetry](https://python-poetry.org/) for packaging and dependency management.
- Tests now exclude `test_async` on Python versions which don't support async instead of requiring maintenance of an includelist of tests.
- No longer use `pyflask` in tests as `pylint` covers all issues checked by `pyflask`

- Misc
  - Files have been reformatted to pass pycodestyle (PEP8)
  - Now enforce passing pycodestyle in CI.
  - Now do CI testing against Python 3.8.

## 2.12.1 2020-03-24

Fixes

- Fixes `traced` decorator behavior when working with generators. [#106](https://github.com/honeycombio/beeline-python/pull/106)
- Fixes method for detection of asyncio. [#107](https://github.com/honeycombio/beeline-python/pull/107)

## 2.12.0 2020-03-19

Features

- urllib auto-instrumentation via patch.[#102](https://github.com/honeycombio/beeline-python/pull/102)
- jinja2 auto-instrumentation via patch. [#103](https://github.com/honeycombio/beeline-python/pull/103)

Improvements

- flask auto-instrumentation now includes the route as `request.route` field on the root span. [#104](https://github.com/honeycombio/beeline-python/pull/104)

## 2.11.4 2020-01-27

Fixes

- Trace context headers injected with the `requests` middleware now reference the correct parent span. Previously, the trace context was generated prior to the wrapping span around the request call, anchoring spans generated with this trace context to the wrong span.

## 2.11.3 2020-01-23

Fixes

- Prevent duplicate `app.` prefixes in trace fields. [#96](https://github.com/honeycombio/beeline-python/pull/96)

## 2.11.2 2019-11-26

Fixes

- Allows less than three fields in trace context headers.

## 2.11.1 2019-11-19

Fixes

- Flask Middleware: AttributeError in DB instrumentation when cursor.lastrowid doesn't exist [#91](https://github.com/honeycombio/beeline-python/pull/91).

## 2.11.0 2019-11-18

Features

- Asyncio support! The new `AsyncioTracer` is used instead of `SynchronousTracer` when the beeline is initialized from within an asyncio event loop. [#87](https://github.com/honeycombio/beeline-python/pull/87)

## 2.10.1 2019-11-12

- Traces propagated from other beelines (nodejs, go) which supply the "dataset" field in the trace context can now be handled by `unmarshal_trace_context`. The dataset is discarded - honoring this override will come in a later version.

## 2.10.0 2019-11-07

Features

- `awslambda` middleware can now extract Honeycomb Trace context from single SNS/SQS messages. [#77](https://github.com/honeycombio/beeline-python/pull/77)

## 2.9.1 2019-09-10

Fixes

- Don't try to access self.state.span in handle_error of Flask DB middleware if there is no current_app [#81](https://github.com/honeycombio/beeline-python/pull/81).

## 2.9.0 2019-09-09

Improvements

- Django middleware now supports instrumentation of multiple database connections. See [#80](https://github.com/honeycombio/beeline-python/pull/80).

## 2.8.0 2019-08-06

Features

- Django, Flask, Bottle, and Werkzeug middleware can now be subclassed to provide alternative implementations of `get_context_from_request` (Django) `get_context_from_environ` (Flask, Bottle, Werkzeug) methods. This allows customization of the request fields that are automatically instrumented at the start of a trace. Thanks to sjoerdjob's initial contribution in [#73](https://github.com/honeycombio/beeline-python/pull/73).

Fixes

- Django's `HoneyMiddleware` no longer adds a `request.post` field by default. This was removed for two reasons. First, calling `request.POST.dict()` could break other middleware by exhausting the request stream prematurely. See issue [#74](https://github.com/honeycombio/beeline-python/issues/74). Second, POST bodies can contain arbitrary values and potentially sensitive data, and the decision to instrument these values should be a deliberate choice by the user. If you currently rely on this behavior currently, you can swap out `HoneyMiddleware` with `HoneyMiddlewareWithPOST` to maintain the same functionality.
- The `awslambda` middleware no longer crashes if the `context` object is missing certain attributes. See [#76](https://github.com/honeycombio/beeline-python/pull/76).

## 2.7.0 2019-07-26

Features

- Implements `add_rollup_field` API used in other Beelines. See the official [API reference docs](https://honeycombio.github.io/beeline-python/) for full details.

## 2.6.1 2019-07-02

Fixes

- Python Beeline now uses the same method to compute deterministic sampling decisions as other beelines (Go, NodeJS, Ruby). Prior to the fix, Beeline-generated traces spanning multiple services implemented in Python and other languages would have sometimes arrived incomplete due to inconsistent sampling behavior.

## 2.6.0 2019-06-05 - Update recommended

Features

- Adds new `traced_thread` decorator to copy over trace state to new threads. Read more in the official docs [here](https://docs.honeycomb.io/getting-data-in/python/beeline/#threading-and-traces).
- Adds initial support for [Werkzeug](https://werkzeug.palletsprojects.com/en/0.15.x/). Read about how to use it [here](https://docs.honeycomb.io/getting-data-in/python/beeline/#using-automatic-instrumentation).

Fixes

- `init` now works after a process fork. If the beeline has already been initialized prior to the fork, it will be reinitialized if called again. Prior to this change, calling `init` before fork would render the beeline inoperable in the forked process(es).

## 2.5.1 2019-05-13

Fixes

- Support parameters of type `dict` in the flask-sqlachemy middleware. Addresses [#62](https://github.com/honeycombio/beeline-python/issues/62).

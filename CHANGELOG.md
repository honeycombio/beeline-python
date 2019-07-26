# beeline-python changelog

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

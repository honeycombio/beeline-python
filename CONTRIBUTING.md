# Contributing Guide

Please see our [general guide for OSS lifecycle and practices.](https://github.com/honeycombio/home/blob/main/honeycomb-oss-lifecycle-and-practices.md)

Features, bug fixes and other changes to this project are gladly accepted.
Please open issues or a pull request with your change. Remember to add your name
to the CONTRIBUTORS file!

All contributions will be released under the Apache License 2.0.

## Developing

beeline-python uses [poetry](https://python-poetry.org/) for packaging and dependency management. Our normal development workflow also uses [pyenv](https://github.com/pyenv/pyenv) to manage python versions.

If you haven't used pyenv or poetry before, see https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/ for a quick guide to getting started using them both.

### Setting up on Mac

- Install [pyenv](https://github.com/pyenv/pyenv) to install python version management

  - `brew install pyenv`

- Follow https://python-poetry.org/ install instructions - it may be possible to use brew to install `poetry`, but it's not offically supported.

* Install dependencies:
  - `poetry install --no-root` to install dependencies.
  - Use `poetry`'s commands for managing dependencies, including adding and updating them..
* Run tests - the below command is configured to run all tests:
  - `poetry run tests`
* Get a shell

  - `poetry shell` will get you a shell with the current virtualenv.

* Switch python version by using the PYENV_VERSION environment variable to toggle between multiple python versions for testing
  - `export PYENV_VERSION=3.10.1` to set the Python virtualenv to 3.10.1

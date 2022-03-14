# hello world example

## Setup and Run

1. Set environment variable for `HONEYCOMB_API_KEY`
1. In top-level directory of repo, run `poetry build` to create a wheel package in the `dist` directory
1. In hello-world directory, ensure version of beeline in `pyproject.toml` matches the wheel package
1. In hello-world directory, run `poetry install`
1. In hello-world directory, run `poetry run python3 app.py`

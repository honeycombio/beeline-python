# hello world example

This simple python app adds a manual span with trace context including the message of "Hello World".

## Prerequisites

First set an environment variable `HONEYCOMB_API_KEY`, available from your account page.
This will configure the server to send instrumentation events to Honeycomb in a dataset called my-flask-app.

You'll also need [Poetry](https://python-poetry.org/) installed to run the example. Poetry automatically creates a virtual environment to run the example in so you don't need to manage one yourself.

## Running the example

Install the dependencies:

```bash
poetry install
```

Run the application:

```bash
poetry run python3 app.py
```

Check out the results in Honeycomb!

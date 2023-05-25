# example django app

This simple django app uses auto-instrumentation and adds a manual span with trace context including the message of "Hello World".

## Prerequisites

First set an environment variable `HONEYCOMB_API_KEY`, available from your account page.
This will configure the server to send instrumentation events to Honeycomb in a dataset called my-django-app.

You'll also need [Poetry](https://python-poetry.org/) installed to run the example.
Poetry automatically creates a virtual environment to run the example in so you don't need to manage one yourself.

## Running the example

Install the dependencies:

```bash
poetry install
```

Navigate into the app directory:

```bash
cd app
```

Run the application:

```bash
poetry run python3 manage.py runserver
```

Now you can `curl` the app:

```bash
$ curl localhost:8000/hello/
Hello World
```

Check out the results in Honeycomb!

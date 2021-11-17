# example flask app

This simple Flask app uses auto-instrumentation and adds a manual span with trace context including the message of "Hello World".

## Prerequisites

First set an environment variable `HONEYCOMB_API_KEY`, available from your account page.
This will configure the server to send instrumentation events to Honeycomb in a dataset called my-flask-app.

You'll also need [Poetry](https://python-poetry.org/) installed to run the example. Poetry automatically creates a virtual environment to run the example in so you don't need to manage one yourself.

## Runing the example

Then install the dependencies:

```bash
poetry install
```

Run the application:

```bash
poetry run flask run
```

The server will start listening on port 5000:

```bash
$ curl localhost:5000
Hello World
```

Check out the results in Honeycomb!

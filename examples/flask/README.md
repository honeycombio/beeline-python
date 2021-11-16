# example flask app

This simple Flask app uses auto-instrumentation and adds a manual span with trace context including the message of "Hello World".

## Getting Started

First set an environment variable `HONEYCOMB_API_KEY`, available from your account page.
This will configure the server to send instrumentation events to Honeycomb in a dataset called my-flask-app.

## Download or Build

[Create and activate a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment):

```bash
python3 -m venv env

source env/bin/activate
```

Then install the dependencies:

```bash
python3 -m pip install .
```

Run the application:

```bash
flask run
```

The server will start listening on port 5000:

```bash
$ curl localhost:5000
Hello World
```

Check out results in Honeycomb! To [deactivate the virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#leaving-the-virtual-environment):

```bash
deactivate
```

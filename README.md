# Honeycomb Beeline for Python

The Honeycomb Beeline for Python is an easy way to instrument your Python web application for observability. It is compatible with the frameworks Django, Flask, and Tornado,
automatically instrumenting them to send useful events to [Honeycomb](https://www.honeycomb.io).

Compatible with both Python 2.7 and Python 3. Sign up for a [Honeycomb trial](https://ui.honeycomb.io/signup) to obtain an API key before starting.

## Installation

Fill me in!

## Instrumented Frameworks

The Beeline will automatically send events if you are using one of the listed frameworks:

### Django

The beeline uses Django's request/response middleware and database query execution wrapper to automatically instrument your HTTP requests and database queries, and also supports tracing.

To begin, add the following to the middleware section of your settings.py file:

```python
'beeline.middleware.django.HoneyMiddleware',
```

### Flask

The beeline makes use of WSGI middleware to instrument HTTP requests and also supports tracing. If you are using Flask's SQLAlchemy extension, you will also get built-in database query instrumentation.

To use it, add the following code where your Flask app is initialized:

```python
from beeline.middleware.flask import HoneyMiddleware

app = Flask(__name__)
HoneyMiddleware(app)
```

### Tornado

Fill me in!

## Configuration

You'll need to configure your Honeycomb API key so that your app can identify itself to Honeycomb. You can find your API key on [your Account page](https://ui.honeycomb.io/account).

You'll also need to configure the name of a dataset in your Honeycomb account to send events to. The name of your app is a good choice.

You can specify the configuration by passing arguments to `beeline.init()`:

```python
beeline.init(
  writekey: '<MY HONEYCOMB API KEY>',
  dataset: 'my-app',
  service_name: 'my-app'
)
```

Note that Honeycomb API keys have the ability to create and delete data, and should be managed in the same way as your other application secrets. For example you might prefer to configure production API keys via environment variables, rather than checking them into version control.

## Example questions

Now your app is instrumented and sending events, try using Honeycomb to ask these questions:

 * Which of my app's routes are the slowest?
```
BREAKDOWN: request.path
CALCULATE: P99(duration_ms)
ORDER BY: P99(duration_ms) DESC
```
 * Which users are using the endpoint that I'd like to deprecate? First add a
   [custom field](#adding-additional-context) `user.email`, then try:
```
BREAKDOWN: user.email
CALCULATE: COUNT
FILTER: request.path == /my/deprecated/endpoint
```

## Example event

Here is an example of an HTTP event (recording that your web app processed an incoming HTTP request) emitted by the Beeline:

```json
{
  "service_name": "my-test-app",
  "request.host": "my-test-app.example.com",
  "request.method": "GET",
  "request.path": "/dashboard",
  "request.query": "",
  "request.remote_addr": "172.217.1.238",
  "request.content_length": "0",
  "request.user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
  "request.scheme": "HTTP",
  "trace.trace_id": "b694512a-833f-4b35-be5f-6c742ba18e12",
  "trace.span_id": "c35cc326-ed90-4881-a4a8-68526d252f2e",
  "response.status_code": 200,
  "duration_ms": 303.057396
}
```

Here is an example of a database query event emitted by the Beeline:

```json
{
  "service_name": "my-test-app",
  "db.query": "SELECT todo.id FROM todo WHERE %s = todo.todolist_id",
  "db.query_args": "[1]",
  "db.duration": "0.41",
  "db.error": "",
  "db.last_insert_id": "0",
  "db.rows_affected": "1",
  "trace.trace_id": "b694512a-833f-4b35-be5f-6c742ba18e12",
  "trace.span_id": "c35cc326-ed90-4881-a4a8-68526d252f2e",
  "duration_ms": "0.82"
}
```

## Adding additional context

The Beeline will automatically instrument your incoming HTTP requests and database queries to send events to Honeycomb. However, it can be very helpful to extend these events with additional context specific to your app.  You can add your own fields by calling `beeline.add_field(name, value)`.

## Tracing

The Beeline will automatically add tracing to your incoming HTTP requests and database queries before sending events to Honeycomb. However, it can be very helpful to extend add tracing to additional calls within your code.  You can add your own tracing spans by calling `beeline._new_event()` with the `trace_name` and `top_level` params, or by using the tracing context manager `with beeline.trace(trace_name):`

## Known limitations

Fill me in!

If support for one of these scenarios is important to you, please [let us know](#get-in-touch)!

## Troubleshooting

If you've setup the Beeline as above but you aren't seeing data for your app in
Honeycomb, or you're seeing errors on startup, here are a few things to try:

### Debug mode

Fill me in!

### Logging

Fill me in!

### Get in touch

This beeline is still young, so please reach out to [support@honeycomb.io](mailto:support@honeycomb.io) or ping us with the chat bubble on [our website](https://www.honeycomb.io) for assistance.  We also welcome [bug reports](https://github.com/honeycombio/beeline-ruby/issues) and [contributions](https://github.com/honeycombio/beeline-ruby/blob/master/CONTRIBUTING.md).

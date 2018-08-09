# Honeycomb Beeline for Python

The Honeycomb Beeline for Python is an easy way to instrument your Python web application for observability. It is compatible with the frameworks Django (>1.10), Flask, Bottle, and Tornado, automatically instrumenting them to send useful events to [Honeycomb](https://www.honeycomb.io).

Compatible with both Python 2.7 and Python 3. Sign up for a [Honeycomb trial](https://ui.honeycomb.io/signup) to obtain an API key before starting.

## Installation

`pip install honeycomb-beeline`

Note: Make sure your version of `setuptools` is up to date (`pip install -U setuptools`).

## Configuration

The Beeline will automatically send events if you are using Django (>1.10), Flask, Bottle, or Tornado.

You'll need to configure your Honeycomb API key so that your app can identify itself to Honeycomb. You can find your API key on [your Account page](https://ui.honeycomb.io/account).

You'll also need to configure the name of a dataset in your Honeycomb account to send events to. The name of your app is a good choice.

You can specify the configuration by passing arguments to `beeline.init()`:

```python
beeline.init(
  writekey='<MY HONEYCOMB API KEY>',
  dataset='my-app',
  service_name='my-app'
)
```

Note that Honeycomb API keys have the ability to create and delete data, and should be managed in the same way as your other application secrets. For example you might prefer to configure production API keys via environment variables, rather than checking them into version control.

### Django

The beeline uses Django's request/response middleware (>1.10) and database query execution wrapper (>2.0) to automatically instrument your HTTP requests and database queries, and also supports tracing.

To begin, add the middleware to your settings.py file. Choose `HoneyMiddlewareHttp` if you do not want db instrumentation, or `HoneyMiddleware` if you do want db instrumentation.

```python
MIDDLEWARE = [
  'beeline.middleware.django.HoneyMiddleware',
]
```

Then, initialize the beeline in app's `apps.py` file:

```python
from django.apps import AppConfig
import beeline


class MyAppConfig(AppConfig):

    def ready(self):
        beeline.init(
            writekey='<MY HONEYCOMB API KEY>',
            dataset='my-app',
            service_name='my-app'
        )
```

Don't forget to set your app's default config in your app's `__init__.py` file:

```python
default_app_config = 'myapp.apps.MyAppConfig'
```

### Flask

The beeline makes use of WSGI middleware to instrument HTTP requests and also supports tracing. If you are using Flask's SQLAlchemy extension, you can also include our database middleware to get built-in query instrumentation.

To use it, add the following code where your Flask app is initialized:

```python
import beeline
from beeline.middleware.flask import HoneyMiddleware

beeline.init(
  writekey='<MY HONEYCOMB API KEY>',
  dataset='my-app',
  service_name='my-app'
)

app = Flask(__name__)
# db_events defaults to True, set to False if not using our db middleware with Flask-SQLAlchemy
HoneyMiddleware(app, db_events=True)
```

### Bottle

The beeline makes use of WSGI middleware to instrument HTTP requests and also supports tracing.

To use it, add the following code where your Bottle app is initialized:

```python
import beeline
from beeline.middleware.bottle import HoneyWSGIMiddleware

beeline.init(
  writekey='<MY HONEYCOMB API KEY>',
  dataset='my-app',
  service_name='my-app'
)

app = bottle.app()
myapp = HoneyWSGIMiddleware(app)
bottle.run(app=myapp)
```

### Tornado

In our initial release, we have limited instrumentation support for Tornado Web RequestHandlers. To instrument HTTP requests and exceptions, simply add a few lines of code to your app init:

```python
import beeline
import libhoney
from beeline.patch import tornado

beeline.init(
  writekey='<MY HONEYCOMB API KEY>',
  dataset='my-app',
  service_name='my-app',
   # use a tornado coroutine rather than a threadpool to send events
  transmission_impl=libhoney.transmission.TornadoTransmission(),
)
```

Full tracing support is on our roadmap, as is support for other asynchronous frameworks.

## Example questions

Now your app is instrumented and sending events, try using Honeycomb to ask these questions:

- Which of my app's routes are the slowest?

```
BREAKDOWN: request.path
CALCULATE: P99(duration_ms)
FILTER: type == http_server
ORDER BY: P99(duration_ms) DESC
```

- Where's my app spending the most time?

```
BREAKDOWN: type
CALCULATE: SUM(duration_ms)
ORDER BY: SUM(duration_ms) DESC
```

- Which users are using the endpoint that I'd like to deprecate? First add a
  [custom field](#adding-additional-context) `user.email`, then try:

```
BREAKDOWN: user.email
CALCULATE: COUNT
FILTER: request.path == /my/deprecated/endpoint
```

## Example event

Here is an example of an HTTP event (type: http_server) emitted by the Beeline:

```json
{
  "service_name": "my-test-app",
  "type": "http_server",
  "request.host": "my-test-app.example.com",
  "request.method": "GET",
  "request.path": "/dashboard",
  "request.query": "",
  "request.remote_addr": "172.217.1.238",
  "request.content_length": "0",
  "request.user_agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
  "request.scheme": "HTTP",
  "trace.trace_id": "b694512a-833f-4b35-be5f-6c742ba18e12",
  "trace.span_id": "c35cc326-ed90-4881-a4a8-68526d252f2e",
  "response.status_code": 200,
  "duration_ms": 303.057396
}
```

Here is an example of a database query (type: db) event emitted by the Beeline:

```json
{
  "service_name": "my-test-app",
  "type": "db",
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

## Adding additional context to events

The Beeline will automatically instrument your incoming HTTP requests and database queries to send events to Honeycomb. However, it can be very helpful to extend these events with additional context specific to your app. You can add your own fields by calling `beeline.add_field(name, value)`.

## Tracing

The Beeline will automatically add tracing to your incoming HTTP requests and database queries before sending events to Honeycomb. However, it can be very helpful to add tracing in additional places within your code. For example, if you have some code that does an expensive computation, you could simply wrap it in the tracer context manager like so:

```python
with beeline.tracer("my expensive computation"):
    recursive_fib(100)
```

## Using Sampler and Presend Hooks

Hooks give you more power over how events are sampled, and which fields are sent to Honeycomb.

### Using a Sampler Hook

Sampler hooks allow you to completely redefine sampling behavior. This replaces built-in sampling logic and replaces it with your own. It also overrides the global sampling rate.

Here is an example: assume you have instrumented an HTTP app and want a default sampling rate of 1 in 10 events. However, you'd like to keep all error events, and heavily sample healthy traffic (200 response codes). Also, you don't really care about 302 redirects in your app, and you want to drop those. You could define a sampler function like so:

```python
def sampler(fields):
  # our default sample rate, sample one in every 10 events
  sample_rate = 10

  response_code = fields.get('response.status_code')
  # False indicates that we should not keep this event
  if response_code == 302:
    return False, 0
  elif response_code == 200:
    # heavily sample healthy requests
    sample_rate = 100
  elif response_code >= 500:
    # sample every error request
    sample_rate = 1

  # True means we keep the event. The sample rate tells Honeycomb what
  # rate the event was sampled at (important for calculations)
  if random.randint(1, sample_rate) == 1:
    return True, sample_rate

  return False, 0
```

To apply this new logic, all you have to do is pass this sampler to the beeline on `init`:

```python
import beeline
beeline.init(writekey='mywritekey', dataset='myapp', sampler_hook=sampler)
```

**Note**: If you intend to use tracing, defining your own sampler can lead to inconsistent trace results.

### Using a Pre-send Hook

Presend hooks enable you to modify data right before it is sent to Honeycomb. For example, maybe you have a field that sometimes contains PII or other sensitive data. You might want to scrub the field, or drop it all together. You can do that with a pre-send hook:

```python
def presend(fields):
  # We don't want to log customer IPs that get captured in the beeline
  if 'request.remote_addr' in 'fields':
    del fields['request.remote_addr']

  # this field is useful, but sometimes contains sensitive data. 
  # Run a scrubber method against it before sending
  if 'transaction_log_msg' in 'fields':
    fields['transaction_log_msg'] = scrub_msg(fields['transaction_log_msg'])
```

After defining your presend hook function, pass it to the beeline's `init` method:

```python
import beeline
beeline.init(writekey='mywritekey', dataset='myapp', presend_hook=presend)
```

**Note**: Sampler hooks are executed *before* presend hooks.

## Get in touch

This beeline is still young, so please reach out to [support@honeycomb.io](mailto:support@honeycomb.io) or ping us with the chat bubble on [our website](https://www.honeycomb.io) for assistance. We also welcome [bug reports](https://github.com/honeycombio/beeline-python/issues) and [contributions](https://github.com/honeycombio/beeline-python/blob/master/CONTRIBUTING.md). Also check out our [official docs](https://docs.honeycomb.io/getting-data-in/beelines/beeline-python/).

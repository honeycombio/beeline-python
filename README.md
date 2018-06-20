# Python Beeline



## Flask

The beeline makes use of WSGI middleware in Flask to instrument HTTP requests and add tracing.
If you are using Flask's SQLAlchemy extension, you will also get built-in database query instrumentation and tracing.

Add the following code where your Flask app is initialized:

```
from beeline.middleware.flask import HoneyMiddleware

app = Flask(__name__)
HoneyMiddleware(app)
```

## Django

The beeline uses Django request/response and database middleware to automatically instrument your HTTP requests and database queries, and also adds tracing.

Add the following to the middleware section of your settings.py file:

```
'beeline.middleware.django.HoneyMiddleware',
```
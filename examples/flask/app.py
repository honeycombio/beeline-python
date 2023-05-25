import beeline
import os

from beeline.middleware.flask import HoneyMiddleware
from flask import Flask

# Get this via https://ui.honeycomb.io/account after signing up for Honeycomb
honeycomb_writekey=os.environ.get("HONEYCOMB_API_KEY")

beeline.init(
    writekey=honeycomb_writekey,
    api_host=os.environ.get('HONEYCOMB_API_ENDPOINT', 'https://api.honeycomb.io:443'),
    # The name of your app is a good choice to start with
    # dataset='my-flask-app', # only needed for classic
    service_name=os.environ.get('SERVICE_NAME', 'my-flask-app'),
    debug=True, # enable to see telemetry in console
)

# Pass your Flask app to HoneyMiddleware
app = Flask(__name__)
HoneyMiddleware(app, db_events=False)

@app.route("/")
def hello_world():
  span = beeline.start_span(context={"name": "Preparing to greet the world"})
  message = "Hello World"
  beeline.add_trace_field('message', message)
  beeline.finish_span(span)
  return message
import beeline
import os

from beeline.middleware.flask import HoneyMiddleware
from flask import Flask

honeycomb_writekey=os.environ.get("HONEYCOMB_API_KEY")

beeline.init(writekey=honeycomb_writekey, dataset="my-flask-app", service_name="my-flask-app-service")

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
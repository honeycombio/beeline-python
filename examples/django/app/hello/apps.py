import beeline
import os

from django.apps import AppConfig

class HelloConfig(AppConfig):
    name = 'hello'

    def ready(self):
        beeline.init(
            # Get this via https://ui.honeycomb.io/account after signing up for Honeycomb
            writekey=os.environ.get("HONEYCOMB_API_KEY"),
            api_host=os.environ.get('HONEYCOMB_API_ENDPOINT', 'https://api.honeycomb.io:443'),
            # The name of your app is a good choice to start with
            # dataset='my-django-app', # only needed for classic
            service_name=os.environ.get('SERVICE_NAME', 'my-django-app'),
            debug=True, # enable to see telemetry in console
        )
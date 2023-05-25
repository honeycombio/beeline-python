import beeline
import os

from django.apps import AppConfig

class HelloConfig(AppConfig):
    name = 'hello'

    def ready(self):
        beeline.init(
            writekey=os.environ.get("HONEYCOMB_API_KEY"),
            api_host="https://api.honeycomb.io",
            service_name='my-django-app',
            debug=True,
        )
import beeline
import os

beeline.init(
    # Get this via https://ui.honeycomb.io/account after signing up for Honeycomb
    writekey=os.environ.get('HONEYCOMB_API_KEY'),
    api_host=os.environ.get('HONEYCOMB_API_ENDPOINT', 'http://api.honeycomb.io:443'),
    # The name of your app is a good choice to start with
    # dataset='my-python-beeline-app', # only needed for classic
    service_name=os.environ.get('SERVICE_NAME', 'my-python-app'),
    debug=True, # enable to see telemetry in console
)

@beeline.traced(name='hello_world')
def hello_world():
    print('hello world')
    beeline.add_context_field('message', 'hello world')

hello_world()

beeline.close()
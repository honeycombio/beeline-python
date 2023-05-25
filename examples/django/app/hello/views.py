import beeline
from django.http import HttpResponse


@beeline.traced(name="hello_world")
def index(request):
    message = "Hello World\n"
    beeline.add_trace_field('message', message)
    return HttpResponse(message)
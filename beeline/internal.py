import beeline

# these are mostly convenience methods for safely calling beeline methods
# even if the beeline hasn't been initialized
def new_event(data=None, trace_name='', top_level=False):
    bl = beeline.get_beeline()
    if bl:
        bl.log("creating new event with data = %s", data)
        return bl.new_event(data, trace_name, top_level)

def send_event():
    bl = beeline.get_beeline()
    if bl:
        return bl.send_event()

def send_all():
    bl = beeline.get_beeline()
    if bl:
        return bl.send_all()

def log(msg, *args, **kwargs):
    bl = beeline.get_beeline()
    if bl:
        bl.log(msg, *args, **kwargs)

import beeline

# these are mostly convenience methods for safely calling beeline methods
# even if the beeline hasn't been initialized
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

def stringify_exception(e):
    try:
        return str(e)
    except UnicodeEncodeError:
        try:
            return u"{}".format(e)
        except Exception:
            return "unable to decode exception"

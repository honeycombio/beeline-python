from wrapt import wrap_function_wrapper
import beeline


def _render_template(fn, instance, args, kwargs):
    span = beeline.start_span(context={
        "name": "jinja2_render_template",
        "template.name": instance.name or "[string]",
    })

    try:
        return fn(*args, **kwargs)
    finally:
        beeline.finish_span(span)


wrap_function_wrapper('jinja2', 'Template.render', _render_template)

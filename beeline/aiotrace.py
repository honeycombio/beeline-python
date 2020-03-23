"""Asynchronous tracer implementation.

This requires Python 3.7, because it uses the contextvars module.

"""
import asyncio
import contextvars  # pylint: disable=import-error
import functools
import inspect

from beeline.trace import Tracer

current_trace_var = contextvars.ContextVar("current_trace")


def create_task_factory(parent_factory):
    """Create a task factory that makes a copy of the current trace.

    New tasks have their own context variables, but the current_trace
    context variable still refers to the same Trace object as the one
    in the parent task. This task factory replaces the Trace object
    with a copy of itself.

    """
    def task_factory_impl(loop, coro):
        async def wrapper():
            current_trace = current_trace_var.get(None)
            if current_trace is not None:
                current_trace_var.set(current_trace.copy())
            return await coro

        if parent_factory is None:
            task = asyncio.tasks.Task(wrapper(), loop=loop)
        else:
            task = parent_factory(wrapper())

        return task

    task_factory_impl.__trace_task_factory__ = True
    return task_factory_impl


class AsyncioTracer(Tracer):
    def __init__(self, client):
        """Initialize, and ensure that our task factory is set up."""
        super().__init__(client)

        loop = asyncio.get_running_loop()  # pylint: disable=no-member

        task_factory = loop.get_task_factory()
        if task_factory is None or not task_factory.__trace_task_factory__:
            new_task_factory = create_task_factory(task_factory)
            loop.set_task_factory(new_task_factory)

    @property
    def _trace(self):
        return current_trace_var.get(None)

    @_trace.setter
    def _trace(self, new_trace):
        current_trace_var.set(new_trace)


def traced_impl(tracer_fn, name, trace_id, parent_id):
    """Implementation of the traced decorator including async support.

    The async version needs to be different, because the trace should
    cover the execution of the whole decorated function. If using the
    synchronous version, the trace would only cover the time it takes
    to return the coroutine object.

    """
    def wrapped(fn):
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_inner(*args, **kwargs):
                with tracer_fn(name=name, trace_id=trace_id, parent_id=parent_id):
                    return await fn(*args, **kwargs)

            return async_inner
        elif inspect.isgeneratorfunction(fn):
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                inner_generator = fn(*args, **kwargs)
                with tracer_fn(name=name, trace_id=trace_id, parent_id=parent_id):
                    yield from inner_generator

            return inner
        else:
            @functools.wraps(fn)
            def inner(*args, **kwargs):
                with tracer_fn(name=name, trace_id=trace_id, parent_id=parent_id):
                    return fn(*args, **kwargs)

            return inner

    return wrapped


def untraced(fn):
    """Async function decorator detaching from any ongoing trace.

    This decorator is necessary for starting independent async tasks
    from within a trace, since async tasks inherit trace state by
    default.

    """

    # Both synchronous and asynchronous functions may create tasks.
    if asyncio.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                token = None
                current_trace = current_trace_var.get(None)
                if current_trace is not None:
                    token = current_trace_var.set(None)

                return await fn(*args, **kwargs)
            finally:
                if token is not None:
                    current_trace_var.reset(token)

        return wrapped

    else:
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                token = None
                current_trace = current_trace_var.get(None)
                if current_trace is not None:
                    token = current_trace_var.set(None)

                return fn(*args, **kwargs)
            finally:
                if token is not None:
                    current_trace_var.reset(token)

        return wrapped

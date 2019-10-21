"""Asynchronous tracer implementation.

This requires Python 3.7, because it uses the contextvars module.

"""
import asyncio
import contextvars  # pylint: disable=import-error

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

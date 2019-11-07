import asyncio
import datetime
import unittest

import beeline
import beeline.aiotrace
import beeline.trace


def async_test(fn):
    """Decorator for making async methods usable as tests.

    This decorator also runs the async_setup method before each test,
    if it exists.

    """
    def wrapper(self, *args, **kwargs):
        async def sequence():
            if hasattr(self, "async_setup"):
                await self.async_setup()
            return await fn(self, *args, **kwargs)

        return asyncio.run(sequence(*args, **kwargs))  # pylint: disable=no-member

    return wrapper


def span_data(span):
    """Utility for converting Span objects to dicts."""
    name = span.event.fields().get("name")
    start = span.event.start_time
    duration = datetime.timedelta(
        milliseconds=span.event.fields()["duration_ms"]
    )
    end = start + duration
    return {
        "name": name,
        "start": start,
        "end": end,
        "trace_id": span.trace_id,
        "span": span,
    }


class TestTracerImplChoice(unittest.TestCase):
    def test_synchronous_tracer_should_be_used_by_default(self):
        """Verify that the SynchronousTracer implementation is chosen when a
        Beeline object is initialised outside of an asyncio loop.

        """
        _beeline = beeline.Beeline()
        self.assertIsInstance(
            _beeline.tracer_impl, beeline.trace.SynchronousTracer
        )

    @async_test
    async def test_asyncio_tracer_should_be_used_in_async_code(self):
        """Verify that the AsyncioTracer implementation is chosen when a
        Beeline object is initialised while running inside an asyncio
        loop.

        """
        _beeline = beeline.Beeline()
        self.assertIsInstance(
            _beeline.tracer_impl, beeline.aiotrace.AsyncioTracer
        )


class TestAsynchronousTracer(unittest.TestCase):
    async def async_setup(self):
        self.finished_spans = []

        def add_span(span):
            self.finished_spans.append(span_data(span))

        self.beeline = beeline.Beeline()
        self.tracer = self.beeline.tracer_impl
        self.tracer._run_hooks_and_send = add_span

    @async_test
    async def test_tracing_in_new_tasks_should_work(self):
        """Test that basic AsyncioTracer functionality is present."""
        trace = self.tracer.start_trace()
        self.tracer.finish_trace(trace)

        self.assertEqual(len(self.finished_spans), 1)

    @async_test
    async def test_traces_started_in_different_tasks_should_be_independent(self):
        """Fork off two tasks, each calling start_trace.

        The traces run simultaneously. This is expected to produce two
        independent traces without raising any exceptions.

        """
        async def task0():
            trace0 = self.tracer.start_trace(context={"name": "task0"})
            await asyncio.sleep(0.2)
            self.tracer.finish_trace(trace0)

        async def task1():
            await asyncio.sleep(0.1)
            trace1 = self.tracer.start_trace(context={"name": "task1"})
            await asyncio.sleep(0.2)
            self.tracer.finish_trace(trace1)

        await asyncio.gather(task0(), task1())

        self.assertEqual(len(self.finished_spans), 2)
        task0_span, task1_span = self.finished_spans  # pylint: disable=unbalanced-tuple-unpacking

        # Check that the spans finished in the expected order.
        self.assertEqual(task0_span["name"], "task0")
        self.assertEqual(task1_span["name"], "task1")
        self.assertLess(task0_span["end"], task1_span["end"])

        # Check that the task0 started before task1
        self.assertLess(task0_span["start"], task1_span["start"])

        # Check that the task1 span started during the task0 span
        self.assertLess(task1_span["start"], task0_span["end"])

        # Check that the task spans are both root spans
        self.assertTrue(task0_span["span"].is_root())
        self.assertTrue(task1_span["span"].is_root())

    @async_test
    async def test_new_tasks_should_trace_in_parallel(self):
        """Fork off two tasks after starting a trace.

        Both tasks record a span, overlapping with each other. Both
        spans are expected to have the root span as their parent.

        """

        trace = self.tracer.start_trace(context={"name": "root"})

        async def task0():
            span0 = self.tracer.start_span(context={"name": "task0"})
            await asyncio.sleep(0.2)
            self.tracer.finish_span(span0)

        async def task1():
            await asyncio.sleep(0.1)
            span1 = self.tracer.start_span(context={"name": "task1"})
            await asyncio.sleep(0.2)
            self.tracer.finish_span(span1)

        await asyncio.gather(task0(), task1())

        self.tracer.finish_trace(trace)

        self.assertEqual(len(self.finished_spans), 3)
        task0_span, task1_span, root_span = self.finished_spans  # pylint: disable=unbalanced-tuple-unpacking

        # Check that the spans finished in the expected order, with
        # the root span last.
        self.assertEqual(task0_span["name"], "task0")
        self.assertEqual(task1_span["name"], "task1")
        self.assertLess(task0_span["end"], task1_span["end"])
        self.assertEqual(root_span["name"], "root")
        self.assertLessEqual(task1_span["end"], root_span["end"])

        # Check that the root span was started before the others.
        self.assertLess(root_span["start"], task0_span["start"])
        self.assertLess(root_span["start"], task1_span["start"])

        # Check that the task0 started before task1
        self.assertLess(task0_span["start"], task1_span["start"])

        # Check that the task1 span started during the task0 span
        self.assertLess(task1_span["start"], task0_span["end"])

        # Check that the task spans are both children of the root span
        self.assertEqual(root_span["span"].id, task0_span["span"].parent_id)
        self.assertEqual(root_span["span"].id, task1_span["span"].parent_id)

    @async_test
    async def test_traced_decorators(self):
        """Fork off two tasks after starting a trace.

        This is the same as test_new_tasks_should_trace_in_parallel,
        except it uses the traced decorator to record the sub-spans.

        """
        trace = self.tracer.start_trace(context={"name": "root"})

        @self.beeline.traced("task0")
        async def task0():
            await asyncio.sleep(0.2)

        async def task1():
            await asyncio.sleep(0.1)

            @self.beeline.traced("task1")
            async def decorated_fn():
                await asyncio.sleep(0.2)

            await decorated_fn()

        await asyncio.gather(task0(), task1())

        self.tracer.finish_trace(trace)

        self.assertEqual(len(self.finished_spans), 3)

        task0_span, task1_span, root_span = self.finished_spans  # pylint: disable=unbalanced-tuple-unpacking

        # Check that the spans finished in the expected order, with
        # the root span last.
        self.assertEqual(task0_span["name"], "task0")
        self.assertEqual(task1_span["name"], "task1")
        self.assertLess(task0_span["end"], task1_span["end"])
        self.assertEqual(root_span["name"], "root")
        self.assertLessEqual(task1_span["end"], root_span["end"])

        # Check that the root span was started before the others.
        self.assertLess(root_span["start"], task0_span["start"])
        self.assertLess(root_span["start"], task1_span["start"])

        # Check that the task0 started before task1
        self.assertLess(task0_span["start"], task1_span["start"])

        # Check that the task1 span started during the task0 span
        self.assertLess(task1_span["start"], task0_span["end"])

        # Check that the task spans are both children of the root span
        self.assertEqual(root_span["span"].id, task0_span["span"].parent_id)
        self.assertEqual(root_span["span"].id, task1_span["span"].parent_id)

    @async_test
    async def test_traceless_spans_in_other_tasks_should_be_ignored(self):
        """Start a span without first starting a trace in the same task.

        This span is started while there is a trace started in another
        task. This span should be independent from that trace, and is
        expected to be ignored.

        """
        async def task0():
            await asyncio.sleep(0.2)
            trace = self.tracer.start_trace(context={"name": "task0"})
            await asyncio.sleep(0.2)
            self.tracer.finish_trace(trace)

        async def task1():
            await asyncio.sleep(0.1)
            span = self.tracer.start_span(context={"name": "task1"})
            await asyncio.sleep(0.2)
            self.tracer.finish_span(span)

        await asyncio.gather(task0(), task1())

        self.assertEqual(len(self.finished_spans), 1)
        task0_span = self.finished_spans[0]

        # Check that only the trace produced a span.
        self.assertEqual(task0_span["name"], "task0")

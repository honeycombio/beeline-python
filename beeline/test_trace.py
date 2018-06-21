from mock import Mock
import unittest
import uuid

from beeline.trace import _should_sample, SynchronousTracer

class TestTraceSampling(unittest.TestCase):
    def test_deterministic(self):
        ''' test a specific id that should always work with the given sample rate '''
        trace_id = '8bd68312-a3ce-4bf8-a2df-896cef4289e5'
        n = 0
        while n < 1000:
            self.assertTrue(_should_sample(trace_id, 1000))
            n += 1

    def test_probability(self):
        ''' test that _should_sample approximates 1 in N sampling for random IDs '''
        tests_count = 50000
        error_margin = 0.05

        sample_rates = [1, 2, 10]

        for rate in sample_rates:
            sampled = n = 0

            while n < tests_count:
                n += 1
                if _should_sample(str(uuid.uuid4()), rate):
                    sampled += 1

            expected = tests_count // rate

            acceptable_lower_bound = int(expected - (expected * error_margin))
            acceptable_upper_bound = int(expected + (expected * error_margin))

            self.assertLessEqual(sampled, acceptable_upper_bound)
            self.assertGreaterEqual(sampled, acceptable_lower_bound)

class TestSynchronousTracer(unittest.TestCase):
    def test_trace_context_manager_exception(self):
        ''' ensure that send_traced_event is called even if an exception is
        raised inside the context manager '''
        m_client, m_state = Mock(), Mock()
        tracer = SynchronousTracer(m_client, m_state)
        try:
            with tracer('foo'):
                raise Exception('boom!')
        except Exception:
            pass
        
        m_state.pop_event.assert_called_once_with()
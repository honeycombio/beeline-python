''' module beeline '''
import datetime
import os

from libhoney import Client
from beeline.state import ThreadLocalState
from beeline.trace import SynchronousTracer

g_client = None
g_state = None
g_tracer = None

def init(writekey='', dataset='', service_name='', state_manager=None, tracer=None,
        sample_rate=1, api_host='https://api.honeycomb.io', max_concurrent_batches=10,
        max_batch_size=100, send_frequency=0.25,
        block_on_send=False, block_on_response=False, transmission_impl=None):
    ''' initialize the honeycomb beeline. This will initialize a libhoney
    client local to this module, and a state manager for tracking event context.

    Args:
    - `writekey`: the authorization key for your team on Honeycomb. Find your team
            write key at [https://ui.honeycomb.io/account](https://ui.honeycomb.io/account)
    - `dataset`: the name of the default dataset to which to write
    - `sample_rate`: the default sample rate. 1 / `sample_rate` events will be sent.
    - `max_concurrent_batches`: the maximum number of concurrent threads sending events.
    - `max_batch_size`: the maximum number of events to batch before sendinga.
    - `send_frequency`: how long to wait before sending a batch of events, in seconds.
    - `block_on_send`: if true, block when send queue fills. If false, drop
            events until there's room in the queue
    - `block_on_response`: if true, block when the response queue fills. If
            false, drop response objects.
    - `transmission_impl`: if set, override the default transmission implementation
            (for example, TornadoTransmission)

    If in doubt, just set `writekey` and `dataset` and move on!
    '''
    global g_client, g_state, g_tracer
    if g_client:
        return

    # allow setting some values from the environment
    if not writekey:
        writekey = os.environ.get('HONEYCOMB_WRITEKEY', '')

    if not dataset:
        dataset = os.environ.get('HONEYCOMB_DATASET', '')

    if not service_name:
        service_name = os.environ.get('HONEYCOMB_SERVICE', dataset)

    g_client = Client(
        writekey=writekey, dataset=dataset, sample_rate=sample_rate,
        api_host=api_host, max_concurrent_batches=max_concurrent_batches,
        max_batch_size=max_batch_size, send_frequency=send_frequency,
        block_on_send=block_on_send, block_on_response=block_on_response,
        transmission_impl=transmission_impl,
    )

    g_client.add_field('service_name', service_name)

    if state_manager:
        g_state = state_manager
    else:
        g_state = ThreadLocalState()

    g_tracer = SynchronousTracer(g_client, g_state)

def add_field(name, value):
    ''' Add a field to the currently active event. For example, if you are
    using django and wish to add additional context to the current request
    before it is sent to Honeycomb:

    `beeline.add_field("my field", "my value")`
    '''
    if not g_state:
        return
    # fetch the current event from our state provider
    ev = g_state.get_current_event()
    # if no event is in state, we're a noop
    if ev is None:
        return

    ev.add_field(name, value)

def tracer(name):
    return g_tracer(name)

def _new_event(data=None, trace_name='', trace_start=False):
    ''' internal - create a new event, populating it with the given data if
    supplied. The event is added to the given State manager. To send the
    event, call _send_event()

    If `trace_name` is set, generate trace metadata and measure the time
    between when the event is created and when the event is sent as
    `duration_ms`

    If trace_start is True, resets any previous trace data. Set this in
    top-level events (example: start of a request)
    '''
    if not g_client or not g_state:
        return

    if trace_start:
        g_state.reset()

    ev = g_client.new_event()
    if data:
        ev.add(data)
    if trace_name:
        trace_id, parent_id, span_id = g_state.start_trace()
        ev.add({
            'trace.trace_id': trace_id,
            'trace.parent_id': parent_id,
            'trace.span_id': span_id,
            'name': trace_name,
        })
        ev.start_time = datetime.datetime.now()
    g_state.add_event(ev)

def _send_event():
    ''' internal - send the current event in the state manager, if one exists
    '''
    if not g_client or not g_state:
        return

    ev = g_state.pop_event()

    # if start time is set, this was a traced event
    if hasattr(ev, 'start_time'):
        duration = datetime.datetime.now() - ev.start_time
        duration_ms = duration.total_seconds() * 1000.0
        ev.add_field('duration_ms', duration_ms)
        g_state.end_trace()

    if ev is None:
        return

    ev.send()


def close():
    ''' close the beeline client, flushing any unsent events. '''
    global g_client
    if g_client:
        g_client.close()

    g_client = None

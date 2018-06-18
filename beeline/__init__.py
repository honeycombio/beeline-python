''' module beeline '''
import os

from libhoney import Client

g_client = None

def init(writekey='', dataset='', service_name='', sample_rate=1.0,
        api_host='https://api.honeycomb.io', max_concurrent_batches=10,
        max_batch_size=100, send_frequency=0.25,
        block_on_send=False, block_on_response=False, transmission_impl=None):
    ''' initialize the honeycomb beeline. This will initialize a libhoney
    client local to this module.

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
    global g_client
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

def send_now(data):
    if g_client:
        g_client.send_now(data)

def close():
    ''' close the beeline client, flushing any unsent events. '''
    global g_client
    if g_client:
        g_client.close()

    g_client = None

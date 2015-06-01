import responses
import json
from collections import defaultdict
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..mojio_events_block import MojioEvents

# Build a response with two new objects and one old
SAMPLE_RESPONSE = {
    "PageSize": 10,
    "Offset": 0,
    "TotalRows": 3,
    "Data": [
        {
            "EventType": "MojioWake",
            "Time": "2015-05-01T00:00:00Z",
            "Type": "Event"
        },
        {
            "EventType": "IgnitionOn",
            "Time": "2015-04-01T00:00:00Z",
            "Type": "Event"
        },
        {
            "EventType": "Accelerometer",
            "Time": "2015-03-01T00:00:00Z",
            "Type": "Event"
        }
    ]}


class TestMojioEvents(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        # This will keep a list of signals notified for each output
        self.last_notified = defaultdict(list)

    def signals_notified(self, signals, output_id='default'):
        self.last_notified[output_id].extend(signals)

    @responses.activate
    def test_request(self):
        blk = MojioEvents()

        # Set the previous fresh post to the last post of the sample response
        blk.prev_freshest = blk.created_epoch(SAMPLE_RESPONSE['Data'][-1])
        responses.add(responses.GET, 'https://api.moj.io/v1/Events',
                      body=json.dumps(SAMPLE_RESPONSE), status=200,
                      content_type='application/json')
        self.configure_block(blk, {
            'polling_interval': {
                'seconds': 0  # We will drive polls with signals
            },
            'queries': ['dummy']
        })
        blk.start()

        blk.process_signals([Signal()])

        # We want the two new ones, not the old one
        self.assert_num_signals_notified(2)
        self.assertEqual(self.last_notified['default'][0].EventType,
                         'MojioWake')
        self.assertEqual(self.last_notified['default'][1].EventType,
                         'IgnitionOn')

        blk.stop()

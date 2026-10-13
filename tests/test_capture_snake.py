import json
from desnivel.cli.capture_snake import Capture, ADDRESS


class MemoryStore:
    def __init__(self):
        self.events = []

    def append(self, address, payload, **details):
        self.events.append((address, payload, details))

    def finish(self, reason):
        pass


def test_capture_uses_storage_interface_and_stops_only_after_play():
    store = MemoryStore()
    capture = Capture(store)
    for playing in (0, 1, 0):
        payload = {'version': 1, 'playing': playing, 'beat': 4.125}
        capture.receive(ADDRESS, json.dumps(payload))
        if not capture.playing_seen:
            assert not capture.finished
    assert capture.finished and capture.count == 3
    assert store.events[-1][1] == payload
    assert all(e[0] == ADDRESS for e in store.events)


def test_capture_keeps_errors_and_malformed_packets_for_diagnosis():
    store = MemoryStore()
    capture = Capture(store)
    capture.receive(ADDRESS, 'not JSON')
    capture.receive(ADDRESS, json.dumps({'version': 1, 'playing': 1, 'error': 'fase assente'}))
    assert capture.count == 2 and not capture.finished
    assert store.events[0][2]['raw_args'] == ['not JSON']
    assert store.events[1][1]['error'] == 'fase assente'
    assert capture.last_status == 'fase assente'


def test_nonfinite_json_is_saved_as_raw_instead_of_invalid_json_numbers():
    store = MemoryStore()
    capture = Capture(store)
    capture.receive(ADDRESS, '{"beat":NaN}')
    assert store.events[0][1] is None
    assert store.events[0][2]['raw_args'] == ['{"beat":NaN}']


def test_keep_open_preserves_stop_and_new_epoch_in_same_capture():
    store = MemoryStore()
    capture = Capture(store, stop_on_transport=False)
    for playing, epoch in [(0, 0), (1, 1), (0, 2), (0, 2), (1, 3), (0, 4)]:
        capture.receive(ADDRESS, json.dumps({'version': 1, 'playing': playing, 'epoch': epoch}))
        assert not capture.finished
    assert capture.count == 6
    assert [event[1]['epoch'] for event in store.events] == [0, 1, 2, 2, 3, 4]
    assert 'Ricevitore aperto' in capture.last_status

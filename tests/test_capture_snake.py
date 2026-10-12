import io
import json
from desnivel.cli.capture_snake import Capture, ADDRESS


def test_capture_preserves_raw_messages_and_stops_only_after_play():
    stream = io.StringIO()
    capture = Capture(stream)
    for playing in (0, 1, 0):
        payload = json.dumps({'version': 1, 'playing': playing, 'beat': 4.125})
        capture.receive(ADDRESS, payload)
        if not capture.playing_seen:
            assert not capture.finished
    rows = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert capture.finished and capture.count == 3
    assert rows[-1]['args'] == [payload]
    assert all(row['address'] == ADDRESS for row in rows)
    assert rows[0]['received_monotonic'] <= rows[-1]['received_monotonic']


def test_capture_keeps_errors_and_malformed_packets_for_diagnosis():
    stream = io.StringIO()
    capture = Capture(stream)
    capture.receive(ADDRESS, 'not JSON')
    capture.receive(ADDRESS, json.dumps({'version': 1, 'playing': 1, 'error': 'fase assente'}))
    assert capture.count == 2 and not capture.finished
    assert json.loads(stream.getvalue().splitlines()[0])['args'] == ['not JSON']
    assert capture.last_status == 'fase assente'

import io
import json
import pytest
from desnivel.sinks.capture_log import JsonlCaptureStore


def test_log_has_session_ordered_events_and_explicit_end():
    stream = io.StringIO()
    ticks = iter([100, 125, 150, 200])
    store = JsonlCaptureStore(stream, {'label': 'prova'}, clock=lambda: next(ticks))
    store.append('/state', {'version': 1, 'beat': 2.5, 'state': {'notes': [60]}})
    store.append('/state', None, raw_args=['broken'], error='invalid JSON')
    store.finish('transport_stop')
    store.finish('transport_stop')
    rows = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert [r['record_type'] for r in rows] == ['session', 'event', 'event', 'end']
    assert len({r['session_id'] for r in rows}) == 1
    assert all(r['schema_version'] == 1 for r in rows)
    assert rows[1]['event_id'] == 1 and rows[2]['event_id'] == 2
    assert rows[1]['elapsed_ns'] == 25 and rows[2]['elapsed_ns'] == 50
    assert rows[1]['payload']['state']['notes'] == [60]
    assert rows[2]['raw_args'] == ['broken']
    assert rows[-1]['event_count'] == 2 and rows[-1]['reason'] == 'transport_stop'
    with pytest.raises(ValueError, match='chiusa'):
        store.append('/state', {})


def test_unfinished_log_preserves_complete_records_without_end():
    stream = io.StringIO()
    store = JsonlCaptureStore(stream, {})
    store.append('/state', {'playing': 1})
    rows = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert [r['record_type'] for r in rows] == ['session', 'event']

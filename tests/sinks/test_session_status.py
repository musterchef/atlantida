import json

from desnivel.sinks.session_status import SessionStatusStore


def test_status_replaces_previous_snapshot_and_keeps_no_temporary_files(tmp_path):
    store = SessionStatusStore(tmp_path / 'session' / 'state.json')
    store.write({'state': 'waiting_for_transport'})
    store.write({'state': 'playing', 'trip': {'progress': .3}})
    assert json.loads(store.path.read_text()) == {'state': 'playing', 'trip': {'progress': .3}}
    assert list(store.path.parent.iterdir()) == [store.path]

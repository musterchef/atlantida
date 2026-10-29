"""Autorizzazione e importazione locale senza alterare i dati del viaggio."""
from io import BytesIO
import json
from types import SimpleNamespace

import pytest

from desnivel.cli import _strava_auth as auth
from desnivel.cli import import_strava as cli


@pytest.mark.parametrize('path', [
    '/callback?state=wrong&code=code&scope=activity:read_all',
    '/other?state=expected&code=code&scope=activity:read_all',
    '/callback?state=expected&error=access_denied',
    '/callback?state=expected&code=code&scope=read',
    '/callback?state=expected&scope=activity:read_all',
    '/callback?state=expected&code=first&code=second&scope=activity:read_all',
])
def test_invalid_callback_cannot_exchange_code(path):
    with pytest.raises(ValueError):
        auth.validate_callback(path, 'expected')


def test_callback_code_requires_matching_state_and_read_scope():
    assert auth.validate_callback('/callback?state=expected&code=code&scope=read,activity:read_all', 'expected') == 'code'


def test_authorization_exchanges_code_without_logging_credentials(monkeypatch, capsys):
    monkeypatch.setattr(auth.secrets, 'token_urlsafe', lambda size: 'expected')

    class Server:
        server_port = 12345

        def __init__(self, address, handler):
            assert address == ('127.0.0.1', 0)
            self.handler = handler

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def handle_request(self):
            request = SimpleNamespace(path='/callback?state=expected&code=temporary&scope=activity:read_all',
                                      send_response=lambda *a: None, send_header=lambda *a: None,
                                      end_headers=lambda: None, wfile=BytesIO())
            self.handler.do_GET(request)

    monkeypatch.setattr(auth, 'HTTPServer', Server)

    def exchange(url, *, form):
        assert url == 'https://www.strava.com/oauth/token'
        assert form == dict(client_id='123', client_secret='hidden', code='temporary', grant_type='authorization_code')
        return {'access_token': 'private-token'}

    monkeypatch.setattr(auth, 'request_json', exchange)
    assert auth.authorize('123', 'hidden') == 'private-token'
    output = capsys.readouterr().out
    assert 'scope=activity%3Aread_all' in output
    assert all(value not in output for value in ('hidden', 'temporary', 'private-token'))


@pytest.fixture
def gpx(tmp_path):
    path = tmp_path/'trip.gpx'
    path.write_text('''<gpx xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
<trkpt lat="42" lon="12"><time>2025-09-20T13:12:22Z</time></trkpt>
<trkpt lat="42.001" lon="12"><time>2025-09-20T13:13:22Z</time></trkpt>
</trkseg></trk></gpx>''')
    return path


def test_import_selects_candidate_and_keeps_raw_snapshot_without_credentials(monkeypatch, tmp_path, gpx):
    original = gpx.read_bytes()
    activity = dict(id=6, name='Trip', start_date='2025-09-20T13:12:00Z', elapsed_time=120, moving_time=100)
    streams = dict(time={'data': [0, 120]}, moving={'data': [False, True]}, latlng={'data': [[42, 12], [42.001, 12]]})
    answers = iter(['123', '6'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(answers))
    monkeypatch.setattr(cli, 'getpass', lambda prompt: 'private-secret')
    monkeypatch.setattr(cli, 'authorize', lambda *args: 'private-token')
    monkeypatch.setattr(cli, 'list_activities', lambda *args: [activity])
    monkeypatch.setattr(cli, 'download_activity', lambda *args: dict(activity=activity, streams=streams))
    output = tmp_path/'snapshot.json'
    assert cli.main(['--gpx', str(gpx), '--output', str(output)]) == 0
    snapshot = json.loads(output.read_text())
    assert snapshot['activity'] == activity
    assert snapshot['streams'] == streams
    assert len(snapshot['source_gpx']['sha256']) == 64
    assert gpx.read_bytes() == original
    assert 'private-' not in output.read_text()


def test_existing_output_is_not_overwritten(tmp_path, gpx):
    output = tmp_path/'snapshot.json'
    output.write_text('keep')
    with pytest.raises(SystemExit):
        cli.main(['--gpx', str(gpx), '--output', str(output)])
    assert output.read_text() == 'keep'


def test_explicit_activity_from_another_day_does_not_create_snapshot(monkeypatch, tmp_path, gpx):
    monkeypatch.setattr('builtins.input', lambda prompt: '123')
    monkeypatch.setattr(cli, 'getpass', lambda prompt: 'secret')
    monkeypatch.setattr(cli, 'authorize', lambda *args: 'token')
    monkeypatch.setattr(cli, 'download_activity', lambda *args: {'activity': dict(
        id=6, start_date='2025-09-21T13:12:00Z', elapsed_time=120)})
    output = tmp_path/'snapshot.json'
    with pytest.raises(SystemExit):
        cli.main(['--gpx', str(gpx), '--activity-id', '6', '--output', str(output)])
    assert not output.exists()

"""Importazione Strava: dati necessari, paginazione ed errori senza segreti."""
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from desnivel.trip import strava


def test_pagination_keeps_all_activity_candidates(monkeypatch):
    calls = []

    def request(url, **kwargs):
        calls.append(url)
        return [{'id': i} for i in range(100)] if len(calls) == 1 else [{'id': 100}]

    monkeypatch.setattr(strava, 'request_json', request)
    assert len(strava.list_activities('secret', 10, 20)) == 101
    assert 'page=2' in calls[-1]
    assert all('secret' not in url for url in calls)


@pytest.mark.parametrize('missing', ['time', 'moving', 'latlng'])
def test_missing_required_stream_is_an_explicit_error(monkeypatch, missing):
    streams = {key: {'data': [0]} for key in ('time', 'moving', 'latlng') if key != missing}
    monkeypatch.setattr(strava, 'request_json', lambda url, **kwargs: streams if '/streams?' in url else {'id': 6})
    with pytest.raises(ValueError, match=missing):
        strava.download_activity('secret', 6)


def test_mismatched_stream_lengths_are_rejected(monkeypatch):
    streams = {'time': {'data': [0, 1]}, 'moving': {'data': [True]}, 'latlng': {'data': [[42, 12], [42, 12]]}}
    monkeypatch.setattr(strava, 'request_json', lambda url, **kwargs: streams if '/streams?' in url else {'id': 6})
    with pytest.raises(ValueError, match='lunghezze differenti'):
        strava.download_activity('secret', 6)


def test_http_error_does_not_expose_credentials_or_response_body(monkeypatch):
    def fail(request, timeout):
        assert timeout == 30
        assert request.get_header('Authorization') == 'Bearer secret-token'
        raise HTTPError(request.full_url, 401, 'secret-message', {}, BytesIO(b'secret-response'))

    monkeypatch.setattr(strava, 'urlopen', fail)
    with pytest.raises(ValueError) as raised:
        strava.request_json('https://www.strava.com/api/v3/athlete', token='secret-token')
    assert '401' in str(raised.value)
    assert 'secret' not in str(raised.value)


def test_token_exchange_uses_post_form_not_query(monkeypatch):
    def respond(request, timeout):
        assert request.get_method() == 'POST'
        assert '?' not in request.full_url
        assert b'client_secret=hidden' in request.data
        return BytesIO(json.dumps({'access_token': 'token'}).encode())

    monkeypatch.setattr(strava, 'urlopen', respond)
    assert strava.request_json('https://www.strava.com/oauth/token', form={'client_secret': 'hidden'}) == {'access_token': 'token'}

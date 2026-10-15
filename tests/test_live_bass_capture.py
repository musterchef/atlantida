from dataclasses import asdict
import json
import pytest
from desnivel.adapters.snake_sequence import Lane, SnakeState
from desnivel.cli.live_bass import main, ADDRESS, PLAN_ADDRESS


def test_capture_records_received_state_and_actual_sent_plans(monkeypatch, tmp_path):
    lane = Lane(1, '16n', 16, 'forwards', .125)
    state = SnakeState(tuple(range(60, 76)), (1,)*16, (64,)*16, (100,)*16,
                       lane, lane, lane, 94, 0)
    snapshot = dict(version=1, source='test', epoch=1, serial=1, playing=1,
                    beat=.125, state=asdict(state))
    sent = []
    handlers = {}

    class Dispatcher:
        def map(self, address, callback):
            handlers[address] = callback

    class Client:
        def __init__(self, *args):
            pass
        def send_message(self, address, payload):
            sent.append((address, json.loads(payload)))

    class Server:
        def __init__(self, *args):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def serve_forever(self):
            handlers[ADDRESS](ADDRESS, json.dumps(snapshot))
            raise KeyboardInterrupt

    monkeypatch.setattr('pythonosc.dispatcher.Dispatcher', Dispatcher)
    monkeypatch.setattr('pythonosc.udp_client.SimpleUDPClient', Client)
    monkeypatch.setattr('pythonosc.osc_server.BlockingOSCUDPServer', Server)
    monkeypatch.setattr('desnivel.cli.live_bass.tempfile.mkdtemp', lambda **kwargs: str(tmp_path))
    assert main(['--capture', '--preset', 'slap', '--density', '1.2']) == 0
    rows = [json.loads(line) for line in (tmp_path/'bass-session.jsonl').read_text().splitlines()]
    settings = rows[0]['metadata']['bass_settings']
    assert settings['density'] == 1.2
    assert settings['min_spacing'] == .5 and settings['mobility'] == .85
    events = [row for row in rows if row['record_type'] == 'event']
    assert events[0]['payload'] == json.loads(json.dumps(snapshot))
    assert [(e['address'], e['payload']) for e in events[1:]] == sent
    assert sent[0][0] == PLAN_ADDRESS and sent[0][1]['start'] == 4
    assert sent[-1][1]['reset'] is True
    assert rows[-1]['reason'] == 'interrupted'


@pytest.mark.parametrize('windows', [0, 1])
def test_live_controls_are_ordered_captured_and_do_not_reset_on_bad_input(monkeypatch, tmp_path, windows):
    from desnivel.cli.live_bass import CONTROL_ADDRESS
    from test_snake_live import snapshot
    handlers = {}
    sent = []
    message = dict(version=1, serial=1, parameters={'density': 1}, transition_windows=windows)
    mobility = dict(version=1, serial=2, parameters={'mobility': .4}, transition_windows=windows)

    class Dispatcher:
        def map(self, address, callback):
            handlers[address] = callback

    class Client:
        def __init__(self, *args):
            pass
        def send_message(self, address, payload):
            sent.append(json.loads(payload))

    class Server:
        def __init__(self, *args):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def serve_forever(self):
            handlers[ADDRESS](ADDRESS, json.dumps(snapshot()))
            assert sent[-1]['phrase']['notes'] == []
            # Un seriale alto ma non valido non deve bloccare i comandi successivi.
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, '{"version":1,"serial":99,"parameters":{"density":NaN}}')
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, b'not JSON')
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, json.dumps(dict(version=1, serial=99, parameters={'density': -1})))
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, json.dumps(message))
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, json.dumps(mobility))
            # Duplicato e comando superato non devono cancellare la destinazione.
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, json.dumps(dict(version=1, serial=2, parameters={'density': 0})))
            handlers[CONTROL_ADDRESS](CONTROL_ADDRESS, json.dumps(dict(version=1, serial=0, parameters={'density': 0})))
            handlers[ADDRESS](ADDRESS, json.dumps(snapshot(2, .375)))
            assert bool(sent[-1]['phrase']['notes']) == (windows == 0)
            handlers[ADDRESS](ADDRESS, json.dumps(snapshot(3, 4.125)))
            assert len(sent[-1]['phrase']['notes']) == 4
            assert not any(plan.get('reset') for plan in sent)
            raise KeyboardInterrupt

    monkeypatch.setattr('pythonosc.dispatcher.Dispatcher', Dispatcher)
    monkeypatch.setattr('pythonosc.udp_client.SimpleUDPClient', Client)
    monkeypatch.setattr('pythonosc.osc_server.BlockingOSCUDPServer', Server)
    monkeypatch.setattr('desnivel.cli.live_bass.tempfile.mkdtemp', lambda **kwargs: str(tmp_path))
    assert main(['--capture', '--density', '0']) == 0
    rows = [json.loads(line) for line in (tmp_path / 'bass-session.jsonl').read_text().splitlines()]
    controls = [row for row in rows if row.get('address') == CONTROL_ADDRESS]
    assert [row['payload'] for row in controls if not row['decode_error']] == [message, mobility]
    assert len([row for row in controls if row['decode_error']]) == 3
    assert rows[0]['metadata']['control_address'] == CONTROL_ADDRESS
    assert sent[-1]['reset'] is True

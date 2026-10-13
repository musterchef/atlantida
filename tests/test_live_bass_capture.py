from dataclasses import asdict
import json
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
    assert main(['--capture']) == 0
    rows = [json.loads(line) for line in (tmp_path/'bass-session.jsonl').read_text().splitlines()]
    events = [row for row in rows if row['record_type'] == 'event']
    assert events[0]['payload'] == json.loads(json.dumps(snapshot))
    assert [(e['address'], e['payload']) for e in events[1:]] == sent
    assert sent[0][0] == PLAN_ADDRESS and sent[0][1]['start'] == 4
    assert sent[-1][1]['reset'] is True
    assert rows[-1]['reason'] == 'interrupted'

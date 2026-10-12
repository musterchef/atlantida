"""Registra gli snapshot OSC di Snake senza modificare Live o generare musica."""
import argparse
import json
from pathlib import Path
import tempfile
import time

ADDRESS = '/desnivel/v1/snake/state'


class Capture:
    def __init__(self, stream):
        self.stream = stream
        self.count = 0
        self.playing_seen = False
        self.finished = False
        self.last_status = None

    def receive(self, address, *values):
        record = {'received_monotonic': time.monotonic(), 'address': address, 'args': values}
        self.stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        self.stream.flush()
        self.count += 1
        try:
            if len(values) != 1 or not isinstance(values[0], str):
                raise ValueError('atteso uno snapshot JSON')
            snapshot = json.loads(values[0])
            if not isinstance(snapshot, dict) or snapshot.get('version') != 1:
                raise ValueError('snapshot non riconosciuto')
            playing = snapshot.get('playing')
            if playing not in (0, 1):
                raise ValueError('stato del trasporto assente')
            if playing:
                self.playing_seen = True
                status = str(snapshot.get('error') or 'Ricezione attiva: registra il MIDI, poi ferma Live.')
            else:
                self.finished = self.playing_seen
                status = 'Stop ricevuto: acquisizione conclusa.' if self.finished else 'Export ricevuto. In attesa di Play.'
        except (ValueError, TypeError) as exc:
            status = 'Messaggio conservato ma non valido: ' + str(exc)
        if status != self.last_status:
            print(status, flush=True)
            self.last_status = status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=9003)
    parser.add_argument('--seconds', type=float, default=180, help='Durata massima, inclusa attesa di Play.')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535 or not 0 < args.seconds < float('inf'):
        parser.error('porta o durata non valida')
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    dispatcher = Dispatcher()
    try:
        server = BlockingOSCUDPServer(('127.0.0.1', args.port), dispatcher)
    except OSError as exc:
        parser.error(f'Porta {args.port} non disponibile: chiudi live_bass o un altro ricevitore. {exc}')
    with server:
        folder = Path(tempfile.mkdtemp(prefix='desnivel-capture-'))
        output = folder / 'snake-state.jsonl'
        with output.open('x') as stream:
            capture = Capture(stream)
            dispatcher.map(ADDRESS, capture.receive)
            server.timeout = 0.25
            deadline = time.monotonic() + args.seconds
            print(f'In ascolto su 127.0.0.1:{args.port}\nFile: {output}', flush=True)
            print('Lascia Export attivo. Registra da 1.1.1 senza loop, poi premi Stop in Live.', flush=True)
            try:
                while not capture.finished and time.monotonic() < deadline:
                    server.handle_request()
            except KeyboardInterrupt:
                pass
        print(f'Salvati {capture.count} messaggi in: {output}', flush=True)
        if not capture.count:
            print('Nessun dato ricevuto: questa acquisizione non è utilizzabile.', flush=True)
            return 1
        if not capture.finished:
            print('Acquisizione interrotta o tempo esaurito; Stop di Live non osservato.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

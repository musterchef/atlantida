"""Registra gli snapshot OSC di Snake senza modificare Live o generare musica."""
import argparse
import json
from pathlib import Path
import tempfile
import time

from desnivel.sinks.capture_log import CaptureStore, JsonlCaptureStore

ADDRESS = '/desnivel/v1/snake/state'


def _reject_constant(value):
    raise ValueError('costante JSON non valida: ' + value)


class Capture:
    def __init__(self, store: CaptureStore, *, stop_on_transport=True):
        self.store = store
        self.stop_on_transport = stop_on_transport
        self.count = 0
        self.playing_seen = False
        self.finished = False
        self.last_status = None

    def receive(self, address, *values):
        snapshot = None
        error = None
        try:
            if len(values) != 1 or not isinstance(values[0], str):
                raise ValueError('atteso uno snapshot JSON')
            snapshot = json.loads(values[0], parse_constant=_reject_constant)
        except (ValueError, TypeError) as exc:
            error = str(exc)
        self.store.append(address, snapshot, raw_args=list(values) if error else None, error=error)
        self.count += 1
        try:
            if error:
                raise ValueError(error)
            if not isinstance(snapshot, dict) or snapshot.get('version') != 1:
                raise ValueError('snapshot non riconosciuto')
            playing = snapshot.get('playing')
            if playing not in (0, 1):
                raise ValueError('stato del trasporto assente')
            if playing:
                self.playing_seen = True
                status = str(snapshot.get('error') or 'Ricezione attiva: registra il MIDI, poi ferma Live.')
            else:
                self.finished = self.playing_seen and self.stop_on_transport
                if self.finished:
                    status = 'Stop ricevuto: acquisizione conclusa.'
                elif self.playing_seen:
                    status = 'Stop ricevuto. Ricevitore aperto: puoi ripartire; Ctrl+C per salvare e chiudere.'
                else:
                    status = 'Export ricevuto. In attesa di Play.'
        except (ValueError, TypeError) as exc:
            status = 'Messaggio conservato ma non valido: ' + str(exc)
        if status != self.last_status:
            print(status, flush=True)
            self.last_status = status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=9003)
    parser.add_argument('--seconds', type=float, default=180, help='Durata massima, inclusa attesa di Play.')
    parser.add_argument('--label', default='', help='Descrizione della prova, salvata nei metadati.')
    parser.add_argument('--keep-open', action='store_true', help='Continua dopo Stop per acquisire anche le ripartenze; Ctrl+C per chiudere.')
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
        with output.open('x', encoding='utf-8') as stream:
            store = JsonlCaptureStore(stream, {
                'producer': 'desnivel.capture_snake', 'label': args.label,
                'host': '127.0.0.1', 'port': args.port,
                'address': ADDRESS, 'max_seconds': args.seconds,
                'stop_on_transport': not args.keep_open,
            })
            capture = Capture(store, stop_on_transport=not args.keep_open)
            dispatcher.map(ADDRESS, capture.receive)
            server.timeout = 0.25
            deadline = time.monotonic() + args.seconds
            print(f'In ascolto su 127.0.0.1:{args.port}\nFile: {output}', flush=True)
            print('Lascia Export attivo. Registra da 1.1.1 senza loop, poi premi Stop in Live.', flush=True)
            if args.keep_open:
                print('Modalità ripartenza: resta aperto dopo Stop. Ctrl+C per salvare e chiudere.', flush=True)
            reason = 'error'
            try:
                while not capture.finished and time.monotonic() < deadline:
                    server.handle_request()
                reason = 'transport_stop' if capture.finished else 'timeout'
            except KeyboardInterrupt:
                reason = 'interrupted'
            finally:
                store.finish(reason)
        print(f'Salvati {capture.count} messaggi in: {output}', flush=True)
        if not capture.count:
            print('Nessun dato ricevuto: questa acquisizione non è utilizzabile.', flush=True)
            return 1
        if not capture.finished:
            if args.keep_open:
                print('Acquisizione chiusa: ' + ('Ctrl+C.' if reason == 'interrupted' else 'tempo esaurito.'), flush=True)
            else:
                print('Acquisizione interrotta o tempo esaurito; Stop di Live non osservato.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Ascolta lo stato Snake e prepara il basso sul trasporto di Live."""
import argparse
from contextlib import ExitStack
from dataclasses import asdict
import json
from pathlib import Path
import tempfile

from desnivel.sinks.capture_log import JsonlCaptureStore

from desnivel.adapters.snake_live import BassSession
from desnivel.music.bass.control import BassControl
from desnivel.cli.bass_options import add_bass_options, bass_settings


ADDRESS = '/desnivel/v1/snake/state'
PLAN_ADDRESS = '/desnivel/v1/player/bass/plan'
CONTROL_ADDRESS = '/desnivel/v1/bass/control'


def _reject_constant(value):
    raise ValueError('costante JSON non valida: ' + value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen-port',type=int,default=9003)
    parser.add_argument('--player-port',type=int,default=9004)
    parser.add_argument('--window',type=float,default=4)
    parser.add_argument('--lead',type=float,default=1)
    add_bass_options(parser)
    parser.add_argument('--capture', action='store_true', help='Salva stati ricevuti e piani inviati in JSONL fuori dalla repository.')
    args = parser.parse_args(argv)
    try:
        if any(not 1<=p<=65535 for p in (args.listen_port,args.player_port)):
            raise ValueError('porta fuori intervallo')
        settings = bass_settings(args)
        session = BassSession(settings, args.window, args.lead)
    except ValueError as exc:
        parser.error(str(exc))
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    from pythonosc.udp_client import SimpleUDPClient
    client=SimpleUDPClient('127.0.0.1',args.player_port)
    dispatcher=Dispatcher()
    last_status=[None]
    store = None
    last_control_serial = -1
    def send_plan(plan):
        payload = json.dumps(plan, separators=(',', ':'))
        if len(payload.encode()) > 60000:
            raise ValueError('piano troppo grande per UDP: ridurre --window')
        client.send_message(PLAN_ADDRESS, payload)
        if store is not None:
            store.append(PLAN_ADDRESS, plan)
    def report(text):
        if text!=last_status[0]:
            print(text,flush=True);last_status[0]=text
    def receive(address,*values):
        try:
            if len(values)!=1 or not isinstance(values[0],str):
                raise ValueError('snapshot JSON mancante')
            snapshot=json.loads(values[0])
            if store is not None:
                store.append(address, snapshot)
            plan=session.update(snapshot)
            if plan is None:return
            send_plan(plan)
            if plan.get('reset'):
                report(snapshot.get('error','Live fermo: basso in attesa'))
            else:
                report(f"Basso pronto dal beat {plan['start']:g}: {len(plan['phrase']['notes'])} note")
        except (KeyError,ValueError,TypeError,OverflowError,OSError) as exc:
            # Non lasciare suonare un piano vecchio dopo uno stato non prevedibile.
            if session.session:
                send_plan({'version':1,'session':session.session,'serial':session.serial,'reset':True})
            report(f'Stato non utilizzabile: {exc}')
    dispatcher.map(ADDRESS,receive)

    def receive_control(address, *values):
        nonlocal last_control_serial
        try:
            if len(values) != 1 or not isinstance(values[0], str):
                raise ValueError('atteso un controllo basso JSON')
            message = json.loads(values[0], parse_constant=_reject_constant)
            control = BassControl.from_dict(message, session.target_settings)
            if control.serial <= last_control_serial:
                report(f'Controllo basso {control.serial} ignorato: duplicato o superato')
                return
            session.set_settings(control.settings, control.transition_windows)
            last_control_serial = control.serial
        except (ValueError, TypeError, OverflowError) as exc:
            if store is not None:
                raw_args = [value if isinstance(value, str) else repr(value) for value in values]
                store.append(address, None, raw_args=raw_args, error=str(exc))
            report(f'Controllo basso rifiutato: {exc}')
            return
        if store is not None:
            store.append(address, message)
        report(f'Controllo basso {control.serial} accettato: '
               f'{", ".join(message["parameters"])}; transizione {control.transition_windows} finestre')

    dispatcher.map(CONTROL_ADDRESS, receive_control)
    with ExitStack() as resources:
        server = resources.enter_context(BlockingOSCUDPServer(('127.0.0.1',args.listen_port),dispatcher))
        if args.capture:
            output = Path(tempfile.mkdtemp(prefix='desnivel-bass-')) / 'bass-session.jsonl'
            stream = resources.enter_context(output.open('x', encoding='utf-8'))
            store = JsonlCaptureStore(stream, {'producer': 'desnivel.live_bass', 'settings': vars(args),
                'bass_settings': asdict(settings),
                'control_address': CONTROL_ADDRESS,
                'input_address': ADDRESS, 'output_address': PLAN_ADDRESS})
            print(f'Acquisizione: {output}', flush=True)
        reason = 'error'
        try:
            print(f'In ascolto Snake sulla porta {args.listen_port}; player {args.player_port}; preset {args.strategy}',flush=True)
            print(f'Controlli basso sulla stessa porta: {CONTROL_ADDRESS}', flush=True)
            server.serve_forever()
        except KeyboardInterrupt:
            reason = 'interrupted'
            if session.session:
                send_plan({'version':1,'session':session.session,'serial':session.serial+1,'reset':True})
        finally:
            if store is not None:
                store.finish(reason)
    return 0


if __name__=='__main__':
    raise SystemExit(main())

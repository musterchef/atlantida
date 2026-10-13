"""Ascolta lo stato Snake e prepara il basso sul trasporto di Live."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile

from desnivel.sinks.capture_log import JsonlCaptureStore

from desnivel.adapters.snake_live import BassSession
from desnivel.bass import BassSettings


ADDRESS = '/desnivel/v1/snake/state'
PLAN_ADDRESS = '/desnivel/v1/player/bass/plan'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen-port',type=int,default=9003)
    parser.add_argument('--player-port',type=int,default=9004)
    parser.add_argument('--window',type=float,default=4)
    parser.add_argument('--lead',type=float,default=1)
    parser.add_argument('--lowest',type=int,default=28)
    parser.add_argument('--highest',type=int,default=47)
    parser.add_argument('--min-spacing',type=float,default=1)
    parser.add_argument('--articulation',type=float,default=.9)
    parser.add_argument('--velocity-ratio',type=float,default=.9)
    parser.add_argument('--strategy', choices=['responsive','follow','slap'], default='responsive')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--variation-period', type=int, default=4)
    parser.add_argument('--max-hold', type=float, default=2)
    parser.add_argument('--grid', type=float, default=.5)
    parser.add_argument('--capture', action='store_true', help='Salva stati ricevuti e piani inviati in JSONL fuori dalla repository.')
    args = parser.parse_args(argv)
    try:
        if any(not 1<=p<=65535 for p in (args.listen_port,args.player_port)):
            raise ValueError('porta fuori intervallo')
        session=BassSession(BassSettings(args.lowest,args.highest,args.min_spacing,
                                        args.articulation,args.velocity_ratio,
                                        args.strategy,args.seed,args.variation_period,args.max_hold,args.grid),args.window,args.lead)
    except ValueError as exc:
        parser.error(str(exc))
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    from pythonosc.udp_client import SimpleUDPClient
    client=SimpleUDPClient('127.0.0.1',args.player_port)
    dispatcher=Dispatcher()
    last_status=[None]
    store = None
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
    with ExitStack() as resources:
        server = resources.enter_context(BlockingOSCUDPServer(('127.0.0.1',args.listen_port),dispatcher))
        if args.capture:
            output = Path(tempfile.mkdtemp(prefix='desnivel-bass-')) / 'bass-session.jsonl'
            stream = resources.enter_context(output.open('x', encoding='utf-8'))
            store = JsonlCaptureStore(stream, {'producer': 'desnivel.live_bass', 'settings': vars(args),
                'input_address': ADDRESS, 'output_address': PLAN_ADDRESS})
            print(f'Acquisizione: {output}', flush=True)
        reason = 'error'
        try:
            print(f'In ascolto Snake sulla porta {args.listen_port}; player {args.player_port}; strategia {args.strategy}',flush=True)
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

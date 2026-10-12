#!/bin/bash
# Configurazione ripetibile per confrontare Snake con il MIDI registrato.
cd -- "$(dirname -- "$0")/.." || exit 1
if [[ ! -x .venv/bin/python ]]; then
    echo "Ambiente Python assente: manca .venv/bin/python nel progetto."
    read -r -p "Premi Invio per chiudere. "
    exit 1
fi
./.venv/bin/python - "$@" <<'PY'
import argparse
import time
from desnivel.adapters import snake
from desnivel.sinks.osc import UdpOscClient

parser = argparse.ArgumentParser(description='Imposta la sequenza di riferimento Snake.')
parser.add_argument('--dry-run', action='store_true', help='Mostra i valori senza inviarli.')
args = parser.parse_args()
messages = [('gate_shape', 0), ('Fondamental', 0), ('Swing', 0)]
messages += snake.note_messages(snake.scale_notes('chromatic', 36))
messages += snake.gate_messages([1] * 16)
messages += [(snake.param_name('Velocity', i), 64) for i in range(1, 17)]
messages += [('Length_Min_ms', 100), ('Length_Max_ms', 100)]
client = None if args.dry_run else UdpOscClient('127.0.0.1', 9001)
for name, value in messages:
    print(f'{name} = {value:g}')
    if client:
        client.send_message(snake.ADDRESS, [name, value])
        time.sleep(0.02)
print('Anteprima: nessun invio.' if args.dry_run else 'Invio completato; OSC non conferma l’applicazione in Live.')
print('16 valori Note ascendenti 36–51; Chromatic, fondamentale C; tutti i gate attivi; velocity 64; durata 100 ms.')
print('Notes, Gates e Velocities: verificare manualmente Speed 16n, Steps 16, Direction forwards e Shift 1.')
print('La Shape Notes resta quella corrente. BPM, Custom e synth non vengono modificati.')
PY
result=$?
if [[ $result -ne 0 ]]; then
    echo "Comando terminato con codice $result. Leggi il messaggio sopra."
fi
read -r -p "Premi Invio per chiudere. "
exit "$result"

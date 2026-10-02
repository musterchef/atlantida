# Passaggio di sessione

Aggiornato: 2026-10-02 (fine sessione). Per Codex, Copilot e chi riprende il lavoro.

## Obiettivo

Trasformare un viaggio GPX in musica. Primo esperimento con MDD Snake 3.2.3 in Ableton; deve essere possibile aggiungere altri adattatori senza cambiare il producer o le regole musicali.

## Decisioni

`GPX → dati agnostici → motore musicale Python → adattatori → strumenti`

- Python interpreta i dati con regole configurabili e produce decisioni musicali indipendenti dallo strumento.
- Ogni adattatore gestisce nomi, range e protocollo della propria destinazione.
- Per Snake: comandi OSC → piccola patch M4L → parametri del device.
- Live/Snake esegue il ritmo. Velocità del replay e BPM sono indipendenti.
- Niente ID Live hardcoded, regole Snake nel producer o framework generico anticipato.
- Conservare le altre implementazioni: archiviazione documentale non significa cancellazione del codice.

## Cosa funziona

Verificato dall'utente in Live 12.3.5 con MDD Snake 3.2.3, traccia 2.

- **Metriche:** `desnivel-stream-metrics`, sei metriche neutre, OSC `/desnivel/v1/trip/metric/<nome> elapsed_s value`, 1 Hz nel tempo del viaggio, porta `9000`. Il device mostra tempo e quota.
- **Controllo per nome:** `/desnivel/v1/control/snake/set <nome> <valore>`, porta `9001`. Python non conosce ID Live: li risolve M4L.
- **Gate:** `Gate_01..16`, valori 0/1, griglia 4x4 per righe, `Gate_01` in alto a sinistra (provato con una diagonale).
- **Note:** `Note_01..16`, range 0–83. Snake quantizza i valori sulla propria scala; con `Scales = 0` (Chromatic) restano quelli inviati, verificato ascoltando. Le scale sono calcolate in Python; l'adattatore invia `Scales = 0` prima delle note.
- Il valore è limitato al range letto da Live.

Parametri di Snake (152 in totale, letti con `dump`):

| Gruppo | Nomi | Range | Stato |
|---|---|---|---|
| Note | `Note_01..16` | 0–83 | provato |
| Gate | `Gate_01..16` | 0–1, a scalini | provato |
| Velocity | `Velocity_01..16` | 0–127 | non provato |
| Scala | `Scales` | 0–36 (0 Chromatic, 1 Major, 36 User) | provato con 0 |
| Altri unici | `Fondamental` 0–11, `MidiInMode`, `Random All`, `Reset All`, `Swing` 0–100 | | non provati |
| Ambigui | `Custom_xx`, `Steps`, `Shapes`, `Shift`, `Random`, `Reset`, `Speed`, `Direction` | | compaiono più volte: il JS li ignora |

Per usare i parametri ambigui serve un'altra strategia (per indice o per posizione); non decisa.

## Struttura del codice

```text
Python: decisione musicale
  → src/desnivel/adapters/snake.py   nomi, gate, scale; funzioni pure, nessuna rete
  → src/desnivel/cli/snake_pattern.py  invio OSC (--gates, --gates-random, --scale, --root, --dry-run)
  → OSC 9001 → m4l/desnivel-bridge.amxd → m4l/desnivel_snake_params.js → parametro Live
```

- Device: `udpreceive 9001` → `route /desnivel/v1/control/snake/set` → `prepend set` → `js desnivel_snake_params.js`. Ha anche ricezione metriche su 9000 e una catena `live.path`/`live.object` di diagnostica sul parametro selezionato.
- JS: messaggi `dump` (elenca parametri), `refresh` (rilegge l'indice), `set <nome> <valore>`, `get <nome>`. Cerca il device con "snake" nel nome.
- `src/desnivel/cli/snake_test.py`: invia un solo parametro. `tests/test_snake_adapter.py`: 5 test sull'adattatore.
- Il `.amxd` e il `.js` vanno tenuti insieme nella cartella `~/Music/Ableton/User Library/Presets/Audio Effects/Max Audio Effect/`. Dopo aver modificato il `.js`, ricopiarlo lì e ricaricare il device.

## Comandi per ripartire

```sh
source .venv/bin/activate
python -m desnivel.cli.snake_pattern --gates "1000 0100 0010 0001"
python -m desnivel.cli.snake_pattern --gates-random 0.5 --seed 7
python -m desnivel.cli.snake_pattern --scale minor --root 36
python -m desnivel.cli.snake_test --param Velocity_01 --value 100
```

Scale in Python: chromatic, major, minor, dorian, phrygian, lydian, mixolydian, pentatonic_major, pentatonic_minor, blues. Snake ne ha 37 e può aggiungerne: sono due elenchi separati.

## Problemi noti

- `live.remote~` con ID assegnato ha mandato in crash Live 12.3.5: non usarlo.
- Console Max `live.object ... has no attribute 'Note_03'`: `prepend set` è ancora collegato al vecchio `live.object`; deve andare solo al `js`.
- `js: findSnake is not a function`: il `.js` copiato è incompleto o vecchio.
- Un solo receiver per porta (9000 metriche, 9001 controllo).

## File da leggere

- [Regole di scrittura](AGENTS.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)
- [Guida Snake](INTEGRAZIONE-SNAKE.md)
- `src/desnivel/trip_metrics.py`, `src/desnivel/cli/stream_metrics.py`: metriche neutre e publisher.
- File della sezione "Struttura del codice".

## Non verificato

- Velocity, valori fuori range, `Fondamental` e altri parametri unici.
- Corrispondenza esatta tra `Note_xx` e nota MIDI emessa (assunto: semitoni con Chromatic).
- Associazione dei parametri dopo riapertura del set o spostamento di Snake (il JS indicizza al primo uso; `refresh` rilegge).
- Comportamento con più istanze di Snake (usa la prima trovata).

## Prossimi passi

1. **Velocity:** `snake_test --param Velocity_01 --value 100`, poi estendere l'adattatore come per le note.
2. **Prima regola musicale** alimentata dalle metriche, con output indipendente da Snake: compilare la scheda in [INTEGRAZIONE-SNAKE.md](INTEGRAZIONE-SNAKE.md). Per esempio quota → scala/densità dei gate. Il riarmo di soglie va deciso (attraversamento contro permanenza).
3. **Motore musicale** separato dall'adattatore, con configurazione dei parametri.
4. Poi: timing a battuta/step, altri parametri, secondo adattatore.

## Ambiente e cautele

```sh
source .venv/bin/activate
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
```

Destinazione iniziale: `127.0.0.1:9000`. Tenere un solo receiver su quella porta.

Leggere `git status` prima di intervenire; non ripristinare o cancellare modifiche altrui. Vecchia documentazione in `doc/archivio/`, vecchio generatore TD/audio in `old/td_audio/`.

## Metodo di lavoro

L'utente vuole scrivere parte del codice, usando autocomplete e aiuto mirato. Risposte e documentazione brevi, chiare, senza cronache o parentesi difensive. Leggere solo i file necessari. Aggiornare la documentazione quando cambia una decisione.

A fine sessione aggiornare questo file con: ultimo risultato verificato, file modificati, eventuale problema e prossimo passo. Distinguere sempre prove eseguite da ipotesi.

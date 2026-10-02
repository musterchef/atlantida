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

- `desnivel-stream-metrics`: sei metriche neutre, OSC `/desnivel/v1/trip/metric/<nome> elapsed_s value`, 1 Hz nel tempo del viaggio.
- Ricezione di quota e tempo in Max e nella patch inserita in Ableton, verificata dall'utente.
- Selezione parametro: messaggio `path live_set view selected_parameter` → `live.path` → ingresso destro di `live.object`.
- Letture `get name`, `get min`, `get max`, `get value` all'ingresso sinistro di `live.object`.
- `Note_01`: range osservato 0–83. `set value 12` cambia la manopola.
- Mappabilità degli altri controlli confermata dall'utente; gate, velocity e pattern completi non ancora provati via API.

L'assegnazione dell'ID a `live.remote~` ha causato crash di Live 12.3.5. Usare il percorso verificato con `live.object`; causa del crash non identificata.

## File da leggere

- [Regole di scrittura](AGENTS.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)
- [Guida Snake](INTEGRAZIONE-SNAKE.md)
- `src/desnivel/trip_metrics.py`: dati neutri.
- `src/desnivel/cli/stream_metrics.py`: avvio del publisher.
- `src/desnivel/adapters/snake.py`, `src/desnivel/cli/snake_pattern.py`: adattatore Snake e comando.
- `m4l/desnivel-bridge.amxd` (device funzionante) e `m4l/desnivel_snake_params.js` (da tenere nella stessa cartella del device). `m4l/desnivel_snake_bridge.maxpat` è il receiver iniziale, solo riferimento.

Il device funzionante è `m4l/desnivel-bridge.amxd`; il `.maxpat` iniziale resta come riferimento.

## Ultimo risultato verificato

Controllo di Snake per nome: Python → OSC → M4L → parametro.

- Comando: `/desnivel/v1/control/snake/set <nome> <valore>`, porta `9001` (le metriche usano `9000`).
- Device `m4l/desnivel-bridge.amxd`: `udpreceive 9001` → `route` → `prepend set` → `js desnivel_snake_params.js`. Il JS trova Snake, indicizza i parametri a nome univoco (`Note_xx`, `Gate_xx`, `Velocity_xx`, `Scales`) e limita i valori al range. Messaggi JS: `dump`, `refresh`, `set`, `get`. Il `.js` va copiato accanto al device.
- Gate: `Gate_01..16`, 0/1, griglia 4x4 per righe con `Gate_01` in alto a sinistra (verificato con una diagonale).
- Note: Snake quantizza `Note_xx` sulla sua scala; con `Scales = 0` (Chromatic) i valori restano quelli inviati (verificato ascoltando). L'adattatore invia `Scales = 0` prima delle note e calcola le scale in Python.
- File: `src/desnivel/adapters/snake.py` (nomi, gate, scale, funzioni pure), `src/desnivel/cli/snake_pattern.py` (`--gates`, `--gates-random`, `--scale`, `--root`, `--dry-run`), `src/desnivel/cli/snake_test.py` (un parametro), `tests/test_snake_adapter.py`.

Comandi per ripartire:

```sh
source .venv/bin/activate
python -m desnivel.cli.snake_pattern --gates "1000 0100 0010 0001"
python -m desnivel.cli.snake_pattern --scale minor --root 36
python -m desnivel.cli.snake_test --param Velocity_01 --value 100
```

Il device `.amxd` va copiato da `~/Music/Ableton/User Library/Presets/Audio Effects/Max Audio Effect/` insieme al `.js`; sulla traccia selezionare Snake non serve, il JS lo trova da solo (cerca "snake" nel nome del device). Errore visto: se la console Max mostra `live.object ... has no attribute 'Note_03'`, `prepend set` è ancora collegato al vecchio `live.object`.

Non verificato: velocity, valori fuori range, corrispondenza esatta note MIDI emesse, associazione dopo riapertura del set.

## Prossimo passo

Provare le velocity con lo stesso adattatore, poi una regola musicale Python alimentata dalle metriche (scheda in [INTEGRAZIONE-SNAKE.md](INTEGRAZIONE-SNAKE.md)).

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

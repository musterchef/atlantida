# Passaggio di sessione

Aggiornato: 2026-10-02. Per Codex, Copilot e chi riprende il lavoro.

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
- `m4l/desnivel_snake_bridge.maxpat`: receiver iniziale, senza le modifiche manuali fatte in Live.

Il device funzionante è `m4l/desnivel-bridge.amxd`; il `.maxpat` iniziale resta come riferimento.

## Ultimo risultato verificato

Python → OSC → M4L → `Note_01` funziona: `python -m desnivel.cli.snake_test --value 12` cambia la manopola.

- Comando: `/desnivel/v1/control/snake/note_01 <float>`, porta `9001` (le metriche usano `9000`).
- Device: `m4l/desnivel-bridge.amxd`: `udpreceive 9001` → `route` → `prepend set value` → `live.object`. Prima va selezionata `Note_01` con il messaggio `path live_set view selected_parameter`.
- Script: `src/desnivel/cli/snake_test.py`, invio di un valore di prova.

Non ancora verificato: lettura del valore dopo `set`, valori fuori 0–83, corrispondenza con le note MIDI emesse, associazione dopo riapertura del set.

## Prossimo passo

Una sola regola musicale Python alimentata dalle metriche, con output indipendente da Snake, e un adattatore che la traduca nel comando `note_01`. Compilare prima la scheda in [INTEGRAZIONE-SNAKE.md](INTEGRAZIONE-SNAKE.md).

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

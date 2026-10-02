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

Il device funzionante con `live.object` va ancora salvato nel repository dall'utente. Non sovrascriverlo con il `.maxpat` iniziale.

## Prossima prova consigliata

Prima verificare il tratto Python → OSC → M4L → Snake con un solo valore di controllo, senza aggiungere subito soglie geografiche.

1. Salvare nel progetto il device M4L funzionante.
2. Definire un comando OSC minimo per un controllo associato, su una porta distinta dal receiver delle metriche. Documentare indirizzo, argomenti e range; non sono ancora definiti.
3. Implementare nell'adattatore Python l'invio di un valore di prova configurabile.
4. Ricevere il comando in M4L e applicarlo tramite `live.object`.
5. Verificare che il parametro cambi e che la lettura restituisca il valore richiesto.

Questo prova il trasporto dell'adattatore. Poi aggiungere una sola regola musicale Python alimentata dalle metriche, con output indipendente da Snake. Non assumere che 0–83 corrisponda direttamente alle note MIDI emesse: questa conversione va verificata nell'adattatore.

Nessun motore musicale separato, protocollo di controllo o nuovo adattatore è già implementato. La richiesta attuale è preparare il passaggio di sessione e scegliere il primo test.

## Ambiente e cautele

```sh
source .venv/bin/activate
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
```

Destinazione iniziale: `127.0.0.1:9000`. Tenere un solo receiver su quella porta.

Il working tree contiene molte modifiche non committate: documenti riordinati, file archiviati e patch iniziale. Leggere `git status` prima di intervenire; non ripristinare o cancellare modifiche altrui. Vecchia documentazione in `doc/archivio/`, vecchio generatore TD/audio in `old/td_audio/`.

## Metodo di lavoro

L'utente vuole scrivere parte del codice, usando autocomplete e aiuto mirato. Risposte e documentazione brevi, chiare, senza cronache o parentesi difensive. Leggere solo i file necessari. Aggiornare la documentazione quando cambia una decisione.

A fine sessione aggiornare questo file con: ultimo risultato verificato, file modificati, eventuale problema e prossimo passo. Distinguere sempre prove eseguite da ipotesi.

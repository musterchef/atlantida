# Export Snake

Export invia lo stato del sequencer a Python. L'adattatore usa stato e fase per prevedere una frase musicale.

## Messaggi

UDP locale, porta predefinita 9003, indirizzo `/desnivel/v1/snake/state`. L'argomento OSC è una stringa JSON.

| Campo | Contenuto |
|---|---|
| `version` | 1. |
| `source`, `serial` | Istanza del JS e contatore crescente. |
| `epoch` | Incrementa ai cambi Play/Stop e quando il trasporto torna indietro. |
| `beat`, `playing` | Posizione in semiminime (tick / 480) e stato Play/Stop. |
| `state` | Stato musicale valido durante Play. |
| `error` | Errore di lettura, in alternativa a `state`. |

`state` contiene 16 valori per `notes`, `gates`, `velocities` e `lengths_ms`, oltre a `bpm`, `swing`, `midi_offset` e ai tre banchi `notes_lane`, `gates_lane`, `velocities_lane`. Ogni banco descrive Shape, Speed, Steps, Direction e `phase_beats`.

Le note sono altezze MIDI già quantizzate, con `midi_offset: 0`. Shape usa ID 1–14, ottenuti dai valori Live 0–13 aggiungendo 1. Steps indica le posizioni eseguite del percorso.

Le durate per cella Notes sono calcolate in millisecondi:

```text
min(Min, Max) + valore_cella / 127 × abs(Max − Min)
```

Il JS legge gli avanzamenti dei banchi con `when` e li associa al trasporto. `qmetro 125` campiona nominalmente ogni 125 ms; la cadenza effettiva dipende dallo scheduler.

## Previsione

`snake_sequence.predict` ricostruisce gli attacchi Gates e legge le celle correnti di Notes, Velocities e Length. Un gate spento produce silenzio; i clock continuano. Il riattacco della stessa altezza chiude la nota precedente. Le code sono troncate al bordo della finestra.

La fase viene ricostruita dall'indice nativo e dal tempo dall'ultimo avanzamento; in backwards l'indice è convertito nel percorso inverso. Fasi assenti, future o più vecchie dell'intervallo del banco più 20 tick sono rifiutate.

## Errori e limiti attuali

- Previsione con stato e BPM costanti nella finestra, Direction forwards/backwards, Shift 1 e Swing 0.
- Le note iniziate prima della finestra e i cambi futuri non sono ricostruiti.
- A Stop si cancellano le fasi e si inviano metadati senza `state`. Servono nuovi avanzamenti alla ripartenza.
- `epoch` non rileva tutti i salti in avanti. I cambi dei parametri possono produrre letture intermedie.
- Usare una sola istanza Export. Un cambio sorgente richiede il riavvio del ricevitore live.
- UDP può perdere messaggi. Spegnere Export interrompe gli invii; il ricevitore live non ha un timeout dedicato.

## Acquisizione

Acquisizione e accompagnamento live usano la stessa porta: avviare un solo ricevitore alla volta.

- `05 - Acquisisci Export Snake.command`: salva `snake-state.jsonl`; attende Play e termina allo Stop successivo. Limite 180 secondi, inclusa l'attesa.
- `06 - Export stop e ripartenza.command`: conserva più avvii e stop nella stessa sessione, con limite 600 secondi. Chiudere con Ctrl+C.
- `07 - Basso e acquisizione.command`: esegue l'accompagnamento e salva stati e piani in `bass-session.jsonl`. [Preparazione dei device](PLAYER-M4L.md#basso-collegato-a-snake).

I file sono creati in una cartella temporanea esterna alla repository, mostrata nel terminale. Ctrl+C conserva i dati ricevuti. In alternativa al launcher 05:

```sh
python -m desnivel.cli.capture_snake --seconds 180 --label "prova Export"
```

Per confrontare previsione ed esecuzione, registrare il MIDI da 1.1.1 senza loop. Conservare il silenzio iniziale, BPM, posizione della clip e acquisizione della stessa sessione. Per Stop/ripartenza esportare la prima clip prima di tornare a 1.1.1 e registrare la seconda, mantenendo aperto il launcher 06 o 07.

## Archivio JSONL

`JsonlCaptureStore` usa `schema_version: 1` e `session_id` UUID.

| Riga | Campi |
|---|---|
| `session` | `started_at` UTC e metadati del ricevitore. |
| `event` | `event_id`, `elapsed_ns`, `address`, `payload`, `raw_args`, `decode_error`. |
| `end` | `elapsed_ns`, `event_count`, `reason`: `transport_stop`, `timeout`, `interrupted` o `error`. |

`payload` conserva il messaggio decodificato. Gli errori conservano gli argomenti originali. `elapsed_ns` misura l'arrivo al processo; il confronto musicale usa il beat dello snapshot. Ogni riga è sottoposta a flush, senza fsync. Una riga finale troncata o l'assenza di `end` indica un'acquisizione incompleta.

## Verifiche

Registrazioni a 94 BPM: 85 snapshot, 585 confronti su 60 note; attacchi, altezze e velocity coincidenti, durate entro un tick MIDI a 96 PPQ. Provati clock indipendenti, Notes con cinque Steps forwards/backwards e riattacchi con Length 265 ms. Escluse le note ai bordi della registrazione non coperte dagli snapshot.

Tre registrazioni dell'accompagnamento: 31/31 note compatibili con i piani e 129/130 note del sequencer compatibili con gli stati. La prima nota precede il primo snapshot. Le origini delle clip sono dedotte dal confronto, non registrate nei MIDI.

## Piano di lavoro

Da verificare: Stop/ripartenza, salti e loop, cambi di parametri durante Play, interruzione Export e ricaricamento del device.

## Sorgenti

Builder: `tools/build_live_bass.py`. Telemetria: `m4l/desnivel_snake_state.js`. Previsione e sessione: `adapters/snake_sequence.py`, `adapters/snake_live.py`. Acquisizione: `cli/capture_snake.py`, `sinks/capture_log.py`.

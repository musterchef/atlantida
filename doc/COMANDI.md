# Comandi

## Avvio con doppio clic

La cartella [comandi](../comandi/) contiene launcher macOS `.command` per impostare la Shape dei Gates a 0 o 13 e avviare Firenze–San Gimignano a 150×. Usano automaticamente `.venv` del progetto. Tenere la cartella dentro il progetto.

Aprire il Set funzionante con Snake e bridge; per ascoltare, avviare il trasporto Live. Eseguire un solo viaggio alla volta; Ctrl+C interrompe il replay e lascia a Snake l’ultimo pattern. Non serve `stream_metrics`.

## Sequenza di riferimento Snake

Il launcher `04 - Snake - sequenza di riferimento.command` imposta 16 valori Note distinti da 36 a 51, scala Chromatic, fondamentale C, gate tutti attivi, velocity 64, Swing 0 e Min/Max Length a 100 ms. Imposta Gates Shape a 0 e lascia invariata Notes Shape. Serve al confronto con una registrazione MIDI; nella configurazione verificata i valori 36–51 producono le altezze MIDI 60–75.

Fermare il replay del viaggio prima dell’invio. Verificare manualmente, nei banchi Notes, Gates e Velocities: Speed 16n, Steps 16, Direction forwards e Shift 1. Il launcher non modifica BPM, Custom o synth. L’invio OSC non conferma l’applicazione dei valori in Live.

Per controllare i messaggi senza inviarli:

```sh
bash 'comandi/04 - Snake - sequenza di riferimento.command' --dry-run
```

## Ambiente di sviluppo

Creare l’ambiente e installare il pacchetto dalla radice del progetto:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Le dipendenze correnti sono definite in `pyproject.toml`.

## Preparare il terminale

Dalla cartella del progetto:

```sh
source .venv/bin/activate
```

## Leggere un viaggio

Mostrare un campione delle metriche senza inviarle:

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --dry-run
```

Inviare le metriche via OSC:

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
```

| Opzione | Effetto |
|---|---|
| `--speed 30` | Riproduce il viaggio a velocità 30×. |
| `--loop` | Ripete il viaggio fino a Ctrl+C. |
| `--osc-host` | Destinatario; predefinito `127.0.0.1`. |
| `--osc-port` | Porta; predefinita `9000`. |

I messaggi contengono tempo e misure del viaggio, indipendenti dallo strumento musicale. Il formato è descritto nel [contratto dati](CONTRATTO-DATI-VIAGGIO.md).

## Provare Snake

La [guida Snake](INTEGRAZIONE-SNAKE.md) descrive la ricezione in Max e il controllo manuale di un parametro in Live.

Prima prova dal viaggio: [quota e pattern](TEST-VIAGGIO-SNAKE.md).

```sh
python -m desnivel.cli.trip_music --gpx gpx/tappa04_Levanto_La_Spezia.gpx --rules presets/quota.json --speed 50
```

## Eseguire i test

```sh
pytest -q
```

Per verificare anche gli script Max con Node.js:

```sh
node tests/js/phrase_player.cjs
node tests/js/snake_params.cjs
node tests/js/snake_state.cjs
node tests/js/transport_player.cjs
```

La pipeline precedente è raccolta in [archivio/](../archivio/README.md), esclusa dall’installazione e dalla suite corrente. I [comandi storici](archivio/COMANDI-PROTOTIPO.md) richiedono il ripristino del relativo codice.

## Preset del viaggio

Disponibili movimento, sforzo e misto, con percorso armonico per tappa. [Comandi e configurazione](TEST-PRESET-MUSICALI.md). Confermati dall’utente i due launcher Shape e il replay Firenze a 150×. Gli altri preset restano da valutare all’ascolto.

## Inviare una frase al player

```sh
python -m desnivel.cli.send_phrase --phrase presets/phrases/bass_sustained.json --voice bass
```

Richiede il [player M4L](PLAYER-M4L.md); `--dry-run` prova il formato senza rete.

## Basso da Snake

Con i due device descritti in [Player M4L](PLAYER-M4L.md#basso-collegato-a-snake) e Export attivo:

```sh
python -m desnivel.cli.live_bass
```

Il comando resta in ascolto e prepara le frasi future. Non richiede `stream_metrics`; il replay del viaggio può continuare a modificare Snake attraverso il bridge esistente.

Per scegliere valori e confrontarli sullo stesso replay: [Regolare il basso all'ascolto](PLAYER-M4L.md#regolare-il-basso-allascolto).

Il launcher `08 - Scegli assetto basso.command` propone `sobrio`, `dialogo` e `ritmico`, riusando il 07. [Comandi per Firenze con il basso](TEST-PRESET-MUSICALI.md#firenze-con-il-basso).

Il ricevitore accetta anche [aggiornamenti dei parametri durante l'esecuzione](CONTROLLI-BASSO.md), su un indirizzo OSC distinto e sulla stessa porta. Il mittente verrà sviluppato separatamente.

Per generare automaticamente un suggerimento dai pattern della tappa, avviando l'analisi su richiesta e senza invii a Live: [Analisi del basso](TEST-PRESET-MUSICALI.md#suggerire-il-basso-dalla-tappa). Non cambia i launcher o i controlli durante l'esecuzione.

## Acquisire Export Snake

[Funzionamento, formato dei dati e piano delle verifiche](EXPORT-SNAKE.md).

Aprire `comandi/05 - Acquisisci Export Snake.command`. Ascolta la porta locale 9003, senza generare il basso o modificare Live. Chiudere prima `live_bass`, che usa la stessa porta.

Con Live fermo e Export attivo, attendere «Export ricevuto». Registrare il MIDI da 1.1.1 con loop disattivato, poi premere Stop: l’acquisizione termina automaticamente. Il terminale mostra il percorso `snake-state.jsonl` in una nuova cartella temporanea esterna alla repository. Conservare insieme MIDI esportato, BPM e posizione iniziale della clip per il confronto. Il file versionato contiene metadati di sessione, snapshot decodificati con beat/fase/stato e motivo di chiusura. I messaggi non decodificabili sono conservati per la diagnosi.

Il limite predefinito è 180 secondi, inclusa l’attesa; Ctrl+C chiude e conserva i dati ricevuti. Da terminale: `python -m desnivel.cli.capture_snake --seconds 180 --label "prova Export"`. Un file vuoto non è un’acquisizione valida; gli errori trasmessi da Export sono conservati e mostrati.


## Stop e ripartenza

Il launcher `06 - Export stop e ripartenza.command` riusa il ricevitore con `--keep-open`, limite di 600 secondi ed etichetta della prova. Non termina allo Stop di Live: chiudere con Ctrl+C nel terminale dopo aver completato le registrazioni. Il launcher 05 conserva la chiusura automatica precedente.

Lasciare invariata la configurazione Snake ed Export attivo. Registrare quattro battute da 1.1.1 senza loop, fermare Live ed esportare la clip come `MIDI-prima-stop.mid`. Riportare il trasporto a 1.1.1, registrare altre quattro battute ed esportare `MIDI-dopo-stop.mid`. Conservare il primo MIDI prima della seconda registrazione. I due file e il JSONL della stessa sessione permettono di confrontare separatamente le epoche prima e dopo Stop.


## Verificare il basso completo

Il launcher `07 - Basso e acquisizione.command` avvia `live_bass --capture`: suona il basso e salva in `bass-session.jsonl`, fuori dalla repository, gli stati Snake e i piani inviati al player. Riusa l’archivio JSONL versionato; l’indirizzo OSC distingue ingresso e uscita. L’invio UDP registrato non certifica la ricezione del player.

Chiudere gli altri ricevitori sulla porta 9003. Usare il device `Desnivel_Bass.amxd` prima del synth sulla traccia basso, Export attivo su Snake e la configurazione già verificata. Registrare il MIDI Post FX della traccia basso da 1.1.1 senza loop per almeno quattro battute. Il basso entra dopo l’anticipo di pianificazione: il silenzio iniziale va conservato nella clip esportata. Per verificare anche la ripartenza, esportare la prima clip, tornare a 1.1.1 e ripetere mantenendo aperto il launcher. Chiudere con Ctrl+C; conservare i due MIDI e il JSONL.

Il test automatico verifica che l’archivio conservi lo stato ricevuto, il piano effettivamente passato al client UDP e il reset finale. Il confronto MIDI del player già concluso è descritto in [Sessione](SESSIONE.md#confronto-del-player-del-basso).

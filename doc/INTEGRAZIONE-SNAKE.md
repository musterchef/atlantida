# Integrazione MDD Snake — guida al prototipo

Aggiornata il 2026-10-02. Riferimento: [decisione architetturale](DECISIONE-ARCHITETTURA-AUDIO.md).

## Confini

Questa guida descrive soltanto il primo adattatore. Il motore musicale Python produce decisioni indipendenti dal device, utilizzabili da altri adattatori senza riscrivere le regole musicali o il producer. Il percorso OSC/M4L qui sotto è specifico dell'integrazione Snake; altre destinazioni possono usare protocolli e ambienti differenti.

```text
Producer GPX → metriche neutre → motore musicale Python
                                     ↓ decisioni musicali
                               adattatore Snake
                                     ↓ comandi OSC
                               patch M4L → Snake / Live
```

Il motore musicale Python contiene regole, soglie, stato e mapping configurabili. L'adattatore contiene nomi e range specifici di Snake. M4L riceve e applica i comandi; il clock delle note resta in Live/Snake.

Il viaggio evolve indipendentemente dal clock musicale. Accelerare il replay non implica accelerare il BPM. Il producer resta agnostico e utilizzabile da altri consumer; il supporto Snake può essere scollegato senza cambiarlo. Le altre implementazioni sono conservate; il precedente generatore TD/JS è stato spostato in [old/td_audio](../old/td_audio/README.md).

## File e stato

| File | Ruolo |
|---|---|
| `src/desnivel/trip_metrics.py` | Catalogo e calcolo delle metriche neutre; già implementato. |
| `src/desnivel/config.py` | Frequenza e parametri del producer; non aggiungere mapping Snake qui. |
| `src/desnivel/sinks/trip_metrics_osc.py` | Invio OSC e replay delle metriche. |
| `src/desnivel/cli/stream_metrics.py` | Comando di avvio del producer. |
| `m4l/desnivel_snake_bridge.maxpat` | Receiver iniziale di quota e timestamp; non contiene ancora le modifiche fatte manualmente in Live. |
| `src/desnivel/bridges/osc_to_midi.py` | Bridge `/mod/*` esistente, conservato; non è il nuovo adattatore Snake. |
| `tests/test_trip_metrics*.py` | Test del contratto metrico esistente. |

Motore musicale separato, adattatore Snake e loro configurazione sono da implementare. Non attribuire loro file o funzionalità già esistenti. Prima di modificare il device M4L, salvare nel progetto la versione funzionante usata in Live: il `.maxpat` iniziale non si aggiorna da solo.

## Risultati verificati dall'utente

- Ricezione GPX → OSC → Max, poi patch inserita in Ableton con dati visibili nell'editor.
- Mappabilità dei controlli necessari di Snake confermata dall'utente.
- Lettura API di `Note_01`: minimo 0, massimo 83.
- `set value 12` tramite `live.object` cambia il parametro di Snake.

Non verificati: equivalenza tra valore del parametro e nota MIDI emessa, controllo completo di gate/velocity, aggiornamento di tutti gli step e applicazione sincronizzata del pattern.

## Riprodurre la prova delle metriche

Dalla root, nell'ambiente del progetto:

```bash
source .venv/bin/activate
python -m desnivel.cli.stream_metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --dry-run
python -m desnivel.cli.stream_metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30 --osc-port 9000
```

Formato: `/desnivel/v1/trip/metric/<nome> elapsed_s value`. Il primo argomento è il tempo, il secondo il valore. Il pilot produce metriche a 1 Hz nel tempo del viaggio; il replay accelerato aumenta la frequenza reale. Contratto: [CONTRATTO-DATI-VIAGGIO.md](CONTRATTO-DATI-VIAGGIO.md).

Aprire [la patch](../m4l/desnivel_snake_bridge.maxpat) in Max. Bloccarla con Cmd+E per usare i controlli. Il messaggio locale di test mostra 12.5 secondi e 345 metri: non prova la rete. Tenere un solo receiver sulla porta scelta; nella prova un altro receiver impediva l'aggiornamento in Max.

Per usarla in Live, copiare gli oggetti nel template di un Max MIDI Effect sostituendo il pass-through MIDI del template, senza duplicarlo. Salvare il device `.amxd` nel progetto. La ricezione diretta delle metriche resta utile come diagnostica; il nuovo flusso operativo porterà a M4L comandi già elaborati, con protocollo e porta da definire separatamente.

## Collegamento manuale verificato

Nell'editor del device aperto da Live:

1. **M** crea un messaggio: `path live_set view selected_parameter`.
2. **N** crea l'oggetto `live.path`. Collegare il messaggio al suo ingresso.
3. **N** crea `live.object`. Collegare l'uscita sinistra di `live.path` all'ingresso destro di `live.object`.
4. Creare con **M** i messaggi `get name`, `get min`, `get max`, `get value`, `set value 12`. Collegarli all'ingresso sinistro di `live.object`.
5. Collegare l'uscita di `live.object` a un oggetto `print parametro`.
6. Bloccare la patch. In Live, con MIDI Map disattivato, selezionare la manopola di Snake; in Max cliccare il messaggio `path ...`, poi i comandi di lettura e scrittura.

Gli ID vengono acquisiti da Live: non scrivere nel codice i numeri osservati durante una sessione. Per `Note_01` usare il range osservato 0–83; non assumere che sia una nota MIDI o un valore normalizzato 0–1. L'associazione da conservare al riavvio resta da implementare/verificare.

Riferimenti: [live.path](https://docs.cycling74.com/reference/live.path), [live.object](https://docs.cycling74.com/reference/live.object), [udpreceive](https://docs.cycling74.com/reference/udpreceive/).

## Risoluzione dei problemi

- `path: No such object`: creare `path ...` con **M** come messaggio.
- Nessun dato OSC: controllare la porta e chiudere altri receiver sulla stessa porta.
- Parametro inatteso: leggere `get name` prima di scrivere un valore.
- Crash con `live.remote~`: usare il collegamento verificato con `live.object`.

## Prossimi passi: sviluppo autonomo

1. **Salvare la base funzionante:** portare nel progetto il device con `live.object` verificato, mantenendo il receiver iniziale come riferimento diagnostico.
2. **Una regola Python:** scegliere una metrica, una conversione e i suoi parametri configurabili. Definire input/output e comportamento a dati mancanti o replay riavviato. Provare la funzione con valori noti prima di collegarla alla rete.
3. **Un adattamento Snake:** tradurre la decisione nel parametro e range di destinazione. Nessun ID Live nel motore musicale. Non generalizzare a tutti i sequencer prima di questa prova.
4. **Un comando OSC:** documentare indirizzo, argomenti, destinazione di rete e comportamento dei valori fuori intervallo. Usare un contratto distinto dalle metriche del viaggio. Evitare due receiver sulla stessa porta.
5. **Ricevere e applicare in M4L:** trasformare il comando ricevuto in `set value` per il parametro associato. Non trasferire qui soglie e regole geografiche.
6. **Provare la catena:** valore noto → parametro atteso, poi replay GPX. Verificare stop, riavvio e associazione del parametro dopo riapertura del set. Solo dopo aggiungere altre destinazioni e timing a battuta/step.

Non implementare tutti i passi insieme. La prova del cambio manuale è già completata e non va ripetuta come prerequisito a ogni sessione.

### Scheda della prima regola

| Decisione | Da compilare |
|---|---|
| Metrica, unità e intervallo di ingresso | |
| Regola musicale e parametri configurabili | |
| Decisione prodotta dal motore | |
| Destinazione e conversione dell'adattatore | |
| Comando OSC, argomenti e porta | |
| Dati assenti, timeout, stop e nuovo replay | |
| Applicazione immediata o sincronizzata | |
| Input di prova e risultato atteso | |

Per una soglia distinguere permanenza sopra soglia da attraversamento: decidere quando riarmare la regola ed evitare trigger ripetuti. Non aggiungere queste regole al producer GPX.

### Autocomplete e richieste mirate

Usare autocomplete per piccoli blocchi di comportamento già deciso. Per una revisione indicare file, input, risultato atteso e osservato; chiedere di leggere solo il frammento o diff necessario. Per gli oggetti Max usare l'help installato. Salvare un punto funzionante e aggiornare questa guida a fine sessione.

## Prossimo passo minimo

Salvare nel progetto il device M4L funzionante, poi scegliere e implementare una sola conversione configurabile nel consumer Python.

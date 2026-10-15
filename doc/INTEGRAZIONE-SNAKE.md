# Integrazione MDD Snake — guida al prototipo

Aggiornata il 2026-10-15. Riferimento: [decisione architetturale](TODO-ARCHITECTURE.md).

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

Il viaggio evolve indipendentemente dal clock musicale. Accelerare il replay non implica accelerare il BPM. Il producer resta agnostico e utilizzabile da altri consumer; il supporto Snake può essere scollegato senza cambiarlo.

## File e stato

| File | Ruolo |
|---|---|
| `src/desnivel/trip/metrics.py` | Catalogo e calcolo delle metriche neutre; già implementato. |
| `src/desnivel/trip/config.py` | Frequenza e parametri del producer; non aggiungere mapping Snake qui. |
| `src/desnivel/sinks/trip_metrics_osc.py` | Invio OSC e replay delle metriche. |
| `src/desnivel/cli/stream_metrics.py` | Comando di avvio del producer. |
| `m4l/desnivel-bridge.amxd` | Device funzionante: riceve le metriche (9000) e i comandi di controllo (9001). |
| `m4l/desnivel_snake_params.js` | Trova Snake e imposta i parametri per nome; va tenuto nella cartella del device. |
| `src/desnivel/adapters/snake.py` | Nomi, gate, scale e conversioni per Snake. |
| `src/desnivel/cli/snake_pattern.py` | Invio di gate e note. |
| `archivio/src/desnivel/bridges/osc_to_midi.py` | Bridge storico `/mod/*`, escluso dal pacchetto corrente. |
| `tests/trip/test_trip_metrics*.py` e `tests/sinks/test_trip_metrics_osc.py` | Test del contratto metrico esistente. |

Il motore a pattern e l’adattatore Snake sono implementati in `music/patterns.py`, `music/journey.py` e `adapters/snake.py`. Comandi e configurazioni sono descritti in [Comandi](COMANDI.md) e [Preset musicali](TEST-PRESET-MUSICALI.md). Prima di modificare il device M4L, salvare nel progetto la versione funzionante usata in Live: il `.maxpat` iniziale non si aggiorna da solo.

## Risultati verificati dall'utente

- Ricezione GPX → OSC → Max, poi patch inserita in Ableton con dati visibili nell'editor.
- Mappabilità dei controlli necessari di Snake confermata dall'utente.
- Lettura API di `Note_01`: minimo 0, massimo 83.
- `set value 12` tramite `live.object` cambia il parametro di Snake.

Le verifiche successive dello stato esportato e della previsione MIDI sono in [Export Snake](EXPORT-SNAKE.md#verifiche-concluse). L’applicazione dei cambi di pattern non è atomica né quantizzata a battuta.

## Riprodurre la prova delle metriche

Dalla root, nell'ambiente del progetto:

```bash
source .venv/bin/activate
python -m desnivel.cli.stream_metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --dry-run
python -m desnivel.cli.stream_metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30 --osc-port 9000
```

Formato: `/desnivel/v1/trip/metric/<nome> elapsed_s value`. Il primo argomento è il tempo, il secondo il valore. Il pilot produce metriche a 1 Hz nel tempo del viaggio; il replay accelerato aumenta la frequenza reale. Contratto: [CONTRATTO-DATI-VIAGGIO.md](CONTRATTO-DATI-VIAGGIO.md).

Caricare in Live [il device](../m4l/desnivel-bridge.amxd), copiandolo con il `.js` nella cartella User Library dei Max Audio Effect. Per provarlo in Max, aprirlo e bloccare la patch con Cmd+E. Il messaggio locale di test mostra 12.5 secondi e 345 metri: non prova la rete. Tenere un solo receiver sulla porta scelta; nella prova un altro receiver impediva l'aggiornamento in Max.

Per usarla in Live, copiare gli oggetti nel template di un Max MIDI Effect sostituendo il pass-through MIDI del template, senza duplicarlo. Salvare il device `.amxd` nel progetto. La ricezione diretta delle metriche resta utile come diagnostica; il nuovo flusso operativo porterà a M4L comandi già elaborati, sulla porta 9001, indirizzo `/desnivel/v1/control/snake/set`, con nome del parametro e valore.

## Collegamento manuale verificato

Nell'editor del device aperto da Live:

1. **M** crea un messaggio: `path live_set view selected_parameter`.
2. **N** crea l'oggetto `live.path`. Collegare il messaggio al suo ingresso.
3. **N** crea `live.object`. Collegare l'uscita sinistra di `live.path` all'ingresso destro di `live.object`.
4. Creare con **M** i messaggi `get name`, `get min`, `get max`, `get value`, `set value 12`. Collegarli all'ingresso sinistro di `live.object`.
5. Collegare l'uscita di `live.object` a un oggetto `print parametro`.
6. Bloccare la patch. In Live, con MIDI Map disattivato, selezionare la manopola di Snake; in Max cliccare il messaggio `path ...`, poi i comandi di lettura e scrittura.

Gli ID vengono acquisiti da Live: non scrivere nel codice i numeri osservati durante una sessione. Per `Note_01` usare il range osservato 0–83; non assumere che sia una nota MIDI o un valore normalizzato 0–1. Il bridge operativo risolve i parametri per nome tramite `desnivel_snake_params.js`.

Riferimenti: [live.path](https://docs.cycling74.com/reference/live.path), [live.object](https://docs.cycling74.com/reference/live.object), [udpreceive](https://docs.cycling74.com/reference/udpreceive/).

## Risoluzione dei problemi

- `path: No such object`: creare `path ...` con **M** come messaggio.
- Nessun dato OSC: controllare la porta e chiudere altri receiver sulla stessa porta.
- Parametro inatteso: leggere `get name` prima di scrivere un valore.
- Crash con `live.remote~`: usare il collegamento verificato con `live.object`.

## Stato corrente

La base confermata e le verifiche ancora aperte sono in [Stato del progetto](SESSIONE.md).

## Leggere le Shape

Il messaggio Max `shapes`, collegato all’ingresso di `js desnivel_snake_params.js`, elenca le Shape e i relativi indici e valori. Nella mod per il basso, Gates è identificato dal nome univoco `Gate_Shape`; il comando `gate_shape` lo cerca per nome a ogni invio. `shapes <indice>` legge un singolo parametro senza modificarlo. Il bridge cerca la prima istanza di Snake.

Aggiornare il JS accanto al device e ricaricarlo. Selezionare una forma in Snake, cliccare il messaggio e associare il numero stampato al percorso visibile. Sospendere il replay Python durante la mappatura perché può cambiare la Shape. La numerazione delle celle è per righe, da 1 a 16.

## Banco Length dedicato

`tools/build_snake_length.py` genera una copia del vanilla 3.2.3 con un banco Length che segue Notes. Conserva Notes, Gates, Velocities e i tre Custom. Il builder accetta soltanto la versione sorgente ispezionata, verificata tramite SHA256.

```bash
python3 tools/build_snake_length.py \
  --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd" \
  --output /tmp/desnivel-snake-length/MDD_SNAKE_LengthBank.amxd
```

L'output deve essere un file nuovo. Il device generato resta fuori dalla repository.

Length ha 16 valori da 0 a 127, convertiti linearmente fra Min e Max in millisecondi. Ogni durata appartiene alla corrispondente cella Notes. Il motore Notes seleziona insieme altezza e durata; Length non ha un sequencer autonomo. I limiti iniziali sono 50–500 ms. La durata corrente viene acquisita all'attacco di ogni nota; cambiarla non modifica le note già iniziate. `makenote` gestisce i note-off e chiude la nota precedente quando viene ripetuta la stessa altezza.

Verificati struttura, collegamenti e conservazione delle risorse incorporate. L’utente ha confermato suono, controllo Shape e replay Firenze nella configurazione installata. Durate, retrigger e previsione sono stati confrontati con registrazioni MIDI nelle configurazioni descritte in [Export Snake](EXPORT-SNAKE.md#verifiche-concluse). Il bridge risolve Gates per nome nella mod; gli indici non sono stabili tra versioni.

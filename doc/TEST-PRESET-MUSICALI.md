# Preset musicali

Una voce melodica, tre interpretazioni confrontabili: movimento, sforzo e misto. Il producer resta neutro; Python genera pattern indipendenti dalla destinazione. Snake è l'adattatore disponibile.

## Avvio

Con bridge e Snake già caricati e trasporto Live avviato:

```sh
source .venv/bin/activate
python -m desnivel.cli.trip_music --gpx gpx/tappa04_Levanto_La_Spezia.gpx --stage-music presets/tappe/levanto_la_spezia.json --preset presets/misto.json --speed 50
```

Sostituire `misto.json` con `movimento.json` o `sforzo.json` per confrontare le interpretazioni. Aggiungere `--dry-run` per leggere tutte le decisioni senza attese né invii. Non serve `stream_metrics`; il comando usa direttamente il producer Python. Il riepilogo viene stampato prima del replay.

## Controlli

| File / campo | Significato |
|---|---|
| `presets/movimento.json` | Solo velocità filtrata, normalizzata sul riferimento configurato. |
| `presets/sforzo.json` | Solo stima dello sforzo disponibile nel producer. |
| `presets/misto.json` | Movimento 60%, sforzo 40%; i pesi vengono normalizzati. |
| `presets/tappe/levanto_la_spezia.json` | Motivo, armonia, gate e tempi della tappa. |
| `gate_range` | Numero minimo e massimo di gate: 3–10 nella prova. |
| `gate_priority` | Ordine di apertura delle celle, indici da 0. Aumentando la densità si conservano i gate già aperti. |
| `motif_degrees` | Motivo espresso nei gradi della scala iniziale, da 0. |
| `sections` | Sezioni per frazione della distanza percorsa, con scala e tonica proprie. |
| `degree_overrides` | Celle da modificare con gradi della scala della sezione. Le altre mantengono la nota comune o quella consentita più vicina. |
| `update_s` | Intervallo minimo fra decisioni, in secondi del viaggio. |
| `smoothing_s` | Costante del filtro esponenziale nel tempo del viaggio. |
| `stale_s` | Età massima degli ingressi prima di sospendere nuove decisioni. |

La densità è la media pesata delle interpretazioni, convertita nel numero di gate. Lo sforzo deriva già anche dalla velocità: i due ingressi non sono statisticamente indipendenti. Non è una misura fisiologica.

La prova usa La pentatonica minore, La minore dal 30% e ritorno alla pentatonica dal 75%. Nello sviluppo cambiano solo due celle, introducendo Si e Fa. Tonica e percorso sono scelte modificabili della tappa, non deduzioni automatiche dal GPX.

A 50× il filtro di 60 s equivale a 1,2 s reali e l'intervallo di 200 s a 4 s. Il clock di Snake non cambia. Si inviano solo pattern diversi dal precedente. Le variazioni della melodia avvengono per ora ai cambi di sezione; la densità segue i dati durante tutta la tappa.

## Limiti e verifica

- Gli ingressi attivi mancanti o scaduti conservano l'ultimo pattern; il primo invio attende dati validi. Una sosta riduce la densità verso il minimo, non impone silenzio.
- I cambi arrivano subito, senza sincronizzazione a ciclo e senza applicazione atomica. Il bridge applica i parametri uno alla volta.
- Snake richiede 16 celle; lunghezza eseguita e percorso restano impostazioni dell'utente. Non vengono imposti dal comando.
- Echo e Reverb non sono ancora controllati. L'ottava MIDI effettiva di Snake resta da verificare.
- Fine replay e Ctrl+C lasciano attivo l'ultimo pattern in Live.

La generazione sul GPX Levanto–La Spezia produce 36 cambi per movimento, 32 per sforzo e 31 per misto, attraversando le tre sezioni. Il replay Firenze è stato confermato in Live; gli altri preset restano da valutare all’ascolto.

Codice: `src/desnivel/journey_music.py` per le regole; `music.py` per pattern e scale; `adapters/snake.py` per la traduzione; `cli/trip_music.py` per il replay. La regola a soglia è descritta in [Quota e pattern](TEST-VIAGGIO-SNAKE.md).

## Shape dei Gates per sezione

Il bridge accetta `gate_shape` e l’alias precedente `test_shape_90`. Nella mod per il basso risolve il parametro per nome univoco `Gate_Shape`, senza dipendere dall’ordine dei parametri. L’indice 90 resta un ripiego soltanto per il vanilla a 152 parametri.

A ogni ingresso di sezione, inclusa la prima, l'adattatore Snake estrae un intero uniforme 0–13. Il valore può ripetersi. Gli aggiornamenti nella stessa sezione non estraggono altre Shape. Il motore musicale emette solo l'indice della sezione; nomi e range Snake restano nell'adattatore.

Aggiornare `desnivel_snake_params.js` accanto al device e ricaricare il bridge. Il comando del replay resta uguale; `--seed 7` rende ripetibili le estrazioni. Senza seed cambiano a ogni avvio. I messaggi Shape vengono applicati immediatamente, senza sincronizzazione a battuta.

Verificati 15 test su motore e adattatore e dry-run sul GPX: tre estrazioni, valori 5, 2, 6 con seed 7. L’11 ottobre 2026 l’utente ha confermato il funzionamento dei launcher Shape 0 e 13 e del replay Firenze a 150×.

## Altre tappe

Tre preset con quattro sezioni, ai progressi 0%, 25%, 55% e 80% della distanza. Sono scelte compositive per l'ascolto, non armonie dedotte dal paesaggio. Ogni sezione modifica più celle; il motivo torna riconoscibile senza ripetere esattamente la prima versione.

| Tappa | Carattere | Percorso delle scale | Gate |
|---|---|---|---|
| Firenze–San Gimignano | Più mobile, con salti e cambi di colore | Re dorico → misolidio → minore → dorico | 4–11 |
| Sabaudia–Formia | Più aperto e meno denso | Do pentatonico maggiore → maggiore → lidio → pentatonico maggiore | 3–8 |
| Peschici–Mattinata | Più teso e denso | Mi minore → frigio → dorico → minore | 4–12 |

Le toniche sono classi di altezza; il registro dipende dai parametri e dalla conversione di Snake. Le Shape dei Gates sono ripetibili con `--seed 7`. Nessun controllo di velocità, direzione, durata o effetto viene aggiunto da questi preset.

```sh
python -m desnivel.cli.trip_music --gpx gpx/tappa05_Firenze_San_Gimignano.gpx --stage-music presets/tappe/firenze_san_gimignano.json --preset presets/misto.json --speed 50 --seed 7
```

```sh
python -m desnivel.cli.trip_music --gpx gpx/tappa08_Sabaudia_Formia.gpx --stage-music presets/tappe/sabaudia_formia.json --preset presets/misto.json --speed 50 --seed 7
```

```sh
python -m desnivel.cli.trip_music --gpx gpx/tappa11_Peschici_Mattinata.gpx --stage-music presets/tappe/peschici_mattinata.json --preset presets/misto.json --speed 50 --seed 7
```

Eseguire un replay alla volta. Per accompagnarlo, lasciare `python -m desnivel.cli.live_bass --preset responsive` in un secondo terminale. Alla fine Snake mantiene l'ultimo pattern: interrompere il replay precedente prima di avviare una tappa diversa.

L'intervallo minimo fra decisioni è 150 secondi di viaggio, pari a 3 secondi a 50×. Verificare le decisioni senza inviare aggiungendo `--dry-run`.

## Firenze con il basso

Usare il Set funzionante con bridge, Snake, Export attivo e player del basso prima dello strumento. Chiudere gli altri ricevitori 05/06/07 sulla porta 9003. Il launcher 08 riusa il 07: genera il basso e salva stati e piani nella cartella temporanea mostrata nel terminale.

Nel primo terminale, dalla radice del progetto, scegliere l'assetto dal menu:

```sh
./comandi/08\ -\ Scegli\ assetto\ basso.command
```

Oppure selezionarlo direttamente:

```sh
./comandi/08\ -\ Scegli\ assetto\ basso.command sobrio
```

| Assetto | Obiettivo d'ascolto | Scelte principali |
|---|---|---|
| `sobrio` | Un appoggio poco invadente; primo confronto consigliato. | Preset responsive, registro 28–47, densità 0,6, mobilità 0,15, articolazione 0,85, distanza minima 1 beat. |
| `dialogo` | Più risposte negli spazi e movimento moderato. | Preset responsive, registro 28–55, densità 1, distanza minima 0,5 beat, sincopi 0,45, legame ritmico 0,3, melodico 0,35, mobilità 0,3, articolazione 0,7. |
| `ritmico` | Note più corte, levare e risposte acute. | Preset slap, registro 28–59, densità 1,2, mobilità 0,6; gli altri valori sono quelli del preset. |

Tutti usano seed del basso 0; i controlli non indicati ereditano i valori descritti in [Generare il basso](PLAYER-M4L.md#generare-il-basso). Sono assetti da valutare all'ascolto, non risultati musicali già confermati.

Avviare il trasporto Live dalla stessa posizione iniziale per ogni confronto. Nel secondo terminale, dalla radice del progetto, avviare Firenze a 50×:

```sh
.venv/bin/python -m desnivel.cli.trip_music --gpx gpx/tappa05_Firenze_San_Gimignano.gpx --stage-music presets/tappe/firenze_san_gimignano.json --preset presets/misto.json --speed 50 --seed 7
```

Il seed 7 riguarda le Shape di Snake; il seed 0 del primo terminale riguarda le variazioni del basso. I BPM restano quelli di Live: 50× accelera i cambi del viaggio, non il clock musicale.

Per cambiare assetto, fermare prima il replay e poi il basso con Ctrl+C; il launcher 07 richiede Invio per chiudere. Fermare il trasporto, ripristinare la stessa configurazione iniziale Snake e ripetere i due comandi con `dialogo` o `ritmico`. Non avviare un secondo ricevitore mentre il primo è aperto. Fine replay lascia attivo l'ultimo pattern: fermare il basso separatamente.

Per correggere un assetto senza modificarne il codice, aggiungere un controllo:

```sh
./comandi/08\ -\ Scegli\ assetto\ basso.command dialogo --density .8
```

Le opzioni finali prevalgono sui valori dell'assetto. Confrontare lo stesso tratto e modificare un controllo per volta; [guida all'ascolto](PLAYER-M4L.md#regolare-il-basso-allascolto) e [scelte delle regole](SCELTE-BASSO.md) spiegano effetti e limiti.

## Suggerire il basso dalla tappa

L'analisi genera automaticamente un suggerimento e viene avviata dall'utente su richiesta. Non modifica gli assetti o il ricevitore live. Genera le stesse decisioni melodiche del replay e stampa un comando per il basso, senza inviarlo a Live:

```sh
.venv/bin/python -m desnivel.cli.analyze_bass --gpx gpx/tappa05_Firenze_San_Gimignano.gpx --stage-music presets/tappe/firenze_san_gimignano.json --preset presets/misto.json
```

Usare GPX, configurazione musicale e interpretazione uguali al replay che si vuole ascoltare. `--preset` indica qui l'interpretazione del viaggio, con `misto.json` come valore predefinito. Per altre tappe sostituire GPX e `--stage-music` con i percorsi documentati sopra. La velocità del replay non cambia il suggerimento.

Il risultato contiene la frazione media di gate aperti, la sua variabilità e un assetto unico da provare per tutta la tappa. Copiare il comando stampato nel primo terminale; nel secondo avviare il replay consueto. Non occorre eseguire l'analisi per usare il launcher 08.

Il suggerimento lascia più spazio al basso quando la melodia è rarefatta; con più gate aperti riduce densità, levare e durate. Il registro resta 28–47 e la mobilità contenuta. I gate descrivono una disponibilità di attacchi, non le note effettive: clock, Steps, Shape e strumento in Live non sono noti. Il risultato è una proposta compositiva prudente, da correggere all'ascolto. [Regole e formule](SCELTE-BASSO.md#suggerimento-automatico-dalla-tappa).

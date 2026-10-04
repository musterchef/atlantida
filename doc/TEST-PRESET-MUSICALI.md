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
- I cambi arrivano subito, senza sincronizzazione a ciclo e senza applicazione atomica. Il bridge M4L non è stato modificato.
- Snake richiede 16 celle; lunghezza eseguita e percorso restano impostazioni dell'utente. Non vengono imposti dal comando.
- Echo e Reverb non sono ancora controllati. L'ottava MIDI effettiva di Snake resta da verificare.
- Fine replay e Ctrl+C lasciano attivo l'ultimo pattern in Live.

Verificati 18 test mirati e generazione sul GPX: 36 cambi per movimento, 32 per sforzo, 31 per misto. Tutti attraversano le tre sezioni. Nessun invio ad Ableton eseguito dall'assistente; l'ascolto resta da fare.

Codice: `src/desnivel/journey_music.py` per le regole; `music.py` per pattern e scale; `adapters/snake.py` per la traduzione; `cli/trip_music.py` per il replay. Il precedente test `--rules presets/quota.json` resta disponibile.

## Shape dei Gates per sezione

Il parametro 90 è stato confermato dall'utente come Shape dei Gates. Il bridge ora accetta `gate_shape`, mantenendo anche `test_shape_90`.

A ogni ingresso di sezione, inclusa la prima, l'adattatore Snake estrae un intero uniforme 0–13. Il valore può ripetersi. Gli aggiornamenti nella stessa sezione non estraggono altre Shape. Il motore musicale emette solo l'indice della sezione; nomi e range Snake restano nell'adattatore.

Aggiornare `desnivel_snake_params.js` accanto al device e ricaricare il bridge. Il comando del replay resta uguale; `--seed 7` rende ripetibili le estrazioni. Senza seed cambiano a ogni avvio. I messaggi Shape vengono applicati immediatamente, senza sincronizzazione a battuta.

Verificati 15 test su motore e adattatore e dry-run sul GPX: tre estrazioni, valori 5, 2, 6 con seed 7. Automazione dei cambi di sezione ancora da ascoltare in Live.

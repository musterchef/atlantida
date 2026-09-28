# Stato di implementazione del contratto OSC

- Verificato il: 2026-09-28
- Riferimenti: [CONTRATTO-MODULAZIONI.md](CONTRATTO-MODULAZIONI.md), [CONTRATTO-DATI-VIAGGIO.md](CONTRATTO-DATI-VIAGGIO.md), [DECISIONE-ARCHITETTURA-AUDIO.md](DECISIONE-ARCHITETTURA-AUDIO.md)
- Scopo: distinguere le metriche di viaggio gia' derivate dai vecchi output musicali e registrare cio' che serve per definire il contratto neutrale.

## Metriche gia' nel Track

Il loader espone `elapsed_s`, `dist_m`, `cum_dist_m`, `ele`, `speed_kmh`, `slope`, `effort`, `lat` e `lon` in `Track.samples` (il tempo e' nell'asse `Track.t`). Le definizioni sorgente sono riportate sopra e implementate nel loader.

## Publisher neutrale implementato

`desnivel-stream-metrics` usa `build_metric_samples` in `src/desnivel/trip_metrics.py` e `TripMetricsOscSink` in `src/desnivel/sinks/trip_metrics_osc.py`.

- Namespace: `/desnivel/v1/trip/metric/<nome>`.
- Argomenti OSC: `(elapsed_s, value)`.
- Frequenza pilot: 1 Hz; le metriche d'intervallo sono aggregate su finestre complete da un secondo.
- Campi: `distance_delta_m`, `distance_total_m`, `elevation_m`, `speed_kmh`, `slope_ratio`, `effort_estimate`.
- I valori non finiti e gli intervalli con campioni interni mancanti sono omessi per le metriche interessate; un endpoint finito puo' comunque essere pubblicato come misura istantanea.
- `effort_estimate` usa riferimenti e pesi `GpxConfig`; e' esplicitamente una stima, non una misura fisiologica.
- Elevazione totalmente assente nel GPX: il loader omette `ele`, `slope` ed `effort`; buchi isolati fra quote valide vengono interpolati prima del filtraggio.

Il publisher non invia coordinate GPS nel pilot audio. L'aggiunta di coordinate o campi ulteriori richiede un consumer e un'esigenza concreti.

## Output musicali del prototipo corrente (non target)

La tabella seguente inventaria `/mod/*` emesso oggi. Questi canali incorporano mapping o astrazioni musicali e **non sono il contratto agnostico scelto**. Restano nel prototipo finche' il nuovo contratto neutrale non e' definito e migrato.

| Canale prototipo | Stato nel codice | Sorgente effettiva / osservazione |
|---|---|---|
| `/mod/journey/phase`, `/mod/journey/energy`, `/mod/journey/openness` | Implementati | Curve/aggregati derivati dal viaggio, ma esposti con un namespace e significati da modulazione musicale; valutare se rimpiazzarli con metriche neutrali. |
| `/mod/macro/scale`, `/mod/macro/palette`, `/mod/macro/register`, `/mod/macro/space`, `/mod/macro/brightness` | Implementati | Mapping esplicito a scale, palette, registro, riverbero e brillantezza: logica consumer musicale nel producer, da migrare fuori da Python. |
| `/mod/meso/root`, `/mod/meso/tension` | Implementati | Root e accumulo denominato tensione: interpretazioni musicali basate su distanza/effort, da sostituire con dati neutri nel contratto target. |
| `/mod/body/euclid_k`, `/mod/body/euclid_rot` | Implementati | Parametri di pattern euclideo: specifici del sequencer consumer, da migrare fuori da Python. |
| Altri canali `/mod/meso/*`, `/mod/micro/*`, `/mod/body/*` | Solo specificati | Non hanno producer nella pipeline standard corrente; non implementare consumer M4L per questi prima di ridefinire il contratto. |

I rate configurati per gruppo (`journey`, `macro`, `meso`, `body`, `micro`) appartengono solo al prototipo `/mod/*`; il publisher neutrale usa la frequenza configurata `OscConfig.trip_metrics_rate_hz`.

## Eventi

I `kind` dei detector (per esempio vetta, ingresso sotto soglia costa, passaggio in POI) descrivono osservazioni del viaggio e possono essere candidate a fatti neutrali. La categoria corrente `MAJOR`/`MINOR`, i cap e i cooldown sono invece policy di composizione musicale applicate dalla pipeline: non vanno trasferiti automaticamente nel nuovo contratto agnostico. Il contratto target dovra' separare timestamp/payload del fatto dalle priorita' che ciascun consumer gli assegna.

| Eventi OSC prodotti | Stato |
|---|---|
| `/event/major/start`, `/event/major/end` | Implementati come eventi framing. |
| `/event/major/summit` | Implementato da `SummitDetector`. |
| `/event/major/sea` | Implementato da `SeaDetector`. |
| `/event/major/poi` | Implementato da `POIDetector` quando e' disponibile un registry POI. |
| `/event/minor/*` | Nessun detector minor attivo nella pipeline standard corrente. |
| `/event/major/city_arrival` | Non implementato; il passaggio POI usa il kind `poi`. |

Il bridge OSC→MIDI attuale mappa `sea_first_view`, mentre il producer emette `sea`: il trigger mare non trova una corrispondenza nella tabella MIDI. Il bridge non e' il consumer audio di destinazione, ma il disallineamento resta da correggere se viene usato come tool di test.

## Lavoro residuo

1. Definire i fatti/eventi neutrali senza categorie `MAJOR`/`MINOR` o cooldown compositivi.
2. Provare il publisher con un receiver OSC reale e poi con M4L.
3. Migrare in M4L root/scale/palette/pattern; TD interpreta autonomamente le metriche necessarie alla visualizzazione.
4. Tenere il percorso legacy TD `/desnivel/*` su porta 9001 fuori dal consumer nuovo.

Questo inventario descrive lo stato verificato del codice, non sostituisce la specifica del pilot.

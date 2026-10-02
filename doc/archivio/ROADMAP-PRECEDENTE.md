# TODO — DESNIVEL

Aggiornato il 2026-10-02. Decisione di riferimento: [architettura audio](../DECISIONE-ARCHITETTURA-AUDIO.md). Le voci storiche completate in fondo non attestano che il nuovo percorso sia già implementato.

## Architettura e priorità

Producer Python agnostico → motore musicale Python indipendente dalla destinazione → adattatori estensibili → strumenti/sequencer. Snake tramite M4L è la prima prova; gli altri adattatori non devono dipendere da Snake, Live o OSC. La frequenza del replay non scandisce le note.

## Prima integrazione completa

- [x] Publisher metrico neutrale implementato e testato (`trip_metrics.py`, `desnivel-stream-metrics`).
- [x] Ricezione di quota e timestamp in Max e nella patch inserita in Ableton, verificata dall'utente il 2026-10-01.
- [x] Scrittura manuale di `Note_01` tramite `live.object`, verificata il 2026-10-02; range letto 0–83.
- [ ] Salvare nel repository il device M4L modificato in Live: il `.maxpat` presente contiene solo il receiver iniziale.
- [ ] Definire e implementare una regola musicale Python configurabile, separata dal producer: input, stato, risultato e comportamento a dati mancanti/riavvio.
- [ ] Definire il minimo contratto di decisioni musicali indipendente dalla destinazione, distinto dal contratto delle metriche.
- [ ] Implementare l'adattatore Snake e il suo comando OSC, senza nomi di parametri Live nel motore musicale.
- [ ] Ricevere il comando in M4L e applicarlo con `live.object`; verificare associazione della destinazione, range e riapertura del set.
- [ ] Provare la catena completa dal viaggio al suono. L'aggiornamento di pattern completi e l'applicazione sincronizzata sono ancora da verificare.
- [ ] Definire la telemetria per TD soltanto quando serve a visualizzare l'esecuzione musicale effettiva.

Guida operativa: [INTEGRAZIONE-SNAKE.md](../INTEGRAZIONE-SNAKE.md). `live.remote~` è escluso dalla prova corrente dopo i crash osservati; nessuna causa definitiva attribuita.

## Percorsi esistenti

`desnivel-play`, i modulatori e `desnivel-bridge-midi` restano disponibili per il prototipo `/mod/*`. Le loro regole potranno essere riutilizzate separandole dal producer. Non sono il nuovo motore/adattatore già implementato.

Il precedente percorso TouchDesigner → generatore JS è archiviato in [old/td_audio](../../old/td_audio/README.md). Progetti TD e altre implementazioni sono conservati; i riferimenti esterni dei `.toe` non sono stati verificati.

## Metriche e fatti del viaggio

- [x] Contratto metrico definito: `/desnivel/v1/trip/metric/<nome> elapsed_s value`, sei metriche, 1 Hz nel tempo sorgente.
- [x] Gestione della quota completamente assente: `ele`, `slope`, `effort` omessi dal Track; interpolazione delle lacune quando esistono quote valide.
- [ ] Definire fatti neutrali senza priorità compositive MAJOR/MINOR; scegliere nel consumer quali fatti diventano gesti musicali.
- [ ] Separare le interpretazioni riutilizzabili dei modulatori nel motore musicale Python, preservando i percorsi esistenti finché servono.
- [ ] Verificare timeout nel consumer; il receiver dimostrativo mantiene ancora l'ultimo valore.

### Prototipo musicale esistente — non estendere il confine `/mod/*`

- [x] **`MacroModulator` (prototipo)** — produce `macro_scale`, `macro_palette`,
  `macro_register`, `macro_space`, `macro_brightness`.
  Decide modalita' musicale e timbro ("mondo sonoro") sezione per
  sezione della tappa, con policy swappabili
  (`config.macro.policy_name`) + override POI -> bells. Vedi
  `doc/archivio/DESIGN-MACRO.md`.
- [x] **`HarmonyModulator` (prototipo)** — produce `meso_root`. Cambia la
  fondamentale ogni `km_per_change` km lungo una sequenza modale
  configurabile in `HarmonyConfig`. POI override -> ritorno a
  tonica (se `poi_force_tonic`). Anti-flicker via dwell time.
- [x] **`BodyModulator` (prototipo)** — produce `body_euclid_k`, `body_euclid_rot`.
  Pattern ritmici euclidei: k cresce con `journey_energy`, rot
  ruota con `journey_phase`. `n` (default 16) e' convenzione lato
  Ableton, non un canale OSC.

### Priorita' 2: dati statici

- [ ] **Popolare `data/poi.json`** — lanciare `desnivel-discover-poi`
  sul corpus, filtrare i 44k candidati a ~50-100 POI rilevanti.
  Senza questo file il `POIDetector` resta silenzioso (registry
  vuoto). Serve un piccolo tool di filtro (per kind, per nome) per
  non doverlo fare a mano voce per voce.

### Fatti geografici futuri (dopo la prima integrazione)

- [ ] **StopDetector / ResumeDetector** — fatti di sosta/ripartenza su soglia
  velocita'. Combinato con `POIDetector` per ottenere il concetto di
  "visita" (stop dentro un POI).
- [ ] **TerrainDetector** *(fatto di cambiamento del terreno)* — riscritta dal
  metodo `_elevation_only` di `old/terrain_classify.py`.
- [ ] **ExternalEventDetector** — legge `events/<stage>.json` con
  eventi manuali; `USER` indica la sorgente, non una categoria musicale.

### Dati: nuovi classifier (dopo lo spike)

- [ ] **`UrbanClassifier`** — variante `urban` per `start`/`end`
  quando il punto e' dentro un POI del registry. Riusa `POIRegistry`.
- [ ] **`MountainStageClassifier`** — variante `mountain` su tappa con
  quota mediana alta + dislivello positivo grande (es. tappe 10/12).
- [ ] **`InlandClassifier`** — variante `inland` esplicita per tappe
  lontane dalla costa (mediana > 30 km). Polo opposto di
  `coastal`/`sea_view` nei mapping musicali.

### Motore musicale: possibili estensioni (dopo la prima integrazione)

- [ ] **StateMachine** per i canali macro (dwell time, transizioni).
- [ ] **Modulatori meso/body/micro** (LFO, vento corporeo, respiro).
  Decidere quali concretamente solo dopo aver ascoltato i canali
  esistenti.

## Roadmap sink (oltre OSC)

- [ ] **ReplaySink** + flag `--speed` su `run_stage` per playback
  offline da CSV. Utile se il computer che gira la pipeline e quello
  che ospita TD/Ableton sono diversi.

## Roadmap integrazione esterna

- [ ] **Loader meteo** *(da `old/weather_fetch.py`)* — quando servira'
  al layer paesaggio. Modulo autonomo, niente riscrittura: chiamarlo
  come utility.

## Da non fare (scartati)

- `old/audio_mapper.py` — implementazione storica; non riattivarla automaticamente. Le regole su attraversamento di soglie restano ammesse nel nuovo motore configurabile.
- `old/generate_sonic_index.py` — generatore HTML legacy.
- `old/desnivel_gpx_to_td.py` — orchestratore vecchio, sostituito da
  `pipeline.py` + `cli/run_stage.py`.
- Vecchi `test_*.py` in `old/` — concettualmente obsoleti.

## Riferimento (in `old/`, non toccare)

- `old/gpmf_extract.py`, `old/gopro_*.py` — pipeline GoPro indipendente.
- `old/constants.py` — verificare coerenza ad-hoc se servisse un valore.

## Fatto

- [x] **OscSink + CLI `desnivel-play`** (2026-05-12): primo passo
  del Binario A, chiude il loop dati -> OSC. Architettura modulare in
  tre strati: `build_schedule()` funzione pura (testabile senza
  rete), `OscClient` Protocol con `UdpOscClient` (python-osc lazy
  import) e `FakeOscClient` per i test, `OscSink` orchestratore con
  timing wall-clock via `time.monotonic()` e flag `--speed` per
  playback accelerato. Conversione automatica nomi canale ->
  address OSC (`journey_phase` -> `/mod/journey/phase`), eventi su
  `/event/{major,minor}/<kind>` con payload JSON. 11 nuovi test
  (98 totali). CLI `desnivel-play --stage tappa_04 --speed 8`
  funzionante con `--dry-run` per ispezione schedule senza rete.
- [x] Documenti di architettura (`ARCHITETTURA-MUSICALE`, `CONTRATTO-MODULAZIONI`,
  `IMPLEMENTAZIONE`).
- [x] Scaffolding pipeline (config, track, events, modulation, pipeline,
  base Protocols, FileSink, CLI).
- [x] Predisposizione modalità live (`EventSource.USER`, `Event.source_id`).
- [x] `JourneyModulator` (phase, energy, openness) — 6 test.
- [x] Loader GPX completo (parse, geo, derive, resample) — 6 test.
- [x] Riorganizzazione repo (`old/`, `tests/`, `pyproject.toml`).
- [x] Audit `old/` per riuso (questa lista nasce da lì).
- [x] Savitzky-Golay in `_filters.py` (riscritto con pseudoinversa di
  Vandermonde, supporta qualunque `window`/`polyorder`) — 8 test.
- [x] `run_all.py` + report di metriche sul corpus (12 tappe processate,
  journey_* coerente, JSON report opzionale).
- [x] CLI `plot_stage` per ispezionare canali (matplotlib, eventi
  sovrapposti come linee verticali).
- [x] Pacchetto installabile (`pip install -e .`): comandi
  `desnivel-run`, `desnivel-all`, `desnivel-plot` direttamente sul PATH.
  Niente più `PYTHONPATH=src`. Dipendenze opzionali: `[plot]`, `[osc]`, `[dev]`.
- [x] `TensionModulator` (canale `meso_tension`, charge 30s/decay 60s)
  — 6 test, montato in `run_stage` e `run_all`.
- [x] `SummitDetector` (un evento `summit` MAJOR per tappa, prominenza
  topografica massima sopra soglia, non massimo globale) — 7 test.
- [x] `StartDetector` / `EndDetector` (framing obbligatori, sempre presenti,
  bypassano cooldown/cap) — 4 test.
- [x] Architettura **classifier pluggabili** (`EventClassifier` Protocol +
  fusione nel payload, varianti come lista) — 4 test pipeline.
- [x] `ArrivalClimbClassifier` (variante `climb` per `end`, soglia 50m dal
  minimo della seconda metà) — 7 test. Cattura Dogliani, Castel del Monte
  e altri arrivi in collina. Sostituisce `ArrivalClimbDetector` (v0.3).
- [x] Contratto v0.4 (`doc/archivio/CONTRATTO-MODULAZIONI.md`): varianti di
  `start`/`end` via `payload.variants: list[str]`, ritirato `arrival_climb`
  come MAJOR autonomo, MAJOR/tappa 3-5.
- [x] Contratto v0.3 (storico): summit per prominenza, evento
  `arrival_climb` (poi ritirato in v0.4).
- [x] Refactor: helper condivisi `detectors/_elevation.py`
  (`smooth_elevation`, `sample_at`) per evitare duplicazione fra detector.
- [x] **`SeaDetector`** (MAJOR `sea` alla prima discesa sotto 500 m
  dalla costa; tappe gia' costiere non emettono) + **`CoastalClassifier`**
  (variante `coastal` su `end` entro 1000 m dalla costa). Helper
  condiviso `geo/coastline.py` (shapely 2 + pyshp, lazy import,
  haversine in metri). 5+5 test con FakeCoastline (niente shapely nei
  test unit). Verificato sul corpus: tappe 02/04/07 hanno `sea`,
  tappe 02/07/08 hanno `end` coastal.
- [x] **Trittico costiero completo** (2026-05-11): estensione di
  `CoastalClassifier` a `start`+`end`, nuovo `CoastalStageClassifier`
  (carattere costiero per mediana < 1 km, cattura tappa_11
  Peschici-Mattinata che termina nell'entroterra ma percorre la costa
  garganica) e nuovo `SeaViewClassifier` (variante `sea_view` per
  tappe panoramiche in quota: mediana < 5 km dalla costa + quota
  mediana ≥ 150 m + max ≥ 250 m; cattura tappa_04 Cinque Terre).
  Helper condiviso `geo/coast_stats.py` con cache LRU (chiave
  `stage_id` + dimensione, niente `id(track)`). 13 nuovi test.
  Validato su 12 tappe del corpus: 06 e 10 restano puro entroterra
  (mediana 53/58 km dalla costa).
- [x] **POIRegistry + POIDetector** (2026-05-12): sistema unificato
  per città, borghi e landmark come "POI = punto con raggio + metadati
  liberi (`kind`, `tags`)". Helper `geo/poi.py` con query batch
  numpy (haversine), `detectors/poi.py` con cooldown re-entry
  (default 3600 s) per evitare jitter su POI grandi e permettere
  ri-visita significativa. Manifest curato in `data/poi.json`
  (assente = registry vuoto, detector silenzioso). Pre-popolatore
  semi-automatico `tools/discover_poi.py` (`desnivel-discover-poi`,
  optional `[discover]`): una query Overpass per tappa con bbox
  stretto + buffer, dedup globale per (nome, lat·1e4, lon·1e4).
  Niente rete a runtime. 13 nuovi test.

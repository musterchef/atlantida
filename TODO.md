# TODO — DESNIVEL

Tracciamento del lavoro residuo. Le voci sono ordinate per priorità
all'interno di ogni sezione. Quando una voce è completata, spostarla in
fondo sotto `## Fatto` con la data.

## In coda — prossimo

- [ ] **Popolare `data/poi.json`** — lanciare `desnivel-discover-poi`
  sul corpus, rivedere a mano (cancellare paeselli non rilevanti,
  correggere `radius_m`), rinominare. Senza questo file il
  `POIDetector` resta silenzioso (registry vuoto).
- [ ] **`UrbanClassifier`** — variante `urban` per `start`/`end` quando
  il punto è dentro un POI del registry. Riusa `POIRegistry`.
- [ ] **StateMachine** per i canali macro (dwell time, transizioni).
- [ ] **Modulatori meso/body/micro** (LFO, vento corporeo, respiro).

## Roadmap detector

- [ ] **StopDetector / ResumeDetector** — minor events su soglia velocità.
  Combinato con `POIDetector` per ottenere il concetto di "visita"
  (stop dentro un POI).
- [ ] **TerrainDetector** *(minor `territory_change`)* — riscritta dal
  metodo `_elevation_only` di `old/terrain_classify.py`.
- [ ] **ExternalEventDetector** — legge `events/<stage>.json` con eventi
  manuali (categoria USER).

## Roadmap classifier

- [ ] **`MountainStageClassifier`** — variante `mountain` su tappa con
  quota mediana alta + dislivello positivo grande (es. tappe 10/12).
- [ ] **`InlandClassifier`** — variante `inland` esplicita per tappe
  lontane dalla costa (mediana > 30 km). Polo opposto di
  `coastal`/`sea_view` nei mapping musicali.

## Roadmap sink

- [ ] **OscSink** — invio live a TouchDesigner/Ableton (python-osc).
- [ ] **ReplaySink** + flag `--speed` su `run_stage` per playback offline.

## Roadmap integrazione esterna

- [ ] **Patch Ableton / Max for Live** che riceve gli OSC del contratto v0.2.
- [ ] **Loader meteo** *(da `old/weather_fetch.py`)* — quando servirà al
  layer paesaggio. Modulo autonomo, niente riscrittura: chiamarlo come
  utility.

## Da non fare (scartati)

- `old/audio_mapper.py` — logica event-based, sostituita dai modulatori.
- `old/generate_sonic_index.py` — generatore HTML legacy.
- `old/desnivel_gpx_to_td.py` — orchestratore vecchio, sostituito da
  `pipeline.py` + `cli/run_stage.py`.
- Vecchi `test_*.py` in `old/` — concettualmente obsoleti.

## Riferimento (in `old/`, non toccare)

- `old/gpmf_extract.py`, `old/gopro_*.py` — pipeline GoPro indipendente.
- `old/constants.py` — verificare coerenza ad-hoc se servisse un valore.

## Fatto

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
- [x] Contratto v0.4 (`doc/CONTRATTO-MODULAZIONI.md`): varianti di
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

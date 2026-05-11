# TODO — DESNIVEL

Tracciamento del lavoro residuo. Le voci sono ordinate per priorità
all'interno di ogni sezione. Quando una voce è completata, spostarla in
fondo sotto `## Fatto` con la data.

## In coda — prossimo

(da decidere: prossimo modulatore/detector dalla roadmap)

## Roadmap modulatori (da IMPLEMENTAZIONE.md)

- [ ] **StateMachine** per i canali macro (dwell time, transizioni).
- [ ] **Modulatori meso/body/micro** (LFO, vento corporeo, respiro).

## Roadmap detector

- [ ] **SeaDetector** — riusa shapefile `data/coastline/` + logica di
  distanza dalla costa estratta da `old/terrain_classify.py::_coastline_dist`.
  Riscritta in `src/desnivel/detectors/sea.py`.
- [ ] **CityDetector** — riusa logica di sampling + chiamate Wikipedia/Overpass
  da `old/poi_discovery.py`. Riscritta in `src/desnivel/detectors/city.py`.
- [ ] **StopDetector / ResumeDetector** — minor events su soglia velocità.
- [ ] **TerrainDetector** *(minor `territory_change`)* — riscritta dal
  metodo `_elevation_only` di `old/terrain_classify.py`.
- [ ] **ExternalEventDetector** — legge `events/<stage>.json` con eventi
  manuali (categoria USER).

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

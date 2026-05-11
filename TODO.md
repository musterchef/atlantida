# TODO — DESNIVEL

Tracciamento del lavoro residuo. Le voci sono ordinate per priorità
all'interno di ogni sezione. Quando una voce è completata, spostarla in
fondo sotto `## Fatto` con la data.

## In coda — prossimo

- [ ] **Pacchetto installabile** *(piccolo, opzionale)*
  Aggiungere `[project]` minimale a `pyproject.toml` così `pip install -e .`
  permette `python -m desnivel.cli.run_all` senza `PYTHONPATH=src`.

## Roadmap modulatori (da IMPLEMENTAZIONE.md)

- [ ] **TensionModulator** — usa `asymmetric_leaky_integrator` già pronto;
  emette `/mod/meso/tension`.
- [ ] **StateMachine** per i canali macro (dwell time, transizioni).
- [ ] **Modulatori meso/body/micro** (LFO, vento corporeo, respiro).

## Roadmap detector

- [ ] **SummitDetector** — un evento `summit` per tappa (massimo globale con
  prominenza ≥ 50 m).
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

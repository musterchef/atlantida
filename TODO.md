# TODO — DESNIVEL

Tracciamento del lavoro residuo. Le voci sono ordinate per priorità
all'interno di ogni sezione. Quando una voce è completata, spostarla in
fondo sotto `## Fatto` con la data.

## Architettura: chi fa cosa

Python e' il direttore d'orchestra: legge GPX, decide quali eventi
accadono e a che intensita' modulare i canali. TD e Ableton ricevono
via OSC e sono organi sensoriali (visual, audio). Una sola fonte di
verita', niente logica musicale dentro TD o Ableton.

```
   Python pipeline (DESNIVEL) ──OSC──> TD (visual)
                              ──OSC──> Ableton/M4L (audio)
                              ──OSC──> ... (luci, altro)
```

## Binario A — Integrazione (priorita' ora)

Lo scopo di questo binario e' **chiudere il loop**: dati -> OSC ->
qualcosa che si vede/sente. Anche minimale: serve per capire cosa
funziona musicalmente prima di accumulare altri detector.

### Contratto Ableton: bridge MIDI ora, M4L dopo

**Destinazione finale = patch Max for Live nativo** che riceve OSC
direttamente e modula parametri Live con risoluzione piena.

**Step provvisorio = bridge OSC→MIDI in Python** per arrivare
all'ascolto in mezz'ora senza scrivere Max. Decisione presa
consapevolmente: serve a iterare e capire quali canali sono
musicalmente sensati. Quando lo sappiamo, il bridge si butta.

Vincoli sul bridge perche' sia "buttabile senza rimpianti":

1. **Stesso contratto OSC** del futuro M4L. Il bridge legge gli stessi
   `/mod/<group>/<name>` e `/event/...` definiti in
   `CONTRATTO-MODULAZIONI.md`. Niente address custom solo-per-MIDI.
2. **Mapping canale -> CC# dichiarativo**, in un dict piccolo nel
   bridge. E' una tabella di traduzione, non logica musicale: nessun
   smoothing, nessun re-scaling oltre il cast a 7-bit. La logica
   musicale resta in Python.
3. **Nessun nuovo canale** introdotto per far stare le cose nel
   bridge. Se un canale non si mappa bene a un CC (es. payload
   evento con testo), il bridge lo lascia perdere e lo recupereremo
   in M4L. Documentare cosa si perde.
4. **Zero stato in Ableton "implicito"**: i mapping MIDI Map sono
   manuali e per loro natura non versionati. Tutto cio' che e'
   significativo resta su file Python. Ableton fa solo
   sound-design, non logica.
5. **Codice in `src/desnivel/bridges/osc_to_midi.py` isolato**: non
   tocca pipeline ne' sink. Quando M4L sara' pronto, si cancella il
   file e basta.

### Passi concreti

- [x] **`OscToMidiBridge` + CLI `desnivel-bridge-midi`** — server
  `python-osc` + `mido`, mapping canali->CC dichiarativo, eventi
  `/event/major/*` -> Note On su canale 16. Stampa mappa all'avvio.
- [ ] **M4L canarino (target finale)**: device Max for Live che
  riceve OSC direttamente sui canali della pipeline. Sostituisce il
  bridge. A quel punto si cancella `bridges/osc_to_midi.py` e
  l'entry point in `pyproject.toml`. Vincolo: deve consumare
  **esattamente lo stesso contratto OSC** (`/mod/<group>/<name>`,
  `/event/<bus>/<kind>`) che useranno anche TD e qualsiasi altro
  client.
- [ ] **Patch TD canarino** — *rimandato* su richiesta utente.
  Si fara' dopo che il sound design Ableton sara' stabile. Vincolo
  fondamentale: **ogni modulator/detector aggiunto al Binario B deve
  restare compatibile con TD**, cioe' niente address custom solo per
  Ableton, niente smoothing dentro il bridge, niente logica musicale
  asimmetrica fra i due client. La pipeline e' unica.

## Binario B — Dati (in corso)

Regola fondamentale: ogni canale aggiunto qui deve essere **agnostico
sul client**. La pipeline emette su OSC, Ableton ascolta tramite
bridge MIDI, TD ascolter? in futuro direttamente. Non si scrive nulla
"solo per Ableton" o "solo per TD".

### Priorita' 1: nuovi modulator (sblocca canali silenti)

- [x] **`MacroModulator`** — sblocca `macro_scale`, `macro_palette`,
  `macro_register`, `macro_space`, `macro_brightness`.
  Decide modalita' musicale e timbro ("mondo sonoro") sezione per
  sezione della tappa, con policy swappabili
  (`config.macro.policy_name`) + override POI -> bells. Vedi
  `doc/DESIGN-MACRO.md`.
- [ ] **`HarmonyModulator`** — sblocca `meso_root`. Cambia la
  fondamentale ogni N km o su trigger (POI, summit).
- [ ] **`BodyModulator`** — sblocca `body_euclid_k`, `body_euclid_rot`.
  Pattern ritmici euclidei. Da fare dopo il MacroModulator e dopo
  almeno una sessione di sound design su Ableton.

### Priorita' 2: dati statici

- [ ] **Popolare `data/poi.json`** — lanciare `desnivel-discover-poi`
  sul corpus, filtrare i 44k candidati a ~50-100 POI rilevanti.
  Senza questo file il `POIDetector` resta silenzioso (registry
  vuoto). Serve un piccolo tool di filtro (per kind, per nome) per
  non doverlo fare a mano voce per voce.

### Dati: nuovi detector (dopo lo spike)

- [ ] **StopDetector / ResumeDetector** — minor events su soglia
  velocita'. Combinato con `POIDetector` per ottenere il concetto di
  "visita" (stop dentro un POI).
- [ ] **TerrainDetector** *(minor `territory_change`)* — riscritta dal
  metodo `_elevation_only` di `old/terrain_classify.py`.
- [ ] **ExternalEventDetector** — legge `events/<stage>.json` con
  eventi manuali (categoria USER).

### Dati: nuovi classifier (dopo lo spike)

- [ ] **`UrbanClassifier`** — variante `urban` per `start`/`end`
  quando il punto e' dentro un POI del registry. Riusa `POIRegistry`.
- [ ] **`MountainStageClassifier`** — variante `mountain` su tappa con
  quota mediana alta + dislivello positivo grande (es. tappe 10/12).
- [ ] **`InlandClassifier`** — variante `inland` esplicita per tappe
  lontane dalla costa (mediana > 30 km). Polo opposto di
  `coastal`/`sea_view` nei mapping musicali.

### Dati: nuovi modulatori (dopo lo spike)

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

- `old/audio_mapper.py` — logica event-based, sostituita dai modulatori.
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

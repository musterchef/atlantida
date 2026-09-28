# TODO — DESNIVEL

Tracciamento del lavoro residuo. Le voci sono ordinate per priorità
all'interno di ogni sezione. Quando una voce è completata, spostarla in
fondo sotto `## Fatto` con la data.

## Architettura: chi fa cosa

Python legge il GPX e produce metriche e fatti del viaggio via OSC. Max for Live /
Ableton interpreta quei segnali, mantiene i sequencer e genera l'audio.
TouchDesigner visualizza la musica e non inoltra i dati GPX ad Ableton.
Decisione accettata e stato dei percorsi: `doc/DECISIONE-ARCHITETTURA-AUDIO.md`.

```
  GPX -> Python pipeline (DESNIVEL) ──OSC──> Max for Live / Ableton (audio)
                                 |
                                 +── telemetria musicale ──> TD (visual)
```

## Binario A — Integrazione (priorita' ora)

Lo scopo di questo binario e' **chiudere il loop**: dati -> OSC ->
qualcosa che si vede/sente. Anche minimale: serve per capire cosa
funziona musicalmente prima di accumulare altri detector.

### Percorso audio e bridge di test

**Percorso audio scelto = Python -> OSC -> Max for Live / Ableton.**
M4L riceve il contratto OSC e ospita i sequencer autonomi. TouchDesigner
non e' nel percorso audio; puo' ricevere telemetria musicale per la visualizzazione.

**Bridge OSC→MIDI = strumento provvisorio di test.** Non e' il consumer
audio definitivo e non sostituisce i sequencer M4L.

Il percorso storico TouchDesigner -> `/desnivel/*` -> M4L e' legacy.
Resta disponibile durante la transizione, ma non va esteso come percorso
principale. Non rimuoverlo prima della prova verticale Python -> OSC ->
M4L -> audio. Vedi `doc/DECISIONE-ARCHITETTURA-AUDIO.md`.

Vincoli sul bridge perche' sia "buttabile senza rimpianti":

1. **Adattatore del prototipo corrente**: il bridge traduce solo i
  messaggi che il prototipo `/mod/*` sa rappresentare in MIDI. Non
  definisce ne' vincola il namespace OSC neutrale futuro.
2. **Mapping canale -> CC# dichiarativo** nel bridge di test. La
  conversione necessaria al trasporto MIDI (inclusa la codifica di
  range signed) va dichiarata e testata; il bridge non applica
  smoothing ne' decide comportamenti musicali.
3. **Nessun nuovo canale** introdotto solo per far stare i dati nel
  bridge. Se una metrica o un payload descrittivo non si mappa bene a
  un CC, il bridge lo omette; il consumer M4L target dovra' leggere il
  contratto neutrale completo.
4. **Responsabilita' separate**: Python produce metriche e fatti del
  viaggio; M4L interpreta quei segnali, contiene i sequencer e decide
  come generare note. I parametri del sequencer devono essere espliciti
  e documentati; M4L non duplica parsing e derivazione GPX.
5. **Codice in `src/desnivel/bridges/osc_to_midi.py` isolato**: non
  tocca pipeline ne' sink. Il bridge resta solo un tool di test;
  rimuoverlo in futuro e' una decisione separata, non un requisito
  per attivare M4L.

### Passi concreti

- [x] **`OscToMidiBridge` + CLI `desnivel-bridge-midi`** — server
  `python-osc` + `mido`, mapping canali->CC dichiarativo, eventi
  `/event/major/*` -> Note On su canale 16. Stampa mappa all'avvio.
- [ ] **M4L canarino (percorso audio scelto)**: device Max for Live che
  riceve direttamente il contratto neutrale di metriche e genera note con
  sequencer autonomi. Il primo test usa metriche, non fatti/eventi. Procedere
  in ordine: ricezione OSC osservabile senza audio; un solo layer autonomo;
  prova end-to-end senza TD. Ogni default M4L deve essere un parametro
  esplicito; niente numeri nascosti nel patch. Il bridge MIDI resta
  strumento di test finche' M4L non e' verificato. Le regole musicali
  (root, scala, palette, pattern) sono interpretazioni del consumer, non
  canali prodotti da Python.
- [ ] **Telemetria M4L -> TD** per visualizzare la musica generata.
  Definire schema e frequenza quando sara' progettato il primo consumer
  M4L. TD non deve inoltrare i dati GPX al percorso audio.
- [x] **Implementare publisher del pilot metrico**: `python -m desnivel.cli.stream_metrics`
  invia il catalogo neutrale a 1 Hz; metriche e serializzazione hanno test.
- [ ] **Prova con receiver OSC reale**: verificare indirizzi/argomenti nel
  receiver M4L prima di implementare la generazione delle note.

## Binario B — Metriche viaggio (producer neutrale)

Regola fondamentale: Python pubblica misure e fatti con semantica di
viaggio, non mappature sonore. M4L, TD e altri consumer possono
reinterpretare gli stessi segnali secondo il proprio scopo. Lo stato
dei canali `/mod/*` musicali gia' implementati e la migrazione sono
registrati in `doc/STATO-CONTRATTO-OSC.md`.

### Priorita' 1: definire il contratto neutrale

- [x] **Catalogo e publisher metriche OSC** — campi da `Track.samples`;
  namespace `/desnivel/v1/trip/metric/<nome>`, pacchetto `(elapsed_s, value)`
  a 1 Hz; codice in `trip_metrics.py` e `sinks/trip_metrics_osc.py`.
- [ ] **Separare producer e interpretazioni** — migrare root/scale/palette/
  registro/pattern dai modulatori Python ai consumer appropriati, dopo aver
  definito il primo mapping M4L e aver mantenuto test di regressione.
- [ ] **Eventi neutrali** — mantenere fatti geografici e payload descrittivi;
  non codificare nel producer un gesto audio specifico.
- [x] **Quota assente nel GPX** — il parser conserva il mancante; il loader
  interpola buchi isolati tra quote note e omette `ele`, `slope`, `effort`
  quando la traccia non contiene alcuna quota.

### Prototipo musicale esistente — non estendere il confine `/mod/*`

- [x] **`MacroModulator` (prototipo)** — produce `macro_scale`, `macro_palette`,
  `macro_register`, `macro_space`, `macro_brightness`.
  Decide modalita' musicale e timbro ("mondo sonoro") sezione per
  sezione della tappa, con policy swappabili
  (`config.macro.policy_name`) + override POI -> bells. Vedi
  `doc/DESIGN-MACRO.md`.
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

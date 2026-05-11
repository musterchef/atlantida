# DESNIVEL — Specifica di implementazione (Python)

> Decisioni tecniche per i moduli Python del nuovo sistema musicale.
> Riferimenti: [ARCHITETTURA-MUSICALE.md](ARCHITETTURA-MUSICALE.md), [CONTRATTO-MODULAZIONI.md](CONTRATTO-MODULAZIONI.md).

---

## 1. Decisioni di fondo

### 1.1 Eventi come oggetti estensibili, non come enum
Gli eventi **non sono** un elenco chiuso codificato in tabella. Sono **oggetti** con un nucleo di campi comuni (cosa, dove, quando) e una parte estendibile (payload arbitrario). Nuovi tipi di evento si aggiungono dichiarandone uno nel registry: nessuna modifica al codice della pipeline.

Il sistema deve poter accogliere qualunque tipo di evento, dai più ovvi (`summit`, `sea`, `city_arrival`, `start`, `end`) a quelli liberi e contestuali come `pioggia_torrenziale`, `pedalata_al_buio`, `derby_allo_stadio`, `treno_preso_al_volo`. Tutti questi convivono nello stesso modello dati.

Il design tiene esplicitamente conto del fatto che in futuro vorremo un **editor di eventi** (CLI o web). Per questo:

- ogni `kind` di evento è dichiarato in un **registry centrale** che ne descrive nome leggibile, categoria di default e schema del payload (campi, tipi, default);
- gli eventi di una tappa vivono in un **file separato dal codice**, in formato JSON validato da JSON Schema;
- l'editor (futuro) legge il registry per generare la UI dei campi, e scrive lo stesso file JSON che la pipeline consuma.

### 1.2 Stile di codice: pipeline di trasformatori
Ogni modulo è una **classe trasformatore** con un'interfaccia uniforme:

- riceve un `Track` (oggetto immutabile con i dati grezzi e le metriche già calcolate della tappa);
- restituisce nuovi canali (Series) o eventi (lista di `Event`), senza modificare l'input.

I trasformatori si compongono in una pipeline lineare. Ogni trasformatore è puro: stesso input → stesso output. Questo rende **tutto testabile** in isolamento.

### 1.3 Una sola configurazione, in un solo posto
Tutti i numeri (τ smoothing, soglie, cooldown, frequenze OSC, intensità default) vivono in **un unico file di configurazione tipato**, importabile da qualunque modulo. Niente costanti sparse. Niente magic number nei moduli.

### 1.4 Output doppio: file e OSC
Ogni modulo può funzionare in due modalità senza modifiche al proprio codice:

- **offline**: produce un CSV/JSON delle modulazioni e una lista JSON di eventi per l'intera tappa. Permette di ascoltare e analizzare il risultato prima di toccare TouchDesigner.
- **online**: spinge gli stessi valori via OSC in tempo reale (o in simulazione di tempo reale).

I due output vivono fuori dai trasformatori, come **sink** intercambiabili.

### 1.5 Disaccoppiamento dei clock
La pipeline lavora sempre su una **griglia temporale uniforme** ricampionata (es. 10 Hz interno), non sui timestamp irregolari del GPX. Questo elimina alla radice tutti i problemi di sample rate variabile e rende deterministici gli smoothing.

---

## 2. Modello dei dati

### 2.1 `Track` — dati di ingresso
Oggetto immutabile (`dataclass(frozen=True)`) con:
- `stage_id`: identificatore tappa (es. `"tappa_01"`)
- `start_time`, `end_time`: estremi temporali
- `samples`: `DataFrame` ricampionato a frequenza fissa con colonne note (`t`, `lat`, `lon`, `ele`, `speed`, `slope`, `terrain`, `flow`, `effort`, ...).
- `metadata`: dizionario libero (meteo, luce, città attraversate, eventi esogeni dichiarati esternamente — es. il derby).

### 2.2 `ModulationFrame` — canali continui di uscita
`DataFrame` con colonna `t` e una colonna per ogni canale del contratto (`journey_phase`, `macro_scale`, `meso_density`, ...).
Ogni trasformatore continuo aggiunge colonne a questo frame.

### 2.3 `Event` — evento estendibile
Classe base con i **campi essenziali e nient'altro**:

```python
@dataclass(frozen=True)
class Event:
    kind: str              # identificatore registrato, es. "summit"
    category: EventCategory  # MAJOR | MINOR
    t: float               # tempo dall'inizio della tappa (s)
    location: GeoPoint | None  # lat, lon, ele (se geograficamente localizzato)
    payload: dict          # campi specifici del tipo, validati dal registry
```

`EventCategory` è solo `MAJOR` o `MINOR` (rispecchia la suddivisione del contratto).

Il `kind` non è una stringa libera: deve essere registrato in `events.registry`. Il registry definisce per ogni `kind`:

- `label`: nome leggibile per l'editor
- `default_category`: `MAJOR` o `MINOR`
- `payload_schema`: JSON Schema dei campi del payload (per validazione e per generare la UI dell'editor)
- `source`: `"derived"` (calcolato dai dati GPX) o `"external"` (dichiarato nel file della tappa)

Nuovi tipi di evento si aggiungono **solo nel registry**, senza toccare la pipeline:

```python
register_event(
    kind="pioggia_torrenziale",
    label="Pioggia torrenziale",
    default_category=EventCategory.MINOR,
    source="external",
    payload_schema={
        "type": "object",
        "properties": {
            "mm_per_h": {"type": "number", "minimum": 0},
            "durata_min": {"type": "number", "minimum": 0},
        },
        "required": ["mm_per_h"],
    },
)
```

Il futuro editor legge il registry e sa esattamente quali campi presentare all'utente per ciascun tipo.

### 2.4 `EventDetector` — interfaccia per rilevatori
Un `EventDetector` è una qualunque classe che espone:
```python
def detect(self, track: Track) -> Iterable[Event]: ...
```
La pipeline degli eventi è semplicemente una **lista** di detector. Ogni detector è responsabile di un tipo di evento (o di una famiglia). Aggiungere un nuovo evento *derivato dai dati* significa scrivere un nuovo detector. Aggiungere un nuovo evento *esterno* (dichiarato dall'autore) significa solo registrarlo nel registry e scriverlo nel file della tappa.

Esistono due famiglie di detector:
- **Derivati dai dati** (`SummitDetector`, `SeaDetector`, `StopDetector`, ecc.): producono eventi a partire dalle metriche calcolate.
- **Esterni** (`ExternalEventDetector`): leggono il file `events/<stage>.json` della tappa e producono `Event` dichiarati dall'autore. È così che entrano `derby_allo_stadio`, `treno_preso_al_volo`, `pioggia_torrenziale`.

---

## 3. Architettura dei moduli

```
src/desnivel/
  __init__.py
  config.py              # tutte le costanti, in un solo posto
  track.py               # Track, GeoPoint, dataclasses
  events.py              # Event, EventCategory, registry
  resampler.py           # ricampionamento a griglia fissa
  pipeline.py            # composizione dei trasformatori
  modulators/
    __init__.py
    base.py              # interfaccia Modulator
    journey.py           # JourneyModulator -> /mod/journey/*
    tension.py           # TensionIntegrator -> /mod/meso/tension
    state.py             # StateMachine -> /mod/macro/*
    meso.py              # MesoModulator -> /mod/meso/*
    body.py              # BodyModulator -> /mod/body/*
    micro.py             # MicroModulator -> /mod/micro/*
  detectors/
    __init__.py
    base.py              # interfaccia EventDetector
    summit.py
    sea.py
    city.py
    stop.py
    territory.py
    external.py          # legge eventi dichiarati nel metadata
  sinks/
    __init__.py
    base.py              # interfaccia Sink
    file_sink.py         # scrive CSV+JSON
    osc_sink.py          # invia OSC live
    replay_sink.py       # invia OSC simulando il tempo reale
  cli/
    run_stage.py         # CLI: processa una tappa
    run_all.py           # CLI: processa tutte le tappe
```

I file Python esistenti non vengono toccati in questa fase. La nuova pipeline cresce in parallelo nella sottocartella `desnivel/`.

---

## 3.1 Sink e CLI

Tre sink concreti, intercambiabili:

- `FileSink` — scrive `output/<stage>_modulations.csv` e `output/<stage>_events.json`.
- `OscSink` — calcola e invia in tempo reale, con flag `--speed` per accelerare.
- `ReplaySink` — rilegge gli output di `FileSink` e li riemette via OSC (nessun ricalcolo).

CLI:

```
run_stage.py --stage tappa_01 --sink file
run_stage.py --stage tappa_01 --sink osc [--speed 1.0]
run_stage.py --stage tappa_01 --sink replay --from-file output/tappa_01_modulations.csv
run_stage.py --stage tappa_01 --sink osc --range 1200 1500   # solo un sotto-intervallo
run_all.py                                                    # batch su tutte le tappe + report
```

La scelta di tre sink (e non due) è deliberata: separa il calcolo dalla riproduzione. Una volta calcolata una tappa con `FileSink`, si può ascoltarla via `ReplaySink` infinite volte senza ricalcolare nulla, anche scrubbando.

---

## 4. Interfacce minime (forma, non implementazione)

```python
# modulators/base.py
class Modulator(Protocol):
    output_columns: tuple[str, ...]
    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame: ...

# detectors/base.py
class EventDetector(Protocol):
    def detect(self, track: Track) -> Iterable[Event]: ...

# sinks/base.py
class Sink(Protocol):
    def emit(self, frame: ModulationFrame, events: list[Event]) -> None: ...
```

Una pipeline completa è la composizione di tre liste: `modulators`, `detectors`, `sinks`. Si configurano dichiarativamente nel CLI.

---

## 5. Configurazione centralizzata

Tutto in `src/desnivel/config.py`. Tipato con `dataclass`. Caricabile da YAML opzionale per esperimenti, ma con default sensati.

```python
@dataclass(frozen=True)
class TimingConfig:
    internal_rate_hz: float = 10.0        # frequenza interna di ricampionamento

@dataclass(frozen=True)
class SmoothingConfig:
    macro_tau_s: float = 90.0             # memoria smoothing macro
    macro_dwell_s: float = 60.0           # permanenza minima di uno stato macro
    meso_tau_s: float = 8.0
    micro_tau_s: float = 0.2
    tension_charge_tau_s: float = 30.0    # con quale velocità si carica
    tension_decay_tau_s: float = 60.0     # con quale velocità decade

@dataclass(frozen=True)
class EventConfig:
    # vincoli musicali assoluti (fissi)
    major_max_per_stage: int = 5
    major_target_per_stage: int = 4         # bersaglio per derivare il cooldown
    minor_target_per_stage: int = 12        # bersaglio per derivare il cooldown
    minor_cooldown_min_s: float = 90.0      # mai sotto questo, anche per tappe brevissime
    major_cooldown_min_s: float = 300.0     # 5 minuti, mai sotto
    # soglie fisiche (fisse, non dipendono dalla tappa)
    stop_speed_threshold_kmh: float = 2.0
    stop_min_duration_s: float = 30.0
    summit_min_prominence_m: float = 50.0
    sea_distance_threshold_m: float = 500.0
    territory_stable_window_s: float = 20.0

    def major_cooldown_s(self, stage_duration_s: float) -> float:
        """Cooldown derivato dalla durata della tappa."""
        return max(self.major_cooldown_min_s,
                   stage_duration_s / (self.major_target_per_stage * 1.5))

    def minor_cooldown_s(self, stage_duration_s: float) -> float:
        return max(self.minor_cooldown_min_s,
                   stage_duration_s / (self.minor_target_per_stage * 1.5))

@dataclass(frozen=True)
class OscConfig:
    host: str = "127.0.0.1"
    port: int = 9000
    rates_hz: dict = field(default_factory=lambda: {
        "journey": 0.2, "macro": 1.0, "meso": 4.0,
        "body": 2.0, "micro": 15.0,
    })

@dataclass(frozen=True)
class Config:
    timing: TimingConfig = TimingConfig()
    smoothing: SmoothingConfig = SmoothingConfig()
    events: EventConfig = EventConfig()
    osc: OscConfig = OscConfig()

DEFAULT_CONFIG = Config()
```

I numeri sopra sono **proposte iniziali allineate al contratto v0.2**. Si modificano solo qui.

Nota sui parametri di rarità degli eventi: `major_cooldown_s` e `minor_cooldown_s` **non sono fissi**, sono derivati dalla durata della tappa. Tappe brevi avranno cooldown corti (ma mai sotto i minimi); tappe lunghe avranno cooldown più ampi. Così ogni tappa ha indicativamente lo stesso *numero* di eventi, indipendentemente dalla sua lunghezza. I parametri fisici (soglia velocità, distanza dalla costa, prominence) restano invece fissi: non hanno motivo di scalare con la tappa.

---

## 6. Testabilità

### 6.1 Unit test puri
Ogni `Modulator` e ogni `EventDetector` sono pure functions di `Track → output`. Si testano con `Track` sintetici (sequenze costruite a mano).

Esempi di test minimi:
- `JourneyModulator` su una tappa di 1000 s produce `phase` monotona da 0 a 1.
- `TensionIntegrator`: con uno sforzo a gradino, l'output sale e poi decade con la costante di tempo attesa (tolleranza ±10%).
- `StateMachine`: due cambi di terreno entro la finestra di stabilità producono **un solo** cambio di stato.
- `SummitDetector`: una tappa con tre massimi locali sopra la soglia di prominence produce esattamente tre eventi.
- `EventConfig.major_max_per_stage`: se i detector producono più di N eventi maggiori, ne sopravvivono solo gli N più significativi.

### 6.2 Smoke test sulla tappa
Un test di alto livello prende `tappa_01`, esegue l'intera pipeline e verifica invarianti grossolane:
- `phase` è monotona e finisce a 1.0;
- nessun canale ha NaN;
- numero di eventi maggiori ≤ 5;
- distanza minima tra eventi maggiori ≥ `major_cooldown_s`;
- nessun canale macro ha più di X transizioni nella tappa.

### 6.3 Test sull'intero corpus
CLI `run_all.py` esegue la pipeline su tutte le tappe e produce un **report di riepilogo** (un JSON di metriche per tappa): numero di eventi, statistiche delle transizioni, distribuzione dei valori. Permette di valutare a colpo d'occhio se una modifica della config ha effetti sensati.

### 6.4 Replay deterministico
`ReplaySink` legge un `ModulationFrame` + lista di `Event` da file e li riemette via OSC simulando il tempo reale. Significa che la pipeline si esegue **una sola volta** in offline, e si può poi ascoltare in Ableton più volte senza ricalcolare nulla, anche scrubbando o accelerando.

---

## 7. Eventi esterni — esempio concreto

Per supportare `derby_allo_stadio`, `treno_preso_al_volo`, `pioggia_torrenziale`, ecc. senza scrivere codice ad hoc:

Si crea un file accanto al GPX, es. `events/tappa05.json`:

```json
{
  "$schema": "../doc/event-schema.json",
  "stage": "tappa05",
  "events": [
    {
      "kind": "derby_allo_stadio",
      "category": "major",
      "at_time": "2026-04-12T18:42:00",
      "location": { "lat": 44.493, "lon": 11.309 },
      "payload": { "teams": ["Bologna", "Inter"], "intensity": 0.9 }
    },
    {
      "kind": "treno_preso_al_volo",
      "category": "minor",
      "at_time": "2026-04-12T19:55:00",
      "payload": { "line": "Bologna-Ancona" }
    },
    {
      "kind": "pioggia_torrenziale",
      "category": "minor",
      "at_time_range": ["2026-04-12T15:20:00", "2026-04-12T16:00:00"],
      "payload": { "mm_per_h": 35 }
    }
  ]
}
```

Il file è validato da JSON Schema (sia globale, sia per il payload di ciascun `kind` in base al registry). `ExternalEventDetector` lo legge e produce `Event`. Il futuro editor scriverà lo stesso identico file leggendo il registry per sapere quali campi presentare all'utente.

Formato JSON e non YAML proprio in vista dell'editor: parsing senza ambiguità, supportato nativamente dal browser, compatibile con JSON Schema senza estensioni.

---

## 8. Ordine di implementazione

Per avere risultati ascoltabili il prima possibile:

1. **Scaffolding minimo**: `config.py`, `track.py`, `events.py`, `pipeline.py`, `sinks/file_sink.py`, `cli/run_stage.py`. Senza nessun modulatore: produce solo un CSV vuoto.
2. **`resampler.py`**: ricampionamento del GPX a griglia fissa. Si verifica che `Track.samples` sia regolare.
3. **`modulators/journey.py`**: il più semplice, produce `phase`, `energy`, `openness`. Si verifica visivamente la curva.
4. **`sinks/osc_sink.py` + `replay_sink.py`**: a questo punto si può già ascoltare `/mod/journey/*` in TouchDesigner/Ableton.
5. **`modulators/tension.py`**: integratore con carica/decadimento.
6. **`modulators/state.py`**: macchina a stati con dwell time. Produce `macro_scale`, `macro_palette`.
7. **`detectors/summit.py`, `sea.py`, `city.py`, `stop.py`, `territory.py`** + filtro `major_max_per_stage`.
8. **`detectors/external.py`**: lettura YAML.
9. **`modulators/meso.py`, `body.py`, `micro.py`**: si chiudono i canali rimanenti del contratto.
10. **`cli/run_all.py`** con report di riepilogo.

Ogni step è autonomamente testabile e produce un output osservabile (file o OSC). Si può fermarsi a qualunque step e avere già un sistema funzionante, semplicemente con meno canali.

---

## 9. Cosa non si fa in questa fase

- Non si tocca la patch Max for Live finché OSC live non emette dati conformi al contratto.
- Non si introducono nuove dipendenze pesanti. Le uniche necessarie: `numpy`, `pandas`, `python-osc`, `jsonschema`.
- Non si costruisce ancora l'editor di eventi: si predispone solo il modello dati e lo schema che lo renderà immediato.

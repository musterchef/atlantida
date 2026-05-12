"""Configurazione centralizzata.

Unico punto in cui vivono tutti i parametri numerici del sistema.
I valori di default sono allineati al contratto v0.2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class TimingConfig:
    """Tempi e frequenze di base della pipeline."""

    internal_rate_hz: float = 10.0
    """Frequenza di ricampionamento interno (Hz)."""


@dataclass(frozen=True)
class SmoothingConfig:
    """Costanti di tempo degli smoothing per scala temporale."""

    macro_tau_s: float = 90.0
    macro_dwell_s: float = 60.0
    meso_tau_s: float = 8.0
    micro_tau_s: float = 0.2
    tension_charge_tau_s: float = 30.0
    tension_decay_tau_s: float = 60.0


@dataclass(frozen=True)
class JourneyConfig:
    """Parametri della scala di arco di tappa.

    L'arco di tappa evolve molto lentamente: queste costanti di tempo
    sono dell'ordine dei minuti, non dei secondi.
    """

    energy_charge_tau_s: float = 300.0
    """Memoria di carica dell'energia accumulata sull'intera tappa."""
    energy_decay_tau_s: float = 600.0
    """Memoria di rilascio dell'energia."""
    openness_base: float = 0.2
    """Valore minimo di apertura, a inizio tappa."""
    openness_phase_weight: float = 0.5
    """Quanto l'apertura cresce con l'avanzare della tappa (0..1)."""
    openness_energy_weight: float = 0.3
    """Quanto l'apertura aumenta con l'energia accumulata (0..1)."""
    effort_channel: str = "effort"
    """Nome del canale di Track.samples da cui leggere lo sforzo.
    Se assente, l'energia resta a zero."""


@dataclass(frozen=True)
class MacroConfig:
    """Parametri del MacroModulator (sezioni macro-temporali della tappa).

    Le soglie di bucketing (quota, varianza) sono **derivate dalla tappa
    stessa** via percentili, cosi' che ogni tappa "viva" nei propri
    estremi. Le costanti qui sotto governano solo il *come* si calcola
    e si stabilizza l'output, non il *cosa*.

    Vedi `modulators/macro_policies.py` per le tabelle musicali e
    `doc/DESIGN-MACRO.md` per il design completo.
    """

    policy_name: str = "default"
    """Nome della `MacroPolicy` da usare (vedi macro_policies.POLICIES)."""

    elev_percentiles: tuple[float, float] = (33.0, 67.0)
    """Percentili (su tutta la tappa) per dividere la quota mediana di
    sezione in 3 bucket (basso/medio/alto). 33/67 = terzili."""

    var_percentile: float = 60.0
    """Percentile sopra il quale la varianza locale e' considerata
    "mossa". Default 60 = solo il 40% delle sezioni piu' irregolari
    cade in `var_bucket=1`."""

    section_window_s: float = 60.0
    """Finestra mobile (s) per quota mediana e std-dev locali. E' la
    grana percettiva delle sezioni macro."""

    fallback_palette: int = 0
    fallback_scale: int = 1
    """Valori usati se la tappa e' troppo corta o senza elevation."""

    elevation_channel: str = "ele"
    openness_channel: str = "journey_openness"
    """Nomi dei canali sorgente (in track.samples e in frame.channels)."""

    poi_registry_path: str | None = None
    """Path al `data/poi.json` per il `palette` override sui POI.
    Se None o file assente, override disattivato."""


@dataclass(frozen=True)
class EventConfig:
    """Parametri degli eventi.

    I cooldown sono *derivati* dalla durata della tappa (vedi metodi),
    così che ogni tappa abbia indicativamente lo stesso numero di eventi
    indipendentemente dalla sua durata. Le soglie fisiche (velocità,
    prominence, distanze) restano invece fisse: non scalano con la tappa.
    """

    major_max_per_stage: int = 5
    major_target_per_stage: int = 4
    minor_target_per_stage: int = 12

    major_cooldown_min_s: float = 300.0
    minor_cooldown_min_s: float = 90.0

    stop_speed_threshold_kmh: float = 2.0
    stop_min_duration_s: float = 30.0
    summit_min_prominence_m: float = 50.0
    arrival_climb_min_delta_m: float = 50.0
    """Dislivello finale (m) sopra il quale una tappa che termina in
    salita emette `arrival_climb`. Misurato rispetto al minimo della
    seconda metà della tappa."""
    sea_distance_threshold_m: float = 500.0
    """Soglia per il MAJOR `sea`: la prima volta che la distanza dalla
    costa scende sotto questo valore, emette l'evento. Tappe che
    iniziano già sotto soglia non emettono (non c'è "arrivo al mare":
    semmai è una tappa costiera, lavoro del classifier)."""
    sea_detector_eval_rate_hz: float = 1.0
    """Frequenza di valutazione del SeaDetector. 1 Hz è sufficiente per
    cogliere la "prima volta sotto soglia" e taglia il costo di un
    ordine di grandezza rispetto al sample rate interno (10 Hz)."""
    coastal_arrival_threshold_m: float = 1000.0
    """Soglia per la variante `coastal` di `start`/`end`: se la posizione
    di apertura/chiusura è entro questa distanza dalla costa, il framing
    viene marcato come costiero. Più larga di `sea_distance_threshold_m`:
    "finire/iniziare in riva al mare" è un carattere ambientale, più
    morbido di "ecco il mare"."""
    coastal_stage_max_median_m: float = 1000.0
    """Soglia per la variante `coastal` come carattere di tappa intera:
    se la *mediana* della distanza dalla costa lungo la tappa è sotto
    questa soglia, la tappa nel suo insieme è costiera anche se il
    singolo punto di start/end non lo è (es. Peschici-Mattinata, che
    termina 1.5km nell'entroterra ma percorre la costa garganica per
    più della metà del tempo)."""
    coastal_view_max_median_m: float = 5000.0
    coastal_view_min_ele_median_m: float = 150.0
    coastal_view_min_ele_max_m: float = 250.0
    """Soglie per la variante `sea_view` (panoramica sul mare): tappe
    che restano vicine alla costa (< 5 km mediana) ma in quota
    (mediana quota ≥ 150 m, max ≥ 250 m). Cattura le Cinque Terre e
    altre alte vie costiere, distinte da `coastal` (in spiaggia)."""
    poi_detector_eval_rate_hz: float = 1.0
    """Frequenza di valutazione del POIDetector. 1 Hz sufficiente per
    cogliere l'entrata nel raggio di un POI."""
    poi_reentry_cooldown_s: float = 3600.0
    """Cooldown minimo prima di riemettere un evento `poi` per lo
    stesso POI. Evita jitter su POI grandi (cammino tortuoso che esce
    e rientra) e permette comunque di emettere una seconda entrata
    significativa (es. ritorno serale in un borgo dopo un'ora fuori)."""
    territory_stable_window_s: float = 20.0

    def major_cooldown_s(self, stage_duration_s: float) -> float:
        return max(
            self.major_cooldown_min_s,
            stage_duration_s / (self.major_target_per_stage * 1.5),
        )

    def minor_cooldown_s(self, stage_duration_s: float) -> float:
        return max(
            self.minor_cooldown_min_s,
            stage_duration_s / (self.minor_target_per_stage * 1.5),
        )


# Frequenze OSC per gruppo di canali (Hz). Mapping immutabile.
_DEFAULT_OSC_RATES: Mapping[str, float] = MappingProxyType({
    "journey": 0.2,
    "macro": 1.0,
    "meso": 4.0,
    "body": 2.0,
    "micro": 15.0,
})


@dataclass(frozen=True)
class OscConfig:
    """Parametri di trasporto OSC."""

    host: str = "127.0.0.1"
    port: int = 9000
    rates_hz: Mapping[str, float] = field(default_factory=lambda: _DEFAULT_OSC_RATES)


@dataclass(frozen=True)
class GpxConfig:
    """Parametri di caricamento e derivazione dai file GPX."""

    # Velocità di riferimento (km/h) per normalizzare la componente di sforzo
    # legata al moto. Sopra questa soglia la componente satura.
    speed_reference_kmh: float = 25.0
    # Pendenza positiva di riferimento (frazione, es. 0.10 = 10%) per
    # normalizzare la componente di sforzo legata alla salita.
    slope_reference: float = 0.08
    # Pesi della formula di effort = w_speed * speed_norm + w_slope * slope_pos_norm.
    # Devono sommare a 1 per restare nel range [0, 1].
    effort_weight_speed: float = 0.4
    effort_weight_slope: float = 0.6
    # Filtraggio leggero del raw GPX (mediana mobile in numero di campioni).
    raw_median_window: int = 3


@dataclass(frozen=True)
class GeoConfig:
    """Parametri di geometria (costa, future feature spaziali).

    Il path dello shapefile non sta qui: viene passato esplicitamente
    a `Coastline(...)` quando serve (default in `geo/coastline.py`).
    """

    # Bounding box di interesse (lon_min, lat_min, lon_max, lat_max).
    # Default: Italia allargata. Riduce il costo di carico dello
    # shapefile mondiale a ~50 segmenti.
    coastline_bbox: tuple[float, float, float, float] = (6.0, 36.0, 19.0, 48.0)


@dataclass(frozen=True)
class Config:
    """Configurazione completa del sistema."""

    timing: TimingConfig = field(default_factory=TimingConfig)
    smoothing: SmoothingConfig = field(default_factory=SmoothingConfig)
    journey: JourneyConfig = field(default_factory=JourneyConfig)
    macro: MacroConfig = field(default_factory=MacroConfig)
    gpx: GpxConfig = field(default_factory=GpxConfig)
    events: EventConfig = field(default_factory=EventConfig)
    osc: OscConfig = field(default_factory=OscConfig)
    geo: GeoConfig = field(default_factory=GeoConfig)


DEFAULT_CONFIG: Config = Config()
"""Istanza di configurazione predefinita, importabile ovunque."""

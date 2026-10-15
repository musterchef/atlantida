"""Configurazione del caricamento GPX e del trasporto delle metriche."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimingConfig:
    """Tempi e frequenze di base della pipeline."""

    internal_rate_hz: float = 10.0
    """Frequenza di ricampionamento interno (Hz)."""


@dataclass(frozen=True)
class OscConfig:
    """Parametri di trasporto OSC."""

    host: str = "127.0.0.1"
    port: int = 9000
    trip_metrics_rate_hz: float = 1.0
    """Frequenza del contratto neutrale delle metriche viaggio."""


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
class Config:
    """Configurazione del producer GPX."""

    timing: TimingConfig = field(default_factory=TimingConfig)
    gpx: GpxConfig = field(default_factory=GpxConfig)
    osc: OscConfig = field(default_factory=OscConfig)


DEFAULT_CONFIG = Config()

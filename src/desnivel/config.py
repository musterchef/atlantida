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
    sea_distance_threshold_m: float = 500.0
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
class Config:
    """Configurazione completa del sistema."""

    timing: TimingConfig = field(default_factory=TimingConfig)
    smoothing: SmoothingConfig = field(default_factory=SmoothingConfig)
    events: EventConfig = field(default_factory=EventConfig)
    osc: OscConfig = field(default_factory=OscConfig)


DEFAULT_CONFIG: Config = Config()
"""Istanza di configurazione predefinita, importabile ovunque."""

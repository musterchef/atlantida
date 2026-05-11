"""Modello dati di una tappa e dei suoi campioni.

`Track` è l'input immutabile della pipeline. Contiene i campioni
ricampionati a frequenza fissa (vedi `Resampler`, da implementare)
e i metadati liberi (meteo, città, eventi esterni dichiarati).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class GeoPoint:
    """Punto geografico (lat/lon in gradi, ele in metri)."""

    lat: float
    lon: float
    ele: float | None = None


@dataclass(frozen=True)
class Track:
    """Dati di una tappa già ricampionati su griglia temporale uniforme.

    Attributes:
        stage_id: identificatore della tappa (es. ``"tappa_01"``).
        t: vettore dei tempi in secondi dall'inizio della tappa.
            È sempre regolare, con passo ``1 / config.timing.internal_rate_hz``.
        samples: dizionario dei canali campionati. Ogni valore è un
            ``np.ndarray`` della stessa lunghezza di ``t``.
            Chiavi previste (non tutte obbligatorie in scaffolding):
            ``lat``, ``lon``, ``ele``, ``speed_kmh``, ``slope``,
            ``effort``, ``flow``, ``terrain``.
        metadata: dati liberi associati alla tappa (meteo, eventi esterni,
            informazioni di contesto). Non viene ispezionato dai modulatori.
    """

    stage_id: str
    t: np.ndarray
    samples: Mapping[str, np.ndarray]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return float(self.t[-1] - self.t[0]) if len(self.t) > 0 else 0.0

    @property
    def n_samples(self) -> int:
        return int(len(self.t))


def make_empty_track(
    stage_id: str,
    duration_s: float,
    rate_hz: float,
) -> Track:
    """Crea un Track vuoto della durata indicata. Utile per scaffolding e test."""
    n = int(duration_s * rate_hz) + 1
    t = np.arange(n, dtype=float) / rate_hz
    return Track(stage_id=stage_id, t=t, samples={}, metadata={})

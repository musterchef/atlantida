"""Modello dati di una tappa e dei suoi campioni.

`Track` contiene i tratti osservati ricampionati e i riferimenti alla sorgente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class TrackSegment:
    """Intervallo osservato, con slice dei campioni ed estremi sorgente originali."""

    start: int
    stop: int
    source_start_unix: float
    source_end_unix: float
    source_start_index: int
    source_end_index: int


@dataclass(frozen=True)
class Track:
    """Dati osservati su un asse temporale che esclude le interruzioni.

    Attributes:
        stage_id: identificatore della tappa (es. ``"tappa_01"``).
        t: secondi attivi dall'inizio dei dati conservati. Regolare all'interno
            di ciascun tratto, con eventuale ultimo intervallo più breve.
            Alla giunzione sono conservati entrambi gli estremi con lo stesso
            tempo attivo; non descrivono movimento fra le due posizioni.
        samples: dizionario dei canali campionati. Ogni valore è un
            ``np.ndarray`` della stessa lunghezza di ``t``.
            Canali del loader (quelli derivati dalla quota possono essere assenti):
            ``lat``, ``lon``, ``ele``, ``speed_kmh``, ``slope``,
            ``effort``, ``dist_m``, ``cum_dist_m``.
        metadata: dati liberi associati alla tappa (meteo, eventi esterni,
            informazioni di contesto). Include il percorso del GPX in ``source_path``.
            Il loader conserva il registro ``source_filter`` e gli intervalli
            temporali ``unavailable_motion_intervals`` esclusi dalle misure di movimento.
        segments: confini dei tratti osservati e riferimenti ai punti e tempi sorgente.
        I FIT conservano inoltre i canali opzionali ``recorded_distance_m``,
        ``recorded_speed_kmh`` e ``gps_accuracy_m``, separati dalle metriche derivate.
    """

    stage_id: str
    t: np.ndarray
    samples: Mapping[str, np.ndarray]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    segments: tuple[TrackSegment, ...] = ()

    @property
    def duration_s(self) -> float:
        return float(self.t[-1] - self.t[0]) if len(self.t) > 0 else 0.0

    @property
    def n_samples(self) -> int:
        return int(len(self.t))

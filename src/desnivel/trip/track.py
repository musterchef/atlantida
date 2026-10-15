"""Modello dati di una tappa e dei suoi campioni.

`Track` contiene i campioni ricampionati dal loader GPX a frequenza
fissa e i metadati della sorgente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class Track:
    """Dati di una tappa già ricampionati su griglia temporale uniforme.

    Attributes:
        stage_id: identificatore della tappa (es. ``"tappa_01"``).
        t: vettore dei tempi in secondi dall'inizio della tappa.
            È sempre regolare, con passo ``1 / config.timing.internal_rate_hz``.
        samples: dizionario dei canali campionati. Ogni valore è un
            ``np.ndarray`` della stessa lunghezza di ``t``.
            Canali del loader (quelli derivati dalla quota possono essere assenti):
            ``lat``, ``lon``, ``ele``, ``speed_kmh``, ``slope``,
            ``effort``, ``dist_m``, ``cum_dist_m``.
        metadata: dati liberi associati alla tappa (meteo, eventi esterni,
            informazioni di contesto). Include il percorso del GPX in ``source_path``.
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

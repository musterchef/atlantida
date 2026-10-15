"""Classifier `arrival_climb`: marca un evento `end` come arrivo in salita.

Logica trasferita dal vecchio `ArrivalClimbDetector` (rimosso nella v0.4
del contratto). La chiusura della tappa e' sempre un unico evento `end`:
se la tappa termina significativamente piu' in alto del minimo della
seconda meta', questo classifier aggiunge la variante ``"climb"`` al
payload e i campi ``climb_delta_m`` / ``final_ele_m``.

Soglia: ``EventConfig.arrival_climb_min_delta_m`` (default 50 m).

Vedi CONTRATTO-MODULAZIONI.md §3.1.1.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..detectors._elevation import smooth_elevation
from ..events import Event
from ..track import Track


class ArrivalClimbClassifier:
    """Aggiunge la variante ``climb`` agli eventi ``end`` in salita.

    Confronta l'elevazione finale (smoothed) con il minimo della seconda
    meta' della tappa: scegliere la seconda meta' evita di marcare come
    "arrivo in salita" tappe che semplicemente iniziano in pianura e
    finiscono in collina dopo una lunga discesa.
    """

    applies_to_kinds: tuple[str, ...] | None = ("end",)

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
        ele = track.samples.get("ele")
        if ele is None or track.n_samples < 3:
            return {}
        ele = np.asarray(ele, dtype=float)
        if not np.isfinite(ele).any():
            return {}

        smoothed = smooth_elevation(ele, self.config.timing.internal_rate_hz)
        half = smoothed.size // 2
        second_half = smoothed[half:]
        final_ele = float(second_half[-1])
        min_after_half = float(np.min(second_half))
        delta = final_ele - min_after_half

        if delta < self.config.events.arrival_climb_min_delta_m:
            return {}

        return {
            "variants": ["climb"],
            "climb_delta_m": float(delta),
            "final_ele_m": float(final_ele),
        }

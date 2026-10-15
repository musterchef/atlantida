"""Suggerimento automatico di accompagnamento dai pattern musicali di una tappa."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from desnivel.bass import BassSettings
from desnivel.music import PatternChange


@dataclass(frozen=True)
class BassRecommendation:
    settings: BassSettings
    mean_gate_fraction: float
    gate_deviation: float
    analyzed_seconds: float


def recommend_bass(changes: Iterable[PatternChange], end_seconds: float) -> BassRecommendation:
    """Pesa i gate aperti per durata; non conosce clock, Shape o note reali di Snake.

    Restituisce un assetto unico per la tappa. Nessun invio o aggiornamento live.
    """
    changes = tuple(changes)
    if not changes or not math.isfinite(end_seconds) or end_seconds <= 0:
        raise ValueError('servono cambi musicali e durata finale positiva e finita')
    times = [change.elapsed_s for change in changes]
    if (any(not math.isfinite(t) or not 0 <= t <= end_seconds for t in times)
            or any(a >= b for a, b in zip(times, times[1:]))):
        raise ValueError('cambi ordinati, con tempi distinti entro la durata della tappa')
    spans = []
    for index, change in enumerate(changes):
        end = times[index + 1] if index + 1 < len(times) else end_seconds
        duration = end - change.elapsed_s
        if duration > 0:
            fraction = sum(change.pattern.gates) / len(change.pattern.gates)
            spans.append((duration, fraction))
    duration = sum(seconds for seconds, _ in spans)
    if duration <= 0:
        raise ValueError('nessun intervallo musicale di durata positiva')
    mean = sum(seconds * fraction for seconds, fraction in spans) / duration
    deviation = math.sqrt(sum(seconds * (fraction - mean) ** 2
                              for seconds, fraction in spans) / duration)
    # Regole conservative: lasciare spazio alla melodia, senza dedurre armonia dal GPX.
    settings = BassSettings(
        density=round(1 - .5 * mean, 3),
        syncopation=round(.4 - .2 * mean, 3),
        articulation=round(.85 - .25 * mean, 3),
        variation=round(.2 + .6 * deviation, 3),
    )
    return BassRecommendation(settings, mean, deviation, duration)

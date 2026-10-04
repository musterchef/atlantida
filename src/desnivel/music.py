"""Regole musicali pure: metriche in ingresso, pattern in uscita."""
from __future__ import annotations

from dataclasses import dataclass
import math

from desnivel.trip_metrics import MetricName, MetricSample

#: Intervalli in semitoni dalla tonica.
SCALES: dict[str, tuple[int, ...]] = {
    "chromatic": tuple(range(12)),
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
}



def scale_notes(scale: str, root: int, count: int = 16) -> list[int]:
    if scale not in SCALES:
        raise ValueError(f"scala sconosciuta: {scale}")
    intervals = SCALES[scale]
    return [root + 12 * (i // len(intervals)) + intervals[i % len(intervals)]
            for i in range(count)]


@dataclass(frozen=True)
class Pattern:
    notes: tuple[int, ...]
    gates: tuple[int, ...]

    def __post_init__(self):
        if not self.notes or len(self.notes) != len(self.gates):
            raise ValueError("note e gate devono avere la stessa lunghezza non nulla")
        if any(type(n) is not int for n in self.notes):
            raise ValueError("le note devono essere semitoni interi")
        if any(g not in (0, 1) for g in self.gates):
            raise ValueError("gate ammessi: 0 e 1")


@dataclass(frozen=True)
class PatternChange:
    elapsed_s: float
    state: str
    pattern: Pattern
    section_index: int | None = None


@dataclass
class ThresholdRule:
    metric: MetricName
    threshold: float
    hysteresis: float
    low: Pattern
    high: Pattern
    state: str | None = None

    def __post_init__(self):
        if not math.isfinite(self.threshold) or not math.isfinite(self.hysteresis) or self.hysteresis < 0:
            raise ValueError("soglia finita e isteresi non negativa richieste")

    def update(self, sample: MetricSample) -> PatternChange | None:
        if sample.name != self.metric or not math.isfinite(sample.value):
            return None
        state = self.state
        if state is None:
            state = "high" if sample.value >= self.threshold else "low"
        elif state == "low" and sample.value >= self.threshold + self.hysteresis:
            state = "high"
        elif state == "high" and sample.value < self.threshold - self.hysteresis:
            state = "low"
        if state == self.state:
            return None
        self.state = state
        return PatternChange(sample.elapsed_s, state, self.high if state == "high" else self.low)


def rule_from_dict(data: dict) -> ThresholdRule:
    def pattern(spec):
        degrees = spec["degrees"]
        if not degrees or any(type(d) is not int or d < 0 for d in degrees):
            raise ValueError("gradi richiesti: interi >= 0")
        notes = scale_notes(spec["scale"], spec["root"], max(degrees) + 1)
        return Pattern(tuple(notes[d] for d in degrees), tuple(spec["gates"]))
    return ThresholdRule(MetricName(data["metric"]), float(data["threshold"]),
                         float(data["hysteresis"]), pattern(data["low"]), pattern(data["high"]))

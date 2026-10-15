"""Frasi musicali indipendenti dal player. Un beat è una semiminima."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Note:
    beat: float
    pitch: int
    duration: float
    velocity: int

    def __post_init__(self):
        if not math.isfinite(self.beat) or self.beat < 0:
            raise ValueError('beat deve essere finito e non negativo')
        if not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError('duration deve essere finita e positiva')
        for value, low, high in [(self.pitch, 0, 127), (self.velocity, 1, 127)]:
            if type(value) is not int or not low <= value <= high:
                raise ValueError('pitch 0–127 e velocity 1–127 devono essere interi')


@dataclass(frozen=True)
class Phrase:
    length_beats: float
    notes: tuple[Note, ...]

    def __post_init__(self):
        if not math.isfinite(self.length_beats) or self.length_beats <= 0:
            raise ValueError('length_beats deve essere finita e positiva')
        if any(n.beat + n.duration > self.length_beats for n in self.notes):
            raise ValueError('ogni nota deve terminare entro la frase')

    @classmethod
    def from_dict(cls, data):
        return cls(data['length_beats'], tuple(Note(**n) for n in data['notes']))

"""Profili ritmici in 4/4: ruoli percussivi, accenti e timing espliciti."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class StyleHit:
    beat: float
    role: str
    velocity: int
    structural: bool = False


@dataclass(frozen=True)
class DrumStyle:
    id: str
    label: str
    variants: tuple[tuple[StyleHit, ...], ...]
    swing_delay: float = 0.
    cycle_beats: float = 4.
    meter: tuple[int, int] = (4, 4)

    def variant(self, cycle, seed):
        # Una figura dura due battute; il seed sceglie la variante iniziale.
        offset = random.Random(f'{self.id}:{seed}').randrange(len(self.variants))
        return (cycle//2+offset) % len(self.variants)


def _hits(kicks, hats, extra=()):
    core = [StyleHit(b, 'kick', v, True) for b, v in kicks]
    core += [StyleHit(1, 'snare', 102, True), StyleHit(3, 'snare', 98, True)]
    return tuple(sorted(core+[StyleHit(b, 'hat', v) for b, v in hats]+list(extra), key=lambda h: (h.beat, h.role)))


STYLES = (
    DrumStyle('house_classic', 'House classica', (
        _hits(((0, 110), (1, 104), (2, 108), (3, 104)),
              ((.5, 76), (1.5, 68), (2.5, 74), (3.5, 68))),
        _hits(((0, 110), (1, 104), (2, 108), (3, 104)),
              ((.5, 76), (1.5, 68), (2.5, 74), (3.5, 68)), (StyleHit(3.75, 'hat', 38),)),
    )),
    DrumStyle('boom_bap_90s', 'Boom bap', (
        _hits(((0, 112), (1.75, 88), (2, 105)),
              tuple((i*.5, 64 if i % 2 == 0 else 43) for i in range(8))),
        _hits(((0, 112), (2, 105), (2.75, 82)),
              tuple((i*.5, 64 if i % 2 == 0 else 43) for i in range(8)),
              (StyleHit(2.75, 'snare', 34),)),
    ), swing_delay=.08),
    DrumStyle('breakbeat_house', 'Breakbeat house', (
        _hits(((0, 110), (1.5, 97), (2.75, 104)),
              tuple((i*.5, 40 if i % 2 == 0 else 67) for i in range(8)),
              (StyleHit(3.75, 'hat', 35),)),
        _hits(((0, 110), (1.75, 97), (2.5, 104)),
              tuple((i*.5, 40 if i % 2 == 0 else 67) for i in range(8)),
              (StyleHit(2.75, 'snare', 36),)),
    ), swing_delay=.04),
)
STYLE_BY_ID = {style.id: style for style in STYLES}
STYLE_OPTIONS = (('none', 'Nessuno'),)+tuple((style.id, style.label) for style in STYLES)


def style_events(style, lanes, start, end, seed):
    """Attacchi assoluti (beat, MIDI, velocity, struttura), prima dello sviluppo."""
    result = []
    for cycle in range(math.floor(start/style.cycle_beats), math.ceil(end/style.cycle_beats)):
        variant = style.variants[style.variant(cycle, seed)]
        for hit in variant:
            delay = style.swing_delay if hit.role == 'hat' and hit.beat % 1 == .5 else 0.
            beat = cycle*style.cycle_beats+hit.beat+delay
            if start <= beat < end:
                result.append((beat, lanes[hit.role], hit.velocity, hit.structural))
    return sorted(result)

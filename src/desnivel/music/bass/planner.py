"""Pianificazione della voce di basso e transizioni dei suoi controlli."""
from __future__ import annotations

import math

from desnivel.music.bass.generator import BassSettings, generate_bass, interpolate_settings
from desnivel.music.phrases import Phrase


class BassPlanner:
    """Coordina l'accompagnamento di una frase sorgente su finestre in beat.

    La sorgente è già pianificata dal chiamante. Il basso ne dipende;
    conserva la continuità con la finestra precedente e i controlli in transizione.
    """

    def __init__(self, settings=BassSettings(), window=4.0):
        if not math.isfinite(window) or window <= 0:
            raise ValueError('window deve essere positiva e finita')
        self.settings = settings
        self.window = window
        self._transition = None
        self._last_start = None
        self._phrases = {}

    @property
    def target_settings(self):
        """Destinazione corrente, anche quando la transizione è ancora in corso."""
        return self._transition[1] if self._transition is not None else self.settings

    def set_settings(self, settings: BassSettings, transition_windows: int = 4):
        """Nuovi controlli dalle prossime finestre, senza dipendere dagli snapshot."""
        if not isinstance(settings, BassSettings):
            raise TypeError('attese BassSettings')
        if type(transition_windows) is not int or transition_windows < 0:
            raise ValueError('transition_windows deve essere un intero non negativo')
        if self._last_start is None or transition_windows == 0:
            self.settings = settings
            self._transition = None
        else:
            self._transition = (self.settings, settings, self._last_start, transition_windows)

    def _settings_at(self, start):
        if self._transition is not None:
            initial, target, origin, windows = self._transition
            amount = min(1.0, max(0.0, (start - origin) / (self.window * windows)))
            self.settings = interpolate_settings(initial, target, amount)
            if amount == 1:
                self._transition = None
        self._last_start = start
        return self.settings

    def reset(self):
        """Apre una nuova sequenza conservando il valore corrente dei controlli."""
        self._phrases.clear()
        if self._transition is not None:
            _, target, _, windows = self._transition
            self._transition = (self.settings, target, None, windows)
        self._last_start = None

    def plan(self, melody: Phrase, start: float) -> Phrase:
        """Compone il basso dopo la sorgente, per la stessa finestra musicale."""
        if not math.isfinite(start) or start < 0:
            raise ValueError('start deve essere finito e non negativo')
        if melody.length_beats != self.window:
            raise ValueError('la frase sorgente deve coprire la finestra musicale')
        if self._transition is not None and self._transition[2] is None:
            initial, target, _, windows = self._transition
            self._transition = (initial, target, start, windows)
        previous = self._phrases.get(start - self.window)
        last = previous.notes[-1].pitch if previous and previous.notes else None
        phrase = generate_bass(melody, self._settings_at(start), last,
                               phrase_index=round(start / self.window))
        self._phrases[start] = phrase
        self._phrases = {k: v for k, v in self._phrases.items() if k >= start - 2 * self.window}
        return phrase

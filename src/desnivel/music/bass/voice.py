"""Ingresso del generatore di accompagnamento nel coordinamento multivoce."""
from dataclasses import replace

from desnivel.music.bass.generator import BassSettings, generate_bass


class BassVoice:
    def __init__(self, settings=None):
        self.settings = BassSettings(**(settings or {}))
        self.previous = None
        self.previous_end = None

    def validate(self, role, parameters):
        if role != 'bass_line':
            raise ValueError('ruolo non supportato dal generatore di accompagnamento')
        return replace(self.settings, **parameters)

    def __call__(self, request):
        settings = self.validate(request.role, request.parameters)
        if len(request.dependencies) != 1:
            raise ValueError('l’accompagnamento richiede una sola frase di riferimento')
        source = next(iter(request.dependencies.values()))
        last = self.previous if self.previous_end == request.start else None
        result = generate_bass(source, settings, last,
                               phrase_index=round(request.start / request.length_beats))
        self.previous = result.notes[-1].pitch if result.notes else None
        self.previous_end = request.start + request.length_beats
        return result

    def reset(self):
        self.previous = self.previous_end = None

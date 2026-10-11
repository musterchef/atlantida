"""Generazione del basso da una frase MIDI, indipendente dalla sorgente."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from collections import defaultdict

from desnivel.phrases import Note, Phrase


@dataclass(frozen=True)
class BassSettings:
    lowest: int = 28
    highest: int = 47
    min_spacing: float = 1.0
    articulation: float = 0.9
    velocity_ratio: float = 0.9
    strategy: str = 'responsive'
    seed: int = 0
    variation_period: int = 4
    max_hold: float = 2.0
    grid: float = 0.5

    def __post_init__(self):
        if self.strategy not in ('responsive', 'follow'):
            raise ValueError('strategia basso sconosciuta')
        if type(self.seed) is not int or type(self.variation_period) is not int or self.variation_period < 1:
            raise ValueError('seed intero e variation_period positivo richiesti')
        if any(not math.isfinite(x) or x <= 0 for x in (self.max_hold, self.grid)):
            raise ValueError('max_hold e grid devono essere positivi e finiti')
        if (type(self.lowest) is not int or type(self.highest) is not int
                or not 0 <= self.lowest <= self.highest <= 127
                or self.highest - self.lowest < 11):
            raise ValueError('registro del basso: almeno 12 note MIDI consecutive')
        if not math.isfinite(self.min_spacing) or self.min_spacing <= 0:
            raise ValueError('min_spacing deve essere positivo e finito')
        for value in (self.articulation, self.velocity_ratio):
            if not math.isfinite(value) or not 0 < value <= 1:
                raise ValueError('articolazione e rapporto velocity devono essere in (0, 1]')


def _follow(melody: Phrase, settings: BassSettings = BassSettings(),
                  previous_pitch: int | None = None) -> Phrase:
    """Seleziona attacchi distanziati e minimizza i salti fra ottave.

    Mantiene la classe di altezza dell'attacco scelto. Non deduce accordi
    dalla sola scala. Il silenzio della melodia resta silenzio nel basso.
    previous_pitch permette continuità fra sezioni pianificate.
    """
    if previous_pitch is not None and (type(previous_pitch) is not int or not 0 <= previous_pitch <= 127):
        raise ValueError('previous_pitch deve essere una nota MIDI')
    selected = []
    for note in sorted(melody.notes, key=lambda n: (n.beat, -n.velocity, n.pitch)):
        if not selected or note.beat - selected[-1].beat >= settings.min_spacing:
            selected.append(note)
    result = []
    reference = previous_pitch if previous_pitch is not None else (settings.lowest + settings.highest) / 2
    for i, note in enumerate(selected):
        candidates = [p for p in range(settings.lowest, settings.highest + 1)
                      if p % 12 == note.pitch % 12]
        pitch = min(candidates, key=lambda p: (abs(p-reference), p))
        end = min(note.beat + note.duration, melody.length_beats)
        if i+1 < len(selected):
            end = min(end, selected[i+1].beat)
        duration = (end-note.beat) * settings.articulation
        result.append(Note(note.beat, pitch, duration,
                           max(1, min(127, round(note.velocity * settings.velocity_ratio)))))
        reference = pitch
    return Phrase(melody.length_beats, tuple(result))


def _salience(melody):
    weights = defaultdict(float)
    for n in melody.notes:
        accent = 1.5 if abs(n.beat-round(n.beat)) < 1e-8 else 1.0
        weights[n.pitch % 12] += n.duration * n.velocity * accent
    return weights


def _rhythm(melody, settings, phase, rng):
    """Combina appoggi metrici e risposte negli spazi della melodia."""
    start = min(n.beat for n in melody.notes)
    end = max(n.beat+n.duration for n in melody.notes)
    slots = {start}
    i = math.ceil(start/settings.grid)
    while i*settings.grid < end-1e-9:
        slots.add(round(i*settings.grid,9)); i += 1
    slots.update(n.beat for n in melody.notes)
    attacks = {round(n.beat,9) for n in melody.notes}
    ranked = []
    for t in sorted(slots):
        strong = abs(t-round(t)) < 1e-8
        response = round(t,9) not in attacks
        # La risposta ha più spazio verso il centro del ciclo di variazione.
        openness = phase/max(1,settings.variation_period-1)
        score = (1.0 if strong else 0.35) + response*openness + rng.random()*.8
        if t == start: score += 4
        ranked.append((score,t))
    density = len(melody.notes)/melody.length_beats
    capacity = max(1,math.ceil((end-start)/settings.min_spacing))
    activity = min(1.0,density/2)
    target = max(1,round(capacity*(.55+.3*activity+.15*phase/max(1,settings.variation_period-1))))
    selected = []
    for _,t in sorted(ranked,reverse=True):
        if all(abs(t-other) >= settings.min_spacing-1e-9 for other in selected):
            selected.append(t)
            if len(selected)>=target:break
    return sorted(selected)


def _responsive(melody, settings, previous_pitch, phrase_index):
    if not melody.notes:
        return Phrase(melody.length_beats,())
    phase = phrase_index % settings.variation_period
    # Non dipende dal numero di snapshot ricevuti: lo stesso piano è ripetibile.
    rng = random.Random(settings.seed + phase*104729)
    weights = _salience(melody)
    anchor = max(weights, key=lambda pc: (weights[pc], -pc))
    candidates = [p for p in range(settings.lowest,settings.highest+1) if p%12 in weights]
    if not candidates:
        raise ValueError('nessuna nota della melodia nel registro richiesto')
    onsets = _rhythm(melody,settings,phase,rng)
    previous = previous_pitch if previous_pitch is not None else (settings.lowest+settings.highest)/2
    peak = max(weights.values())
    result = []
    for i,t in enumerate(onsets):
        sounding = [n for n in melody.notes if n.beat <= t < n.beat+n.duration]
        nearby = min(melody.notes,key=lambda n: (abs(n.beat-t),-n.velocity))
        strong = abs(t-round(t)) < 1e-8
        resolve = phase == settings.variation_period-1 and i == len(onsets)-1
        jitter = {p:rng.random()*.3 for p in candidates}
        def score(p):
            harmonic = sum(1 if (n.pitch-p)%12 in (0,3,4,5,7,8,9) else -2
                           for n in sounding)/max(1,len(sounding))
            home = 2.5 if (i==0 or resolve) and p%12==anchor else 0
            repeat = .8 if result and p==result[-1].pitch and not resolve else 0
            return home + harmonic + weights[p%12]/peak - abs(p-previous)*.1 - repeat + jitter[p]
        pitch = max(candidates,key=lambda p:(score(p),-p))
        end = onsets[i+1] if i+1<len(onsets) else melody.length_beats
        hold = min(end-t,settings.max_hold)
        # Appoggi più distesi, risposte più corte: non copia la durata della melodia.
        articulation = settings.articulation * (1 if strong else .65)
        duration = hold*articulation
        accent = 1 if i==0 or resolve else (.92 if strong else .75)
        velocity = max(1,min(127,round(nearby.velocity*settings.velocity_ratio*accent)))
        result.append(Note(t,pitch,duration,velocity));previous=pitch
    return Phrase(melody.length_beats,tuple(result))


def generate_bass(melody: Phrase, settings: BassSettings = BassSettings(),
                  previous_pitch: int | None = None, *, phrase_index: int = 0) -> Phrase:
    """Compone una frase; indice musicale esplicito per variazioni ripetibili.

    responsive costruisce ritmo e articolazione autonomi usando le classi di
    altezza osservate. follow conserva il comportamento di accompagnamento
    iniziale. Nessuna conoscenza di Snake, OSC o del viaggio.
    """
    if type(phrase_index) is not int or phrase_index < 0:
        raise ValueError('phrase_index deve essere un intero non negativo')
    if previous_pitch is not None and (type(previous_pitch) is not int or not 0<=previous_pitch<=127):
        raise ValueError('previous_pitch deve essere una nota MIDI')
    if settings.strategy == 'follow':
        return _follow(melody,settings,previous_pitch)
    return _responsive(melody,settings,previous_pitch,phrase_index)

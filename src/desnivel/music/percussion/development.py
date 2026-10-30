"""Sviluppo di un materiale percussivo lungo richieste musicali consecutive."""
from __future__ import annotations

from copy import deepcopy
import math
import random

from desnivel.music.phrases import Note, Phrase
from .generator import PercussionGenerator, ROLES


DEFAULTS = {'conceptuality': 1., 'variation': .7, 'displacement_beats': .25, 'velocity_ratio': .85,
            'gate_beats': .1, 'seed': 7, 'support_tolerance_beats': .5, 'answer_clearance_beats': .25}
OPERATIONS = {'statement', 'subtract', 'displace', 'accent', 'silence'}


class PercussionPhraseGenerator:
    def __init__(self, lanes, material, anchor_beats, development, interaction, settings=None, *, standard_material=None):
        # Riutilizza la validazione dei materiali espliciti e della mappa MIDI.
        parsed = PercussionGenerator(lanes, [material])
        self.name, self.cycle, self.hits = parsed.patterns[0]
        self.standard = (PercussionGenerator(lanes, [standard_material]).patterns[0]
                         if standard_material is not None else None)
        if (not isinstance(anchor_beats, list) or not anchor_beats
                or any(type(b) not in (int, float) or not math.isfinite(b) for b in anchor_beats)
                or len(set(anchor_beats)) != len(anchor_beats)
                or not set(anchor_beats) <= {hit[0] for hit in self.hits}):
            raise ValueError('anchor_beats deve indicare attacchi distinti presenti nel materiale')
        self.anchors = frozenset(anchor_beats)
        if (not isinstance(development, list) or not development
                or any(not isinstance(op, str) or op not in OPERATIONS for op in development)
                or development[0] != 'statement'):
            raise ValueError('development deve iniziare con statement e contenere operazioni supportate')
        self.development = tuple(development)
        fields = {'support_source', 'support_lanes', 'answer_source', 'answer_lanes'}
        if not isinstance(interaction, dict) or set(interaction) != fields:
            raise ValueError('interaction richiede sorgenti e canali di sostegno e risposta')
        if any(not isinstance(interaction[k], str) or not interaction[k] for k in ('support_source', 'answer_source')):
            raise ValueError('nomi delle sorgenti di interazione non vuoti richiesti')
        support = interaction['support_lanes']
        answers = interaction['answer_lanes']
        if (not isinstance(support, list) or not support or not isinstance(answers, list) or not answers
                or any(not isinstance(lane, str) or lane not in lanes for lane in support+answers)
                or len(set(support+answers)) != len(support+answers)
                or set(support+answers) != set(lanes)):
            raise ValueError('ogni canale deve essere assegnato una volta al sostegno o alla risposta')
        self.interaction = deepcopy(interaction)
        self.support_pitches = frozenset(lanes[lane] for lane in support)
        if settings is not None and not isinstance(settings, dict):
            raise ValueError('settings deve essere una mappa di parametri')
        self.settings = {**DEFAULTS, **deepcopy(settings or {})}
        self.validate('percussion', {})
        self.reset()

    def reset(self):
        self.position = 0.
        self.last_start = None
        self.last_position = 0.
        self.last_decision = None

    def describe_controls(self, role, parameters):
        """Disponibilità dei controlli secondo materiali e trasformazioni configurati."""
        values = {**self.settings, **parameters}
        details = {'conceptuality': {'label': 'Standard ↔ sviluppato'}}
        if values['conceptuality'] == 0:
            for name in ('variation', 'displacement_beats', 'support_tolerance_beats',
                         'answer_clearance_beats', 'seed'):
                details[name] = {'inactive_reason': 'Groove standard: nessuno sviluppo o interazione'}
        elif values['variation'] == 0 or 'displace' not in self.development:
            details['displacement_beats'] = {'inactive_reason': 'Richiede trasformazione displace attiva'}
        return details

    def validate(self, role, parameters):
        if role not in ROLES:
            raise ValueError('ruolo non supportato dal generatore percussivo')
        values = {**self.settings, **parameters}
        if set(values) != set(DEFAULTS):
            raise ValueError('parametri percussivi sconosciuti')
        for key in ('conceptuality', 'variation', 'displacement_beats', 'velocity_ratio', 'gate_beats',
                    'support_tolerance_beats', 'answer_clearance_beats'):
            value = values[key]
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not 0 <= value <= 1 or (key in ('velocity_ratio', 'gate_beats') and value == 0)):
                raise ValueError(f'{key} fuori intervallo')
        if values['conceptuality'] < 1 and self.standard is None:
            raise ValueError('standard_material richiesto per conceptuality inferiore a 1')
        if type(values['seed']) is not int or not 0 <= values['seed'] <= 2147483647:
            raise ValueError('seed deve essere un intero tra 0 e 2147483647')
        return values

    def _cycle(self, index, values):
        operation = self.development[index % len(self.development)]
        amount = values['variation']
        if not amount:
            operation = 'statement'
        if operation == 'silence':
            return operation, ()
        rng = random.Random((values['seed'] << 32)+index)
        secondary = [i for i, hit in enumerate(self.hits) if hit[0] not in self.anchors]
        selected = set(rng.sample(secondary, min(len(secondary), math.ceil(len(secondary)*amount))))
        direction = rng.choice((-1, 1))
        events = {}
        # Gli attacchi protetti hanno precedenza in caso di coincidenza.
        for i in sorted(range(len(self.hits)), key=lambda i: self.hits[i][0] not in self.anchors):
            beat, pitch, velocity = self.hits[i]
            if i in selected:
                if operation == 'subtract':
                    continue
                if operation == 'displace':
                    beat = (beat+direction*values['displacement_beats']) % self.cycle
                if operation == 'accent':
                    velocity = max(1, min(127, velocity+direction*round(64*amount)))
            events.setdefault((beat, pitch), velocity)
        return operation, tuple((b, p, v) for (b, p), v in sorted(events.items()))

    def _interact(self, events, dependencies, values):
        definition = self.interaction
        answer_name, support_name = definition['answer_source'], definition['support_source']
        if answer_name not in dependencies:
            raise ValueError(f'frase di riferimento richiesta: {answer_name}')
        support = dependencies.get(support_name)
        attacks = support.notes if support is not None else ()
        foreground = dependencies[answer_name].notes
        result, supported, omitted = {}, 0, 0
        for beat, pitch, velocity in events:
            if pitch in self.support_pitches:
                if not attacks:
                    continue
                nearest = min(attacks, key=lambda n: (abs(n.beat-beat), -n.velocity, n.beat))
                if abs(nearest.beat-beat) > values['support_tolerance_beats']:
                    continue
                beat = nearest.beat
                velocity = round((velocity+nearest.velocity)/2)
                supported += 1
            elif (not foreground or any(abs(n.beat-beat) < values['answer_clearance_beats'] for n in foreground)):
                omitted += 1
                continue
            key = (beat, pitch)
            result[key] = max(result.get(key, 0), velocity)
        trace = {'support_source': support_name, 'answer_source': answer_name,
                 'available_sources': list(dependencies), 'supported_hits': supported,
                 'omitted_answer_hits': omitted, 'support_available': support is not None}
        return [(beat, pitch, velocity) for (beat, pitch), velocity in sorted(result.items())], trace

    def _standard_events(self, start, end):
        _, cycle, hits = self.standard
        events = []
        for offset, pitch, velocity in hits:
            repetition = max(0, math.ceil((start-offset)/cycle))
            while offset+repetition*cycle < end:
                if len(events) >= 128:
                    raise ValueError('il groove standard supera 128 attacchi nella finestra')
                events.append((offset+repetition*cycle-start, pitch, velocity))
                repetition += 1
        return events

    def _blend(self, standard, conceptual, start, values):
        """Scelta stabile per attacco: stessa fase e stesso seed, anche fra finestre."""
        amount = values['conceptuality']
        regular = {(beat, pitch): velocity for beat, pitch, velocity in standard}
        developed = {(beat, pitch): velocity for beat, pitch, velocity in conceptual}
        result = []
        for beat, pitch in sorted(regular.keys() | developed.keys()):
            if (beat, pitch) in regular and (beat, pitch) in developed:
                velocity = round(regular[beat, pitch]*(1-amount)+developed[beat, pitch]*amount)
            else:
                rng = random.Random(f'{values["seed"]}:{start+beat:.9f}:{pitch}')
                source = developed if rng.random() < amount else regular
                velocity = source.get((beat, pitch))
            if velocity is not None:
                result.append((beat, pitch, velocity))
        return result

    def __call__(self, request):
        values = self.validate(request.role, request.parameters)
        if (not math.isfinite(request.start) or request.start < 0
                or not math.isfinite(request.length_beats) or request.length_beats <= 0):
            raise ValueError('inizio non negativo e lunghezza positiva richiesti')
        # Ripianificare lo stesso inizio non consuma due volte il materiale.
        start = self.last_position if request.start == self.last_start else self.position
        end = start+request.length_beats
        if not math.isfinite(end) or end <= start:
            raise ValueError('finestra percussiva non rappresentabile')
        first, last = math.floor(start/self.cycle), math.ceil(end/self.cycle)
        if last-first > 128:
            raise ValueError('la richiesta supera 128 cicli percussivi')
        events, operations = [], []
        for index in range(first, last):
            operation, hits = self._cycle(index, values)
            operations.append({'cycle': index, 'operation': operation})
            for beat, pitch, velocity in hits:
                absolute = index*self.cycle+beat
                if start <= absolute < end:
                    events.append((absolute-start, pitch, velocity))
        if len(events) > 128:
            raise ValueError('lo sviluppo supera 128 attacchi nella finestra')
        interaction = {'support_source': self.interaction['support_source'],
                       'answer_source': self.interaction['answer_source'],
                       'available_sources': list(request.dependencies), 'supported_hits': 0,
                       'omitted_answer_hits': 0, 'support_available': self.interaction['support_source'] in request.dependencies}
        if values['conceptuality']:
            events, interaction = self._interact(events, request.dependencies, values)
        if values['conceptuality'] < 1:
            standard = self._standard_events(start, end)
            events = (self._blend(standard, events, start, values) if values['conceptuality'] else sorted(standard))
        if len(events) > 128:
            raise ValueError('la combinazione supera 128 attacchi nella finestra')
        notes, next_attack = [], {}
        for beat, pitch, velocity in reversed(events):
            duration = min(values['gate_beats'], request.length_beats-beat,
                           next_attack.get(pitch, request.length_beats)-beat)
            notes.append(Note(beat, pitch, duration, max(1, min(127, round(velocity*values['velocity_ratio'])))))
            next_attack[pitch] = beat
        phrase = Phrase(request.length_beats, tuple(reversed(notes)))
        self.last_start, self.last_position, self.position = request.start, start, end
        self.last_decision = {'method': 'percussion_phrase', 'material': self.name,
                              'conceptuality': values['conceptuality'],
                              'standard_material': self.standard[0] if self.standard else None,
                              'logical_start': start, 'cycles': operations,
                              'interaction': interaction,
                              'summary': f'carattere {values["conceptuality"]:.2f} · {self.name} · ' + ', '.join(o['operation'] for o in operations)
                                         + f' · {interaction["supported_hits"]} sostegni, '
                                         + f'{interaction["omitted_answer_hits"]} risposte omesse · {len(notes)} attacchi'}
        return phrase

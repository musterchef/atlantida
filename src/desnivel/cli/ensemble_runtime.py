"""Sessione continua: viaggio indipendente dai beat, pianificazione e stato globale."""
from __future__ import annotations

from copy import deepcopy
import math
import time

import numpy as np

from desnivel.adapters.voice_device import DeviceVoice
from desnivel.cli.ensemble import EnsembleSession
from desnivel.cli.generators import build_generator
from desnivel.music.phrases import Phrase


class EnsembleRuntime:
    def __init__(self, track, config, bridge, speed=1., clock=time.monotonic):
        if not math.isfinite(speed) or speed <= 0:
            raise ValueError('speed deve essere positiva e finita')
        self.track, self.bridge, self.speed, self.clock = track, bridge, speed, clock
        self.window, self.lead = config['window_beats'], config['lead_beats']
        if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in (self.window, self.lead)):
            raise ValueError('finestra e anticipo devono essere positivi e finiti')
        distances = track.samples.get('cum_dist_m')
        if distances is None or len(distances) != len(track.t) or not len(track.t):
            raise ValueError('traccia con distanza cumulativa richiesta')
        self.distances = distances
        if not np.all(np.isfinite(distances)) or distances[-1] <= distances[0] or track.duration_s <= 0:
            raise ValueError('durata e distanza della traccia devono essere positive')
        self.transport_voice = config['transport_voice']
        if self.transport_voice not in config['voices']:
            raise ValueError('transport_voice non registrata')
        self.elapsed = 0.
        self.playing = False
        self.beat = 0.
        self.epoch = None
        self.instance = None
        self.transport_serial = -1
        self.error = None
        self.last_update = clock()
        self.planned_start = None
        self.last_section = None
        self.last_decisions = None
        self.sounding = set()
        self.registry = {}
        self.voice_descriptions = {name: {'name': spec.get('name', name), 'generator': spec['generator'],
                                         'dependencies': list(spec.get('dependencies', []))}
                                   for name, spec in config['voices'].items()}
        session_config = deepcopy(config)
        destinations = {}
        for name, voice in session_config['voices'].items():
            definition = config['generators'][voice['generator']]
            self.registry[name] = build_generator(definition)
            if definition['type'] == 'responsive_line' and len(voice.get('dependencies', [])) != 1:
                raise ValueError('responsive_line richiede una dipendenza')
            voice['generator'] = name  # Ogni voce ha il proprio generatore e il proprio stato.
            destination = voice['destination']
            if destination in destinations:
                raise ValueError('ogni voce richiede una destinazione distinta')
            bridge.voices[name] = DeviceVoice()
            destinations[destination] = bridge.destination(name)
        self.session = EnsembleSession(session_config, {name: spec.generator for name, spec in self.registry.items()}, destinations)
        for name, registered in self.registry.items():
            bridge.voices[name] = DeviceVoice.for_session(
                self.session, name, lambda: self.progress,
                controls=registered.controls, values=registered.values, presets=registered.presets)
        self.state = 'waiting_for_transport'

    @property
    def progress(self):
        distance = float(np.interp(self.track.t[0]+self.elapsed, self.track.t, self.distances))
        return min(1., max(0., (distance-self.distances[0])/(self.distances[-1]-self.distances[0])))

    def reset(self):
        for name in self.sounding:
            if self.bridge.connected(name):
                self.bridge.reset(name)
        self.sounding.clear()
        self.planned_start = None
        self.last_section = None
        self.last_decisions = None
        for registered in self.registry.values():
            if registered.reset:
                registered.reset()

    def on_message(self, bridge, message):
        if message['voice'] != self.transport_voice:
            return
        if message['instance'] == self.instance and message['serial'] <= self.transport_serial:
            return
        transport = message.get('transport', {})
        beat, playing, epoch = transport.get('beat'), transport.get('playing'), transport.get('epoch')
        if (type(beat) not in (int, float) or not math.isfinite(beat) or beat < 0
                or type(playing) is not int or playing not in (0, 1)
                or type(epoch) is not int or epoch < 0):
            raise ValueError('stato del trasporto non valido')
        self.advance()
        if self.instance != message['instance'] or self.epoch != epoch or beat < self.beat or not playing:
            self.reset()
        self.instance, self.transport_serial = message['instance'], message['serial']
        self.beat, self.playing, self.epoch = beat, bool(playing), epoch

    def advance(self):
        now = self.clock()
        delta, self.last_update = max(0., now-self.last_update), now
        if self.playing and self.state == 'playing' and self.bridge.connected(self.transport_voice) and not self.error:
            self.elapsed = min(self.track.duration_s, self.elapsed+delta*self.speed)

    def tick(self):
        self.advance()
        if self.error:
            self.state = 'error'
            return
        if self.elapsed >= self.track.duration_s:
            self.state = 'finished'
            self.reset()
            return
        assignments = self.session.director.assignments_at(self.progress)
        if not self.bridge.connected(self.transport_voice):
            self.state = 'waiting_for_transport'
        elif not self.playing:
            self.state = 'stopped'
        elif any(not self.bridge.connected(name) for name in assignments):
            self.state = 'waiting_for_devices'
        else:
            self.state = 'playing'
        if self.state != 'playing':
            if self.sounding:
                self.reset()
            return
        start = math.ceil((self.beat+self.lead)/self.window)*self.window
        if start == self.planned_start:
            return
        context = self.session.director.context_at(self.progress)
        # I cambi di organico si applicano alla prossima finestra, con frasi vuote
        # per le parti uscenti: la finestra già iniziata può concludersi.
        phrases = self.session.plan(self.progress, start, self.window)
        for name in self.sounding - phrases.keys():
            if self.bridge.connected(name):
                self.bridge.destination(name)(start, Phrase(self.window, ()))
        self.sounding |= set(phrases)
        self.session.send(start, phrases)
        self.sounding = set(phrases)
        self.planned_start, self.last_section = start, context.name
        self.last_decisions = {**self.session.coordinator.last_plan, 'section': context.name}

    def fail(self, error):
        self.error = str(error)
        self.reset()
        self.state = 'error'

    def snapshot(self):
        context = self.session.director.context_at(self.progress)
        return {'version': 1, 'state': self.state, 'error': self.error,
                'decisions': {'director': self.session.director.decision_at(self.progress),
                              'coordinator': self.last_decisions},
                'trip': {'stage': self.track.stage_id, 'elapsed_s': self.elapsed,
                         'duration_s': self.track.duration_s, 'progress': self.progress, 'speed': self.speed,
                         'distance_m': float(np.interp(self.track.t[0]+self.elapsed, self.track.t, self.distances)),
                         'total_distance_m': float(self.distances[-1])},
                'section': {'index': context.section_index, 'name': context.name,
                            'root': context.root, 'scale': context.scale},
                'transport': {'voice': self.transport_voice, 'playing': self.playing,
                              'beat': self.beat, 'epoch': self.epoch},
                'planning': {'next_start': self.planned_start, 'section': self.last_section,
                             'window_beats': self.window}, 'voices': {name: {**self.voice_descriptions[name], **state}
                           for name, state in self.bridge.status().items()}}

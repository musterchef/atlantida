"""Pianificazione da snapshot Snake con posizione assoluta del trasporto."""
from __future__ import annotations

from dataclasses import asdict, replace
import math
import uuid

from desnivel.adapters.snake_sequence import SnakeState, SPEEDS, predict
from desnivel.bass import BassSettings, generate_bass


class BassSession:
    def __init__(self, settings=BassSettings(), window=4.0, lead=1.0):
        if not all(math.isfinite(x) and x>0 for x in (window,lead)):
            raise ValueError('window e lead devono essere positivi e finiti')
        self.settings, self.window, self.lead = settings, window, lead
        self.run_id = uuid.uuid4().hex
        self.source = None
        self.serial = -1
        self.session = None
        self.plans = {}
        self.revision = 0

    def update(self, snapshot):
        if snapshot['version'] != 1:
            raise ValueError('versione snapshot non supportata')
        source = snapshot['source']
        if not isinstance(source, str) or not source:
            raise ValueError('sorgente snapshot non valida')
        if self.source is not None and self.source != source:
            raise ValueError('sorgente Snake cambiata: può essere un reload o un’altra istanza; riavviare live_bass e mantenere un solo Export attivo')
        serial = snapshot['serial']
        if type(serial) is not int or serial<0:
            raise ValueError('seriale snapshot non valido')
        if serial<=self.serial:
            return None
        self.source, self.serial = source, serial
        session = f"{source}:{snapshot['epoch']}:{self.run_id}"
        if self.session != session:
            self.session, self.plans = session, {}
        if not snapshot['playing'] or snapshot.get('error'):
            self.plans = {}
            return {'version':1,'session':session,'serial':serial,'reset':True}
        beat = snapshot['beat']
        if not math.isfinite(beat) or beat<0:
            raise ValueError('posizione trasporto non valida')
        state = SnakeState.from_dict(snapshot['state'])
        start = math.ceil((beat+self.lead)/self.window)*self.window
        elapsed = start-beat
        lanes = {}
        for name in ('notes_lane','gates_lane','velocities_lane'):
            lane = getattr(state,name)
            period = float(SPEEDS[lane.speed])*lane.steps
            lanes[name] = replace(lane,phase_beats=round((lane.phase_beats+elapsed)%period,9))
        future = replace(state,**lanes)
        melody = predict(future,self.window)
        previous = self.plans.get(start-self.window)
        last = previous['phrase']['notes'][-1]['pitch'] if previous and previous['phrase']['notes'] else None
        bass = generate_bass(melody,self.settings,last,phrase_index=round(start/self.window))
        self.revision += 1
        plan = {'version':1,'session':session,'serial':serial,'revision':self.revision,
                'start':start,'phrase':asdict(bass)}
        # Ripetere lo stesso piano permette il recupero da un datagramma perso.
        # Il player scarta i duplicati senza riavviare la frase.
        existing = self.plans.get(start)
        if existing and existing['phrase']==plan['phrase']:
            return {**existing, 'serial':serial}
        self.plans[start] = plan
        self.plans = {k:v for k,v in self.plans.items() if k>=start-2*self.window}
        return plan

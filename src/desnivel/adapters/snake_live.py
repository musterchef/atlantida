"""Pianificazione da snapshot Snake con posizione assoluta del trasporto."""
from __future__ import annotations

from dataclasses import asdict, replace
import math
import uuid

from desnivel.adapters.snake_sequence import SnakeState, SPEEDS, predict
from desnivel.music.bass.generator import BassSettings, generate_bass, interpolate_settings


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
        self._transition = None
        self._last_start = None

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
            if self._transition is not None:
                # Una discontinuità riparte dall'ultimo valore, senza riusare il beat vecchio.
                _, target, _, windows = self._transition
                self._transition = (self.settings, target, None, windows)
            self._last_start = None
        if not snapshot['playing'] or snapshot.get('error'):
            self.plans = {}
            return {'version':1,'session':session,'serial':serial,'reset':True}
        beat = snapshot['beat']
        if not math.isfinite(beat) or beat<0:
            raise ValueError('posizione trasporto non valida')
        state = SnakeState.from_dict(snapshot['state'])
        start = math.ceil((beat+self.lead)/self.window)*self.window
        if self._transition is not None and self._transition[2] is None:
            initial, target, _, windows = self._transition
            self._transition = (initial, target, start, windows)
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
        bass = generate_bass(melody,self._settings_at(start),last,phrase_index=round(start/self.window))
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

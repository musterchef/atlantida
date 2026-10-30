"""Coordinamento delle dipendenze tra voci musicali."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from types import MappingProxyType
from typing import Callable, Mapping

from desnivel.music.director import MusicalContext
from desnivel.music.arrangement import Assignment
from desnivel.music.phrases import Phrase
from desnivel.music.presence import participates


@dataclass(frozen=True)
class PlanningRequest:
    start: float
    length_beats: float
    context: MusicalContext | None
    dependencies: Mapping[str, Phrase]
    role: str | None = None
    parameters: Mapping = field(default_factory=dict)


@dataclass(frozen=True)
class Voice:
    generate: Callable[[PlanningRequest], Phrase]
    dependencies: tuple[str, ...] = ()
    supported_roles: tuple[str, ...] = ()
    describe: Callable[[], dict] | None = None
    optional_dependencies: tuple[str, ...] = ()


class MusicCoordinator:
    """Ordina i generatori secondo le dipendenze e raccoglie le loro frasi.

    Le voci e le frasi sorgente sono identificate dal chiamante. Nessuna
    voce ha un ruolo privilegiato; ogni generatore riceve le sole dipendenze
    dichiarate e lo stesso intervallo e contesto musicale.
    """

    def __init__(self, voices: Mapping[str, Voice]):
        self._voices = dict(voices)
        self.last_plan = None

    def plan(self, start: float, length_beats: float,
             context: MusicalContext | None = None, *,
             sources: Mapping[str, Phrase] | None = None,
             assignments: Mapping[str, Assignment] | None = None) -> dict[str, Phrase]:
        if not math.isfinite(start) or start < 0:
            raise ValueError('start deve essere finito e non negativo')
        if not math.isfinite(length_beats) or length_beats <= 0:
            raise ValueError('length_beats deve essere finita e positiva')
        active = self._voices if assignments is None else {
            name: self._voices[name] for name in assignments if name in self._voices}
        if assignments is not None:
            if set(assignments) - self._voices.keys():
                raise ValueError('voce assegnata non registrata')
            for name, assignment in assignments.items():
                if assignment.role not in active[name].supported_roles:
                    raise ValueError(f'ruolo non supportato dalla voce {name}: {assignment.role}')
        phrases = dict(sources or {})
        if phrases.keys() & active.keys():
            raise ValueError('una voce non può essere anche una sorgente fornita')
        if any(p.length_beats != length_beats for p in phrases.values()):
            raise ValueError('le sorgenti devono coprire la finestra musicale')
        # Verifica tutto il grafo prima di chiamare generatori con eventuale stato.
        available = set(phrases)
        pending = dict(active)
        order = []
        while pending:
            ready = [name for name, voice in pending.items()
                     if (set(voice.dependencies) | (set(voice.optional_dependencies) & active.keys())) <= available]
            if not ready:
                raise ValueError('dipendenze mancanti o cicliche tra le voci')
            for name in ready:
                order.append(name)
                available.add(name)
                del pending[name]
        decisions = {}
        for name in order:
            voice = active[name]
            references = (*voice.dependencies, *(key for key in voice.optional_dependencies if key in phrases))
            dependencies = MappingProxyType({key: phrases[key] for key in references})
            assignment = assignments[name] if assignments is not None else None
            phrase = voice.generate(PlanningRequest(
                start, length_beats, context, dependencies,
                assignment.role if assignment else None,
                MappingProxyType(dict(assignment.parameters)) if assignment else MappingProxyType({})))
            if phrase.length_beats != length_beats:
                raise ValueError(f'la voce {name} deve coprire la finestra musicale')
            presence = assignment.presence if assignment else 1.
            participating = participates(name, start, presence)
            if not participating:
                phrase = Phrase(length_beats, ())
            phrases[name] = phrase
            decisions[name] = {
                'presence': presence,
                'participating': participating,
                'role': assignment.role if assignment else None,
                'dependencies': list(references),
                'parameters': dict(assignment.parameters) if assignment else {},
                'notes': [asdict(note) for note in phrase.notes],
                'composition': dict(voice.describe()) if voice.describe else None,
            }
        self.last_plan = {'start': start, 'length_beats': length_beats,
                          'order': order, 'voices': decisions}
        return {name: phrases[name] for name in active}

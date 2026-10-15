"""Composizione della pipeline: modulatori + detector + classifier + sink.

La pipeline è un oggetto dichiarativo: si costruisce con le liste dei
trasformatori, dei detector e dei classifier, e si esegue su un `Track`
producendo modulazioni ed eventi. I cooldown e i limiti per categoria
vengono applicati qui (non nei singoli detector).

Eventi *framing* (``start`` e ``end``) sono sempre presenti per ogni
tappa e bypassano cooldown e cap: sono pilastri narrativi, non gesti
opzionali. Vedi CONTRATTO-MODULAZIONI.md §3.1.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .classifiers.base import EventClassifier
from .config import DEFAULT_CONFIG, Config
from .detectors.base import EventDetector
from .events import Event, EventCategory
from .modulation import ModulationFrame
from .modulators.base import Modulator
from .sinks.base import Sink
from .track import Track

# Eventi che devono comparire sempre, una sola volta per tappa.
# Bypassano cooldown e cap.
FRAMING_KINDS: frozenset[str] = frozenset({"start", "end"})


@dataclass
class Pipeline:
    """Esecutore della pipeline DESNIVEL."""

    modulators: list[Modulator] = field(default_factory=list)
    detectors: list[EventDetector] = field(default_factory=list)
    classifiers: list[EventClassifier] = field(default_factory=list)
    sinks: list[Sink] = field(default_factory=list)
    config: Config = DEFAULT_CONFIG

    def run(self, track: Track) -> tuple[ModulationFrame, list[Event]]:
        frame = self._run_modulators(track)
        events = self._run_detectors(track)
        events = self._apply_classifiers(events, track)
        events = self._filter_events(events, track.duration_s)
        for sink in self.sinks:
            sink.emit(track.stage_id, frame, events)
        return frame, events

    def _run_modulators(self, track: Track) -> ModulationFrame:
        frame = ModulationFrame(t=track.t)
        for mod in self.modulators:
            frame = mod.process(track, frame)
        return frame

    def _run_detectors(self, track: Track) -> list[Event]:
        events: list[Event] = []
        for det in self.detectors:
            events.extend(det.detect(track))
        events.sort(key=lambda e: e.t)
        return events

    def _apply_classifiers(
        self, events: list[Event], track: Track,
    ) -> list[Event]:
        """Fonde nel payload di ogni evento i contributi dei classifier
        applicabili. Restituisce nuovi `Event` (immutabili)."""
        if not self.classifiers:
            return events
        enriched: list[Event] = []
        for ev in events:
            payload: dict[str, Any] = dict(ev.payload)
            for clf in self.classifiers:
                kinds = clf.applies_to_kinds
                if kinds is not None and ev.kind not in kinds:
                    continue
                contribution = clf.classify(ev, track)
                if contribution:
                    payload = _merge_payload(payload, contribution)
            enriched.append(_replace_payload(ev, payload))
        return enriched

    def _filter_events(
        self, events: list[Event], stage_duration_s: float,
    ) -> list[Event]:
        cfg = self.config.events
        cooldowns = {
            EventCategory.MAJOR: cfg.major_cooldown_s(stage_duration_s),
            EventCategory.MINOR: cfg.minor_cooldown_s(stage_duration_s),
        }
        kept: list[Event] = []
        last_t: dict[EventCategory, float] = {}
        major_count = 0
        for ev in events:
            # Framing (start/end) bypassano cooldown e cap, ma il loro
            # timestamp aggiorna last_t cosi' un MAJOR ordinario troppo
            # vicino al framing viene comunque scartato.
            if ev.kind in FRAMING_KINDS:
                kept.append(ev)
                last_t[ev.category] = ev.t
                continue
            cooldown = cooldowns[ev.category]
            prev = last_t.get(ev.category)
            if prev is not None and (ev.t - prev) < cooldown:
                continue
            if ev.category is EventCategory.MAJOR:
                if major_count >= cfg.major_max_per_stage:
                    continue
                major_count += 1
            kept.append(ev)
            last_t[ev.category] = ev.t
        return kept


def _merge_payload(
    base: dict[str, Any], contribution: Mapping[str, Any],
) -> dict[str, Any]:
    """Fonde un contributo di classifier nel payload base.

    Convenzione: ``variants`` (lista) viene unita preservando l'ordine
    e senza duplicati; le altre chiavi sovrascrivono.
    """
    merged = dict(base)
    for key, value in contribution.items():
        if key == "variants":
            existing = list(merged.get("variants", []))
            for v in value:
                if v not in existing:
                    existing.append(v)
            merged["variants"] = existing
        else:
            merged[key] = value
    return merged


def _replace_payload(ev: Event, payload: Mapping[str, Any]) -> Event:
    """Ricostruisce un Event con payload diverso (Event e' frozen)."""
    return Event(
        kind=ev.kind,
        category=ev.category,
        t=ev.t,
        location=ev.location,
        payload=payload,
        source_id=ev.source_id,
    )


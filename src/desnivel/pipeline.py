"""Composizione della pipeline: modulatori + detector + sink.

La pipeline è un oggetto dichiarativo: si costruisce con le liste dei
trasformatori e dei detector, e si esegue su un `Track` producendo
modulazioni ed eventi. I cooldown e i limiti per categoria vengono
applicati qui (non nei singoli detector).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import DEFAULT_CONFIG, Config
from .detectors.base import EventDetector
from .events import Event, EventCategory
from .modulation import ModulationFrame
from .modulators.base import Modulator
from .sinks.base import Sink
from .track import Track


@dataclass
class Pipeline:
    """Esecutore della pipeline DESNIVEL."""

    modulators: list[Modulator] = field(default_factory=list)
    detectors: list[EventDetector] = field(default_factory=list)
    sinks: list[Sink] = field(default_factory=list)
    config: Config = DEFAULT_CONFIG

    def run(self, track: Track) -> tuple[ModulationFrame, list[Event]]:
        frame = self._run_modulators(track)
        events = self._run_detectors(track)
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

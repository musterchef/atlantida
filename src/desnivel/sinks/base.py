"""Interfaccia base per i sink di output."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..events import Event
from ..modulation import ModulationFrame


@runtime_checkable
class Sink(Protocol):
    """Riceve l'output completo della pipeline (modulazioni + eventi)
    e lo materializza (file, OSC, ecc.).
    """

    def emit(self, stage_id: str, frame: ModulationFrame,
             events: list[Event]) -> None:
        ...

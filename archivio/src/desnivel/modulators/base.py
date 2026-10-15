"""Interfaccia base per i modulatori."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..modulation import ModulationFrame
from ..track import Track


@runtime_checkable
class Modulator(Protocol):
    """Trasformatore puro: aggiunge canali al `ModulationFrame`.

    Convenzioni:
    - Non modifica il `Track` di ingresso.
    - Aggiunge esclusivamente le colonne dichiarate in `output_channels`.
    - È idempotente: chiamato due volte sullo stesso frame fallisce
      al secondo (i canali esistono già), comportamento desiderato.
    """

    @property
    def output_channels(self) -> tuple[str, ...]:
        """Nomi dei canali prodotti."""

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        ...

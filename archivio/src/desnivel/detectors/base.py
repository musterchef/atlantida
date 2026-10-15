"""Interfaccia base per i rilevatori di eventi."""
from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from ..events import Event
from ..track import Track


@runtime_checkable
class EventDetector(Protocol):
    """Produce zero o più eventi a partire da un `Track`.

    Convenzioni:
    - Non modifica il `Track`.
    - Restituisce eventi in qualunque ordine: la pipeline li ordinerà.
    - Non applica cooldown globali (li applica la pipeline).
    """

    def detect(self, track: Track) -> Iterable[Event]:
        ...

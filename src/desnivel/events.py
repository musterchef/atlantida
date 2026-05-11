"""Modello degli eventi e registry estendibile.

Un evento è un oggetto con campi essenziali (kind, category, t, location,
payload). Il `kind` è una stringa registrata in `EVENT_REGISTRY` insieme
ai metadati (etichetta, categoria di default, schema del payload) che
servono sia per la validazione sia, in futuro, per generare la UI di
un editor di eventi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .track import GeoPoint


class EventCategory(str, Enum):
    """Categorie del contratto. `MAJOR` produce gesti musicali identificabili;
    `MINOR` accelera transizioni di stato senza generare note."""

    MAJOR = "major"
    MINOR = "minor"


class EventSource(str, Enum):
    """Origine dell'evento."""

    DERIVED = "derived"
    """Calcolato dai dati GPX da un detector."""
    EXTERNAL = "external"
    """Dichiarato dall'autore in `events/<stage>.json`."""


@dataclass(frozen=True)
class Event:
    """Evento generato dalla pipeline o dichiarato esternamente.

    Attributes:
        kind: identificatore registrato, es. ``"summit"``, ``"pioggia_torrenziale"``.
        category: ``MAJOR`` o ``MINOR``.
        t: tempo in secondi dall'inizio della tappa.
        location: posizione geografica, opzionale.
        payload: campi specifici del `kind`, validati dal registry.
    """

    kind: str
    category: EventCategory
    t: float
    location: GeoPoint | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "category": self.category.value,
            "t": self.t,
            "location": (
                {"lat": self.location.lat, "lon": self.location.lon,
                 "ele": self.location.ele}
                if self.location is not None
                else None
            ),
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class EventType:
    """Metadati di un tipo di evento, condivisi con l'editor futuro.

    Attributes:
        kind: identificatore univoco.
        label: nome leggibile per la UI.
        default_category: categoria suggerita all'utente.
        source: chi produce questo tipo di evento (derivato o esterno).
        payload_schema: JSON Schema del payload (validazione + UI).
        description: breve descrizione opzionale.
    """

    kind: str
    label: str
    default_category: EventCategory
    source: EventSource
    payload_schema: Mapping[str, Any] = field(default_factory=dict)
    description: str = ""


class EventRegistry:
    """Registro centrale dei tipi di evento conosciuti dal sistema."""

    def __init__(self) -> None:
        self._types: dict[str, EventType] = {}

    def register(self, event_type: EventType) -> None:
        if event_type.kind in self._types:
            raise KeyError(f"Tipo di evento '{event_type.kind}' già registrato")
        self._types[event_type.kind] = event_type

    def get(self, kind: str) -> EventType:
        try:
            return self._types[kind]
        except KeyError as exc:
            raise KeyError(f"Tipo di evento '{kind}' non registrato") from exc

    def has(self, kind: str) -> bool:
        return kind in self._types

    def all(self) -> tuple[EventType, ...]:
        return tuple(self._types.values())


EVENT_REGISTRY = EventRegistry()
"""Registry globale. I tipi standard si registrano in `desnivel.events_builtin`."""

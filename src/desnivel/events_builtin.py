"""Registrazione dei tipi di evento standard del progetto DESNIVEL.

Importando questo modulo si popola `EVENT_REGISTRY` con i tipi base.
Nuovi tipi (specifici di una tappa o sperimentali) possono essere
registrati altrove senza modificare questo file.
"""
from __future__ import annotations

from .events import EVENT_REGISTRY, EventCategory, EventSource, EventType


def _empty_object_schema() -> dict:
    """Schema permissivo: oggetto qualunque."""
    return {"type": "object", "additionalProperties": True}


# --- Eventi maggiori derivati ----------------------------------------------

EVENT_REGISTRY.register(EventType(
    kind="start",
    label="Inizio tappa",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema=_empty_object_schema(),
    description="Apertura della tappa, una sola volta.",
))

EVENT_REGISTRY.register(EventType(
    kind="end",
    label="Fine tappa",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema=_empty_object_schema(),
    description="Chiusura della tappa, una sola volta.",
))

EVENT_REGISTRY.register(EventType(
    kind="summit",
    label="Vetta principale",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {
            "ele_m": {"type": "number"},
            "prominence_m": {"type": "number"},
        },
        "required": ["ele_m"],
        "additionalProperties": True,
    },
    description=(
        "Picco interno con prominenza topografica massima sopra soglia. "
        "Non e' il massimo globale: tappe che terminano in cima usano "
        "'arrival_climb' invece."
    ),
))

EVENT_REGISTRY.register(EventType(
    kind="arrival_climb",
    label="Arrivo in salita",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {
            "climb_delta_m": {"type": "number"},
            "final_ele_m": {"type": "number"},
        },
        "required": ["climb_delta_m"],
        "additionalProperties": True,
    },
    description=(
        "Tappa che termina significativamente piu' in alto del minimo "
        "della seconda meta'. Es. arrivo in collina (Dogliani, Castel del Monte)."
    ),
))

EVENT_REGISTRY.register(EventType(
    kind="sea",
    label="Arrivo al mare",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {"distance_m": {"type": "number"}},
        "additionalProperties": True,
    },
    description="Prima volta sotto la soglia di distanza dalla costa.",
))

EVENT_REGISTRY.register(EventType(
    kind="city_arrival",
    label="Arrivo in città",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {"city_name": {"type": "string"}},
        "additionalProperties": True,
    },
    description="Ingresso nella città di arrivo della tappa.",
))

# --- Eventi minori derivati -------------------------------------------------

EVENT_REGISTRY.register(EventType(
    kind="territory_change",
    label="Cambio di territorio",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {
            "from": {"type": "string"},
            "to": {"type": "string"},
            "intensity": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "additionalProperties": True,
    },
))

EVENT_REGISTRY.register(EventType(
    kind="city_enter",
    label="Ingresso in area urbana",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema=_empty_object_schema(),
))

EVENT_REGISTRY.register(EventType(
    kind="city_exit",
    label="Uscita da area urbana",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema=_empty_object_schema(),
))

EVENT_REGISTRY.register(EventType(
    kind="stop",
    label="Sosta prolungata",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {"duration_s": {"type": "number"}},
        "additionalProperties": True,
    },
))

EVENT_REGISTRY.register(EventType(
    kind="resume",
    label="Ripresa del movimento",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema=_empty_object_schema(),
))

EVENT_REGISTRY.register(EventType(
    kind="local_summit",
    label="Massimo locale di altitudine",
    default_category=EventCategory.MINOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {"elevation_m": {"type": "number"}},
        "additionalProperties": True,
    },
))

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
    payload_schema={
        "type": "object",
        "properties": {
            "variants": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "additionalProperties": True,
    },
    description=(
        "Apertura della tappa, una sola volta. Il carattere specifico "
        "(dawn, urban, manual, ...) e' codificato in payload.variants "
        "dai classifier pluggabili. Vedi CONTRATTO-MODULAZIONI.md §3.1.1."
    ),
))

EVENT_REGISTRY.register(EventType(
    kind="end",
    label="Fine tappa",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {
            "variants": {
                "type": "array",
                "items": {"type": "string"},
            },
            "climb_delta_m": {"type": "number"},
            "final_ele_m": {"type": "number"},
            "coast_distance_m": {"type": "number"},
            "coast_median_m": {"type": "number"},
            "coast_below_fraction_1000": {"type": "number"},
            "ele_median_m": {"type": "number"},
            "ele_max_m": {"type": "number"},
        },
        "additionalProperties": True,
    },
    description=(
        "Chiusura della tappa, una sola volta. Il carattere specifico "
        "(climb, sunset, natural, urban, ...) e' codificato in "
        "payload.variants dai classifier pluggabili. "
        "Vedi CONTRATTO-MODULAZIONI.md §3.1.1."
    ),
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
        "l'evento 'end' con variante 'climb' (vedi §3.1.1)."
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
    kind="poi",
    label="Passaggio in POI",
    default_category=EventCategory.MAJOR,
    source=EventSource.DERIVED,
    payload_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "kind": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "distance_from_center_m": {"type": "number"},
        },
        "additionalProperties": True,
    },
    description=(
        "Entrata nel raggio di un POI del registry (città, borgo, "
        "landmark). Un evento per ogni entrata fresca; il re-entry sullo "
        "stesso POI richiede un cooldown configurabile."
    ),
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

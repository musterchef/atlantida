"""Registry di POI (città, borghi, landmark) con query spaziali.

Modello uniforme: un POI è un punto WGS84 con raggio in metri e
metadati liberi (`kind`, `tags`). Il detector non distingue città
da landmark: il `kind` è solo informativo per il mapping musicale a
valle.

Il manifest è un JSON curato a mano (`data/poi.json`). Pre-popolato
in modo semi-automatico da `tools/discover_poi.py` (Overpass offline),
poi filtrato/corretto manualmente: il repository resta deterministico
e senza rete a runtime.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np

from .coastline import haversine_m


@dataclass(frozen=True)
class POI:
    """Un punto di interesse con raggio di attivazione."""

    name: str
    lat: float
    lon: float
    radius_m: float
    kind: str = "poi"
    tags: tuple[str, ...] = field(default_factory=tuple)


class POIRegistry:
    """Insieme di POI con query spaziali vettoriali.

    Le coordinate dei POI sono materializzate in array numpy per
    consentire query batch sull'intera tappa in un solo passo.
    """

    def __init__(self, pois: Iterable[POI]) -> None:
        self._pois: tuple[POI, ...] = tuple(pois)
        if self._pois:
            self._lats = np.array([p.lat for p in self._pois], dtype=float)
            self._lons = np.array([p.lon for p in self._pois], dtype=float)
            self._radii = np.array([p.radius_m for p in self._pois], dtype=float)
        else:
            self._lats = np.zeros(0)
            self._lons = np.zeros(0)
            self._radii = np.zeros(0)

    def __len__(self) -> int:
        return len(self._pois)

    @property
    def pois(self) -> tuple[POI, ...]:
        return self._pois

    def distances_m(self, lat: float, lon: float) -> np.ndarray:
        """Distanze haversine in metri da `(lat, lon)` a tutti i POI."""
        if not self._pois:
            return np.zeros(0)
        # Haversine vettoriale.
        phi1 = np.radians(lat)
        phi2 = np.radians(self._lats)
        dphi = np.radians(self._lats - lat)
        dlmb = np.radians(self._lons - lon)
        a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2.0) ** 2
        return 2.0 * 6_371_000.0 * np.arcsin(np.sqrt(a))

    def inside_indices(self, lat: float, lon: float) -> list[int]:
        """Indici dei POI il cui cerchio contiene `(lat, lon)`."""
        if not self._pois:
            return []
        d = self.distances_m(lat, lon)
        return [int(i) for i in np.where(d <= self._radii)[0]]

    def nearest(self, lat: float, lon: float) -> tuple[POI, float] | None:
        """POI più vicino con distanza in metri (None se registry vuoto)."""
        if not self._pois:
            return None
        d = self.distances_m(lat, lon)
        i = int(np.argmin(d))
        return self._pois[i], float(d[i])


def default_poi_path() -> Path:
    """Percorso convenzionale del manifest POI (`data/poi.json`)."""
    return Path(__file__).resolve().parents[3] / "data" / "poi.json"


def load_poi_registry(path: Path | str | None = None) -> POIRegistry:
    """Carica un `POIRegistry` da JSON.

    Schema accettato (lista di oggetti):
        [{"name": str, "lat": float, "lon": float, "radius_m": float,
          "kind": str?, "tags": [str]?}, ...]

    Se il file non esiste ritorna un registry vuoto.
    """
    p = Path(path) if path is not None else default_poi_path()
    if not p.exists():
        return POIRegistry([])
    with p.open(encoding="utf-8") as f:
        raw = json.load(f)
    pois = [
        POI(
            name=str(item["name"]),
            lat=float(item["lat"]),
            lon=float(item["lon"]),
            radius_m=float(item["radius_m"]),
            kind=str(item.get("kind", "poi")),
            tags=tuple(item.get("tags", ())),
        )
        for item in raw
    ]
    return POIRegistry(pois)


@lru_cache(maxsize=4)
def _cached_default_registry(path_str: str) -> POIRegistry:
    return load_poi_registry(path_str)


def get_default_registry(path: Path | str | None = None) -> POIRegistry:
    """Versione cached di `load_poi_registry` (singleton per path)."""
    p = Path(path) if path is not None else default_poi_path()
    return _cached_default_registry(str(p))


__all__ = [
    "POI",
    "POIRegistry",
    "default_poi_path",
    "load_poi_registry",
    "get_default_registry",
]

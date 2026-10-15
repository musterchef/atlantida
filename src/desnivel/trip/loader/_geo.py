"""Funzioni geografiche minimali (haversine).

Stdlib + `numpy` per le versioni vettoriali. Niente dipendenze esterne.
"""
from __future__ import annotations

import math

import numpy as np

_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(
    lat1: np.ndarray, lon1: np.ndarray,
    lat2: np.ndarray, lon2: np.ndarray,
) -> np.ndarray:
    """Distanza haversine in metri tra coppie di punti (vettoriale)."""
    lat1r = np.radians(lat1)
    lat2r = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * _EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


def haversine_scalar(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Versione scalare per chiamate isolate."""
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2.0) ** 2
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))

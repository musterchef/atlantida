"""Calcolo dei canali derivati dai trackpoint grezzi.

Vettoriale e puro: prende il dizionario di array prodotto da `parse_gpx_points`
e ritorna un dizionario con i canali derivati allineati allo stesso indice:
``elapsed_s``, ``dist_m``, ``cum_dist_m``, ``speed_kmh``, ``slope``, ``effort``.
"""
from __future__ import annotations

import numpy as np

from ..config import GpxConfig
from ._geo import haversine_m


def _running_median(values: np.ndarray, window: int) -> np.ndarray:
    """Mediana mobile semplice. Pratica per smussare picchi del raw GPX."""
    if window <= 1 or values.size == 0:
        return values
    half = window // 2
    padded = np.pad(values, (half, half), mode="edge")
    out = np.empty_like(values)
    for i in range(values.size):
        out[i] = np.median(padded[i:i + window])
    return out


def _safe_div(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    out = np.zeros_like(num, dtype=float)
    np.divide(num, den, out=out, where=den > 0)
    return out


def derive_channels(
    raw: dict[str, np.ndarray],
    cfg: GpxConfig,
) -> dict[str, np.ndarray]:
    """Calcola i canali derivati a partire dagli array grezzi.

    Args:
        raw: dizionario con ``lat``, ``lon``, ``ele``, ``t_unix``.
        cfg: configurazione GPX (riferimenti, pesi, smussatura).

    Returns:
        Dizionario di array della stessa lunghezza degli ingressi.
    """
    lat = raw["lat"]
    lon = raw["lon"]
    ele_raw = raw["ele"]
    t_unix = raw["t_unix"]
    n = lat.size

    # Tempo: se mancante o irregolare, ricostruito come progressione costante.
    elapsed = _elapsed_from_unix(t_unix)

    # Distanze tra punti consecutivi (il primo è 0).
    dist = np.zeros(n, dtype=float)
    if n > 1:
        dist[1:] = haversine_m(lat[:-1], lon[:-1], lat[1:], lon[1:])
    cum_dist = np.cumsum(dist)

    # Smussatura leggera dell'elevazione per stabilizzare la pendenza.
    ele = _running_median(ele_raw, cfg.raw_median_window)
    ele_delta = np.zeros(n, dtype=float)
    if n > 1:
        ele_delta[1:] = np.diff(ele)

    # Velocità in m/s, poi km/h.
    dt = np.zeros(n, dtype=float)
    if n > 1:
        dt[1:] = np.diff(elapsed)
    speed_ms = _safe_div(dist, dt)
    speed_kmh = speed_ms * 3.6

    # Pendenza come ele_delta / dist (frazione, non %).
    slope = _safe_div(ele_delta, dist)

    # Effort normalizzato in [0, 1] come combinazione lineare di velocità
    # e pendenza positiva, ciascuna saturata sul valore di riferimento.
    speed_norm = np.clip(speed_kmh / cfg.speed_reference_kmh, 0.0, 1.0)
    slope_pos_norm = np.clip(np.maximum(slope, 0.0) / cfg.slope_reference, 0.0, 1.0)
    effort = np.clip(
        cfg.effort_weight_speed * speed_norm + cfg.effort_weight_slope * slope_pos_norm,
        0.0, 1.0,
    )

    return {
        "lat": lat,
        "lon": lon,
        "ele": ele,
        "elapsed_s": elapsed,
        "dist_m": dist,
        "cum_dist_m": cum_dist,
        "speed_kmh": speed_kmh,
        "slope": slope,
        "effort": effort,
    }


def _elapsed_from_unix(t_unix: np.ndarray) -> np.ndarray:
    """Tempo trascorso (s) dall'inizio. Se i tempi sono tutti NaN, usa
    una griglia uniforme a 1 Hz come fallback. Se sono parziali, riempie
    i buchi per interpolazione lineare sull'indice."""
    if t_unix.size == 0:
        return t_unix.copy()
    if np.all(np.isnan(t_unix)):
        return np.arange(t_unix.size, dtype=float)
    # Riempimento dei NaN con interpolazione lineare sull'indice.
    idx = np.arange(t_unix.size, dtype=float)
    mask = np.isnan(t_unix)
    if mask.any():
        t_unix = t_unix.copy()
        t_unix[mask] = np.interp(idx[mask], idx[~mask], t_unix[~mask])
    elapsed = t_unix - t_unix[0]
    # Garanzia di monotonia non-decrescente.
    return np.maximum.accumulate(elapsed)

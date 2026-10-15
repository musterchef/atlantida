"""Helper condiviso per statistiche sulla distanza dalla costa di un Track.

I classifier `coastal`, `coastal_stage` e `sea_view` lavorano tutti
sulle distanze GPS rispetto alla costa: senza una cache, ognuno
ricalcolerebbe le stesse `n` chiamate a `nearest_points`.

Cache LRU keyed per `id(track)` + identita' del provider. La pipeline
processa una tappa per volta e i classifier sono tutti istanziati su
una sola `Config`, quindi la cache si riempie con poche entry.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..track import Track
from .coastline import CoastlineProvider


@dataclass(frozen=True)
class CoastStats:
    """Statistiche aggregate della distanza dalla costa per una tappa.

    Attributes:
        median_m: mediana della distanza dalla costa (robusto agli outlier).
        below_fraction_500: frazione di tempo entro 500 m dalla costa.
        below_fraction_1000: frazione di tempo entro 1000 m dalla costa.
        ele_median_m: mediana della quota lungo la tappa.
        ele_max_m: quota massima lungo la tappa.
    """

    median_m: float
    below_fraction_500: float
    below_fraction_1000: float
    ele_median_m: float
    ele_max_m: float


def _compute_stats(
    lat: np.ndarray, lon: np.ndarray, ele: np.ndarray | None,
    coastline: CoastlineProvider, step: int,
) -> CoastStats:
    idxs = np.arange(0, lat.size, step)
    if idxs.size == 0 or idxs[-1] != lat.size - 1:
        idxs = np.append(idxs, lat.size - 1)
    d = coastline.distances_m(lat[idxs], lon[idxs])
    if ele is not None and ele.size == lat.size:
        e = np.asarray(ele[idxs], dtype=float)
        ele_med = float(np.median(e))
        ele_max = float(np.max(e))
    else:
        ele_med = 0.0
        ele_max = 0.0
    return CoastStats(
        median_m=float(np.median(d)),
        below_fraction_500=float((d < 500.0).mean()),
        below_fraction_1000=float((d < 1000.0).mean()),
        ele_median_m=ele_med,
        ele_max_m=ele_max,
    )


# Cache leggera: chiave (id(track), id(coastline), step).
# Limite 8 entry: corpus ha 12 tappe ma una pipeline ne processa una alla volta.
_CacheKey = tuple[str, int, int, int]
_CACHE: dict[_CacheKey, CoastStats] = {}
_CACHE_ORDER: list[_CacheKey] = []
_CACHE_MAX = 8


def coast_stats_for(
    track: Track, coastline: CoastlineProvider, step: int = 10,
) -> CoastStats | None:
    """Ritorna `CoastStats` per la tappa, calcolandole se necessario.

    Ritorna ``None`` se il Track non ha lat/lon o ha pochi campioni.
    `step` controlla il sottocampionamento (default 10: 1 Hz dal 10 Hz
    interno, sufficiente per mediane).
    """
    lat = track.samples.get("lat")
    lon = track.samples.get("lon")
    if lat is None or lon is None or track.n_samples < 2:
        return None
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if not (np.isfinite(lat).any() and np.isfinite(lon).any()):
        return None

    key = (track.stage_id, int(track.n_samples), id(coastline), step)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    ele = track.samples.get("ele")
    stats = _compute_stats(lat, lon, ele, coastline, step)

    _CACHE[key] = stats
    _CACHE_ORDER.append(key)
    if len(_CACHE_ORDER) > _CACHE_MAX:
        old = _CACHE_ORDER.pop(0)
        _CACHE.pop(old, None)
    return stats

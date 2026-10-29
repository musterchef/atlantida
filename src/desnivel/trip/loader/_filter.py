"""Esclusione di brevi deviazioni GPS con riconnessione verificata degli adiacenti."""
import math

import numpy as np

from ._geo import haversine_m


def filter_position_spikes(raw, cfg):
    """Restituisce punti conservati, validità degli intervalli e registro delle esclusioni.

    I punti originali non vengono modificati. Le deviazioni devono superare
    il limite di velocità, essere brevi e ridurre il percorso almeno della
    quota configurata riconnettendo gli estremi con tempi originali.
    Non applica esclusioni successive sulla stessa riconnessione.
    """
    for value in (cfg.max_speed_kmh, cfg.spike_max_gap_s):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('limite di velocità e durata di riconnessione positivi e finiti richiesti')
    if type(cfg.spike_max_removed_points) is not int or not 1 <= cfg.spike_max_removed_points <= 10:
        raise ValueError('numero massimo di punti da escludere fra 1 e 10 richiesto')
    if (type(cfg.spike_min_detour_ratio) not in (int, float)
            or not math.isfinite(cfg.spike_min_detour_ratio) or not 0 < cfg.spike_min_detour_ratio < 1):
        raise ValueError('riduzione minima della deviazione compresa fra 0 e 1 richiesta')
    n = len(raw['lat'])
    if not n or any(np.asarray(values).ndim != 1 or len(values) != n for values in raw.values()):
        raise ValueError('campioni sorgente non vuoti e allineati richiesti')
    source = np.asarray(raw['source_index'])
    segments = np.asarray(raw['segment_index'])

    def intervals(indices):
        lat, lon, times = (raw[key][indices] for key in ('lat', 'lon', 't_unix'))
        coordinates = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
        valid = coordinates[:-1] & coordinates[1:]
        distances = np.full(len(indices)-1, np.nan)
        distances[valid] = haversine_m(lat[:-1][valid], lon[:-1][valid], lat[1:][valid], lon[1:][valid])
        dt = np.diff(times)
        valid &= np.isfinite(dt) & (dt > 0) & np.isfinite(times[:-1]) & np.isfinite(times[1:])
        valid &= (segments[indices[:-1]] == segments[indices[1:]]) & (segments[indices[:-1]] > 0)
        speeds = np.full(len(indices)-1, np.nan)
        speeds[valid] = distances[valid]/dt[valid]*3.6
        return distances, dt, speeds, valid

    original = np.arange(n)
    distance, dt, speed, valid = intervals(original)
    adjacent = np.diff(source) == 1
    candidates = {}
    for edge in np.flatnonzero(valid & adjacent & (speed > cfg.max_speed_kmh)):
        for count in range(1, cfg.spike_max_removed_points+1):
            for first in range(max(1, edge-count+1), min(edge+2, n-count)):
                left, right = first-1, first+count
                if (left, right) in candidates or not (valid[left:right] & adjacent[left:right]).all():
                    continue
                duration = float(raw['t_unix'][right]-raw['t_unix'][left])
                if duration > cfg.spike_max_gap_s:
                    continue
                direct = float(haversine_m(raw['lat'][left:left+1], raw['lon'][left:left+1],
                                           raw['lat'][right:right+1], raw['lon'][right:right+1])[0])
                path = float(distance[left:right].sum())
                reduction = 1-direct/path if path > 0 else 0
                if direct/duration*3.6 <= cfg.max_speed_kmh and reduction >= cfg.spike_min_detour_ratio:
                    candidates[left, right] = (count, reduction, direct, duration, path)
    keep, reserved, removed = np.ones(n, dtype=bool), np.zeros(n, dtype=bool), []
    for (left, right), (count, reduction, direct, duration, path) in sorted(
            candidates.items(), key=lambda item: (item[1][0], -item[1][1], item[0])):
        if reserved[left:right+1].any():
            continue
        keep[left+1:right] = False
        reserved[left:right+1] = True
        removed.append({'removed_source_indices': source[left+1:right].astype(int).tolist(),
                        'start_source_index': int(source[left]), 'end_source_index': int(source[right]),
                        'duration_s': duration, 'original_distance_m': path,
                        'reconnected_distance_m': direct, 'reconnected_speed_kmh': direct/duration*3.6,
                        'detour_reduction_ratio': reduction})
    indices = np.flatnonzero(keep)
    distance, dt, speed, valid = intervals(indices)
    bridges = {(r['start_source_index'], r['end_source_index']) for r in removed}
    continuity = np.array([source[b]-source[a] == 1 or (int(source[a]), int(source[b])) in bridges
                           for a, b in zip(indices[:-1], indices[1:])], dtype=bool)
    valid &= continuity & (speed <= cfg.max_speed_kmh)
    unresolved = []
    for j in np.flatnonzero(~valid):
        a, b = indices[j:j+2]
        unresolved.append({'start_source_index': int(source[a]), 'end_source_index': int(source[b]),
                           'reason': ('above_speed_limit' if np.isfinite(speed[j]) and speed[j] > cfg.max_speed_kmh
                                      else 'skipped_point' if not continuity[j] else 'invalid_source_interval'),
                           'duration_s': float(dt[j]) if np.isfinite(dt[j]) else None,
                           'distance_m': float(distance[j]) if np.isfinite(distance[j]) else None,
                           'speed_kmh': float(speed[j]) if np.isfinite(speed[j]) else None})
    report = {'max_speed_kmh': cfg.max_speed_kmh, 'max_removed_points': cfg.spike_max_removed_points,
              'max_gap_s': cfg.spike_max_gap_s, 'min_detour_ratio': cfg.spike_min_detour_ratio,
              'original_points': n, 'retained_points': len(indices),
              'removed_points': int((~keep).sum()), 'reconnections': removed,
              'unresolved_intervals': unresolved}
    return {key: value[keep].copy() for key, value in raw.items()}, np.r_[True, valid], report

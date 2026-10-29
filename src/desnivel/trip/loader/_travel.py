"""Selezione dei tratti osservati prima della derivazione e del ricampionamento."""
import math

import numpy as np

from ._geo import haversine_m
from ._stops import infer_pauses


def restrict_to_timer(raw, intervals):
    """Seleziona solo campioni negli intervalli registrati, prima dei filtri."""
    bounds = np.asarray(intervals, dtype=float)
    if (bounds.ndim != 2 or bounds.shape[1] != 2 or not len(bounds)
            or not np.isfinite(bounds).all() or np.any(bounds[:, 1] <= bounds[:, 0])
            or np.any(bounds[1:, 0] < bounds[:-1, 1])):
        raise ValueError('intervalli timer finiti, ordinati e non sovrapposti richiesti')
    times = raw['t_unix']
    index = np.searchsorted(bounds[:, 0], times, side='right')-1
    keep = np.isfinite(times) & (index >= 0) & (times <= bounds[np.maximum(index, 0), 1])
    selected = {name: values[keep].copy() for name, values in raw.items()}
    # Conserva sia i confini del timer sia eventuali confini del file sorgente.
    original = selected['segment_index']
    pairs = np.column_stack((index[keep], original))
    _, labels = np.unique(pairs, axis=0, return_inverse=True)
    selected['segment_index'] = np.where(original > 0, labels+1, 0)
    return selected


def select_travel(raw, cfg, reconnections=(), *, timer_intervals=None):
    """Restituisce slice di punti contigui elaborabili e interruzioni escluse.

    Senza timer, le pause sono stimate dalla cadenza e dallo spostamento,
    oppure da sequenze quasi ferme prolungate. Una lacuna temporale lunga
    rimane distinta dalla pausa.
    Non crea posizioni, tempi o distanze fra tratti separati.
    """
    for value in (cfg.recording_gap_s, cfg.stop_min_duration_s, cfg.stop_radius_m,
                  cfg.pause_min_gap_s, cfg.pause_gap_factor, cfg.pause_max_speed_kmh):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('criteri di selezione del viaggio positivi e finiti richiesti')
    if cfg.pause_gap_factor <= 1:
        raise ValueError('pause_gap_factor deve essere maggiore di 1')
    times, lat, lon = (raw[key] for key in ('t_unix', 'lat', 'lon'))
    source, segment = raw['source_index'], raw['segment_index']
    n = len(times)
    if n < 2:
        raise ValueError('almeno due punti richiesti per un tratto di viaggio osservato')
    coordinates = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
    dt = np.diff(times)
    bridges = {(r['start_source_index'], r['end_source_index']) for r in reconnections}
    continuity = np.array([b-a == 1 or (int(a), int(b)) in bridges for a, b in zip(source[:-1], source[1:])], dtype=bool)
    reasons = np.full(max(0, n-1), '', dtype=object)
    reasons[dt > cfg.recording_gap_s] = 'recording_gap'
    reasons[~continuity] = 'missing_points'
    reasons[(segment[:-1] != segment[1:]) | (segment[:-1] == 0)] = 'segment_boundary'
    reasons[~np.isfinite(times[:-1]) | ~np.isfinite(times[1:]) | (dt <= 0)] = 'invalid_time'
    reasons[~(coordinates[:-1] & coordinates[1:])] = 'invalid_coordinates'
    continuous = reasons == ''
    inference = {}
    if timer_intervals is None:
        inferred, inference = infer_pauses(raw, continuous, cfg)
        reasons[continuous] = inferred[continuous]
    else:
        # Un intervallo deve essere interamente contenuto nello stesso tratto
        # del timer. I confini non vengono interpolati né spostati sui campioni.
        intervals = np.asarray(timer_intervals, dtype=float)
        index = np.searchsorted(intervals[:, 0], times[:-1], side='right')-1
        in_timer = (index >= 0) & (times[1:] <= intervals[np.maximum(index, 0), 1])
        reasons[~in_timer] = 'timer_paused'
    active = reasons == ''
    starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
    ends = np.flatnonzero(active & ~np.r_[active[1:], False])+1
    spans = []
    for start, end in zip(starts, ends):
        distance = haversine_m(lat[start:end], lon[start:end], lat[start+1:end+1], lon[start+1:end+1]).sum()
        if distance > 0:
            spans.append((int(start), int(end)+1))
        else:
            reasons[start:end] = 'stationary'
    interruptions = []
    i = 0
    while i < len(reasons):
        if not reasons[i]:
            i += 1
            continue
        end = i+1
        while end < len(reasons) and reasons[end] == reasons[i]:
            end += 1
        duration = times[end]-times[i]
        interruptions.append({'reason': reasons[i], 'start_source_index': int(source[i]),
                              'end_source_index': int(source[end]),
                              'source_start_unix': float(times[i]) if np.isfinite(times[i]) else None,
                              'source_end_unix': float(times[end]) if np.isfinite(times[end]) else None,
                              'duration_s': float(duration) if np.isfinite(duration) and duration >= 0 else None})
        i = end
    if not spans:
        raise ValueError('nessun tratto osservato in movimento disponibile dopo la selezione del viaggio')
    source_duration = times[-1]-times[0]
    return spans, {'recording_gap_s': cfg.recording_gap_s, 'stop_min_duration_s': cfg.stop_min_duration_s,
                   'stop_radius_m': cfg.stop_radius_m, 'segment_count': len(spans),
                   'source_duration_s': float(source_duration) if np.isfinite(times).all() and (dt > 0).all() else None,
                   'observed_duration_s': float(sum(times[b-1]-times[a] for a, b in spans)),
                   'selection_source': 'timer_events' if timer_intervals is not None else 'gps_inference',
                   'pause_inference': inference,
                   'interruptions': interruptions}

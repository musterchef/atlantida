"""Confronto temporale fra selezione GPS e intervalli timer di riferimento."""
import numpy as np


def compare_pauses(raw, kept, timer_intervals, motion_valid, max_interval_s):
    """Misura separatamente movimento escluso e pause del timer conservate.

    Confronta solo intervalli GPS validi, entro la cadenza massima ammessa,
    interamente attivi o interamente in pausa secondo il timer. Le lacune
    e gli intervalli misti ai confini non diventano errori di riconoscimento.
    """
    times = np.asarray(raw['t_unix'], dtype=float)
    kept = np.asarray(kept, dtype=bool)
    valid = np.asarray(motion_valid, dtype=bool)
    bounds = np.asarray(timer_intervals, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or kept.shape != (len(times)-1,)
            or valid.shape != times.shape or bounds.ndim != 2 or bounds.shape[1:] != (2,)
            or not len(bounds) or not np.isfinite(bounds).all()
            or np.any(bounds[:, 1] <= bounds[:, 0]) or np.any(bounds[1:, 0] < bounds[:-1, 1])
            or not np.isfinite(max_interval_s) or max_interval_s <= 0):
        raise ValueError('campioni, selezione e intervalli timer allineati e validi richiesti')
    dt = np.diff(times)
    # Tempo attivo cumulato agli estremi: anche intervalli con più eventi
    # interni rimangono misurabili, senza arrotondare i confini ai campioni.
    duration = bounds[:, 1]-bounds[:, 0]
    prefix = np.r_[0., np.cumsum(duration)]
    index = np.searchsorted(bounds[:, 0], times, side='right')-1
    safe = np.maximum(index, 0)
    active_at = np.where(index < 0, 0., prefix[safe]+np.clip(times-bounds[safe, 0], 0, duration[safe]))
    overlap = np.diff(active_at)
    binary = np.isclose(overlap, 0, atol=1e-7, rtol=0) | np.isclose(overlap, dt, atol=1e-7, rtol=0)
    eligible = (np.isfinite(dt) & (dt > 0) & (dt <= max_interval_s) & valid[1:] & binary
                & (times[:-1] >= bounds[0, 0]) & (times[1:] <= bounds[-1, 1]))
    expected = overlap > 1e-7
    masks = {'matched_pause_s': ~expected & ~kept, 'extra_pause_s': expected & ~kept,
             'missed_pause_s': ~expected & kept, 'matched_active_s': expected & kept}
    metrics = {name: float(dt[eligible & mask].sum()) for name, mask in masks.items()}
    metrics['compared_s'] = sum(metrics.values())
    finite_intervals = np.isfinite(dt) & (dt > 0)
    metrics['not_compared_s'] = float(dt[finite_intervals & ~eligible].sum())
    differences = []
    i = 0
    while i < len(dt):
        if not eligible[i] or expected[i] == kept[i]:
            i += 1
            continue
        end = i+1
        while end < len(dt) and eligible[end] and expected[end] != kept[end] and kept[end] == kept[i]:
            end += 1
        differences.append({'start_unix': float(times[i]), 'end_unix': float(times[end]),
                            'start_source_index': int(raw['source_index'][i]),
                            'end_source_index': int(raw['source_index'][end]),
                            'duration_s': float(times[end]-times[i]),
                            'kind': 'missed_pause' if kept[i] else 'extra_pause'})
        i = end
    return {'metrics': metrics, 'differences': differences}

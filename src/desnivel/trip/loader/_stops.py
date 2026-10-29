"""Stima delle pause GPS, distinta dagli eventi timer e dalle lacune di segnale."""
import numpy as np

from ._geo import haversine_m, haversine_scalar


def infer_pauses(raw, continuous, cfg):
    """Riconosce campionamento interrotto a basso spostamento e soste prolungate.

    Una velocità bassa da sola non costituisce una pausa. La cadenza tipica
    è il quartile inferiore degli intervalli continui, meno influenzato
    dalle pause rispetto alla media degli intervalli.
    """
    times, lat, lon = (raw[name] for name in ('t_unix', 'lat', 'lon'))
    dt = np.diff(times)
    cadence = float(np.quantile(dt[continuous], .25)) if continuous.any() else None
    threshold = max(cfg.pause_min_gap_s, cadence*cfg.pause_gap_factor) if cadence is not None else None
    reasons = np.full(len(dt), '', dtype=object)
    if threshold is not None:
        distances = haversine_m(lat[:-1][continuous], lon[:-1][continuous],
                                 lat[1:][continuous], lon[1:][continuous])
        speed = np.full(len(dt), np.nan)
        speed[continuous] = distances/dt[continuous]*3.6
        reasons[continuous & (dt >= threshold) & (speed <= cfg.pause_max_speed_kmh)] = 'sampling_pause'
    anchor = 0
    for i in range(1, len(times)+1):
        inside = (i < len(times) and continuous[i-1]
                  and haversine_scalar(float(lat[anchor]), float(lon[anchor]),
                                       float(lat[i]), float(lon[i])) <= cfg.stop_radius_m)
        if inside:
            continue
        end = i-1
        if end > anchor and times[end]-times[anchor] >= cfg.stop_min_duration_s:
            reasons[anchor:end] = 'stationary'
        anchor = i
    return reasons, {'typical_sample_interval_s': cadence, 'pause_gap_threshold_s': threshold,
                     'pause_min_gap_s': cfg.pause_min_gap_s, 'pause_gap_factor': cfg.pause_gap_factor,
                     'pause_max_speed_kmh': cfg.pause_max_speed_kmh}

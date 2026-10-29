"""Geometria dei tratti osservati sullo stesso asse temporale della sessione."""
import numpy as np


def route_payload(track):
    """Conserva i confini dei segmenti, senza collegare le interruzioni."""
    if not track.n_samples:
        raise ValueError('traccia vuota per il visualizzatore')
    coordinates = np.column_stack((track.samples['lat'], track.samples['lon']))
    if (not np.all(np.isfinite(coordinates)) or np.any(np.abs(coordinates[:, 0]) > 90)
            or np.any(np.abs(coordinates[:, 1]) > 180)):
        raise ValueError('coordinate non valide per il visualizzatore')
    samples = np.column_stack((track.t-track.t[0], coordinates))
    spans = [(s.start, s.stop) for s in track.segments] or [(0, track.n_samples)]
    return {'version': 1, 'stage': track.stage_id,
            'segments': [samples[start:stop].tolist() for start, stop in spans]}

"""Analisi del profilo altimetrico, indipendente dalle decisioni musicali."""
from __future__ import annotations

from copy import deepcopy
import math

import numpy as np

from .track import Track


def _validate_config(config: dict) -> None:
    expected = {'sample_distance_m', 'slope_window_m', 'min_zone_distance_m', 'bands'}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError(f'campi richiesti per l’analisi: {sorted(expected)}')
    for name in expected - {'bands'}:
        value = config[name]
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'{name} deve essere positivo e finito')
    bands = config['bands']
    if not isinstance(bands, list) or not bands:
        raise ValueError('bands deve contenere almeno una fascia')
    names, previous = set(), -math.inf
    for i, band in enumerate(bands):
        if not isinstance(band, dict) or set(band) != {'name', 'from_slope_ratio'}:
            raise ValueError('ogni fascia richiede name e from_slope_ratio')
        name, lower = band['name'], band['from_slope_ratio']
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('nomi delle fasce non vuoti e distinti richiesti')
        names.add(name)
        if i == 0:
            if lower is not None:
                raise ValueError('la prima fascia deve partire da null (nessun limite inferiore)')
        else:
            if type(lower) not in (int, float) or not math.isfinite(lower) or lower <= previous:
                raise ValueError('soglie delle fasce finite e strettamente crescenti richieste')
            previous = lower


def _prepare_profile(track: Track) -> tuple[np.ndarray, np.ndarray]:
    """Valida quota/distanza e conserva l'ultima quota nelle soste."""
    channels = []
    for name in ('cum_dist_m', 'ele'):
        values = np.asarray(track.samples.get(name, []), dtype=float)
        if values.ndim != 1 or len(values) != track.n_samples or not np.isfinite(values).all():
            raise ValueError(f'canale {name} completo e finito richiesto')
        channels.append(values)
    distance, elevation = channels
    if len(distance) < 2 or np.any(distance[1:] < distance[:-1]) or distance[-1] <= distance[0]:
        raise ValueError('distanza cumulata crescente con estensione positiva richiesta')
    with np.errstate(over='ignore'):
        distance = distance - distance[0]
    if not np.isfinite(distance).all():
        raise ValueError('estensione del percorso non rappresentabile')
    increments = np.diff(distance)
    if np.any(increments == 0):
        keep = np.r_[increments > 0, True]
        distance, elevation = distance[keep], elevation[keep]
    return distance, elevation


def _zone_starts(observed: np.ndarray, edges: np.ndarray, minimum_m: float) -> np.ndarray:
    """Conferma le sequenze persistenti e scarta quelle della zona già attiva."""
    run_starts = np.r_[0, np.flatnonzero(observed[1:] != observed[:-1]) + 1]
    run_ends = np.r_[run_starts[1:], len(observed)]
    lengths = edges[run_ends] - edges[run_starts]
    # La prima osservazione inizializza la zona anche se il tratto è breve.
    confirmed = np.r_[0, run_starts[1:][lengths[1:] >= minimum_m]]
    labels = observed[confirmed]
    return confirmed[np.r_[True, labels[1:] != labels[:-1]]]


def analyze_track(track: Track, config: dict) -> dict:
    """Campiona per distanza, classifica la pendenza e conferma i cambi persistenti.

    La pendenza è la differenza di quota fra gli estremi di una finestra
    centrata su ciascun intervallo. Un cambio confermato viene riportato
    all'inizio della sequenza candidata: questa è un'analisi offline.
    """
    _validate_config(config)
    distance, elevation = _prepare_profile(track)
    total = float(distance[-1])
    step = config['sample_distance_m']
    regular_edges = np.array([0.]) if step >= total else np.arange(0., total, step)
    # Con passi decimali arange può includere per arrotondamento il termine
    # escluso. Aggiungere di nuovo total creerebbe un intervallo vuoto.
    if regular_edges[-1] >= total:
        regular_edges = regular_edges[:-1]
    edges = np.r_[regular_edges, total]
    widths = np.diff(edges)
    with np.errstate(over='ignore', invalid='ignore'):
        centers = (edges[:-1] + edges[1:]) / 2
        half = config['slope_window_m'] / 2
        left, right = np.maximum(0., centers-half), np.minimum(total, centers+half)
        spans = right - left
    if np.any(widths <= 0) or not np.isfinite(centers).all() or np.any(spans <= 0):
        raise ValueError('intervalli o finestre di pendenza non rappresentabili alla scala del percorso')
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        slopes = (np.interp(right, distance, elevation)-np.interp(left, distance, elevation))/spans
    if not np.isfinite(slopes).all():
        raise ValueError('pendenze non rappresentabili con i dati e la finestra forniti')

    # Confini e centri sono già ordinati: interlacciali, senza un ordinamento.
    # Una sola interpolazione fornisce quote per profilo, finestre e zone.
    profile_distances = np.empty(2*len(centers)+1)
    profile_distances[::2], profile_distances[1::2] = edges, centers
    profile_heights = np.interp(profile_distances, distance, elevation)
    edge_heights = profile_heights[::2]
    bands = config['bands']
    names = np.array([band['name'] for band in bands], dtype=object)
    observed = np.searchsorted([band['from_slope_ratio'] for band in bands[1:]], slopes, side='right')
    starts = _zone_starts(observed, edges, config['min_zone_distance_m'])
    ends = np.r_[starts[1:], len(observed)]
    labels = observed[starts]
    zone_indices = np.repeat(np.arange(len(starts)), ends-starts)
    matching = np.add.reduceat(np.where(observed == labels[zone_indices], widths, 0.), starts)
    with np.errstate(over='ignore', invalid='ignore'):
        gains = edge_heights[ends] - edge_heights[starts]
        mean_slopes = gains / (edges[ends] - edges[starts])
    if (not np.isfinite(gains).all() or not np.isfinite(profile_heights).all()
            or not np.isfinite(mean_slopes).all()):
        raise ValueError('quote, dislivelli o pendenze medie non rappresentabili')

    zones = []
    for number, (start, end, kind, gain, mean_slope, match) in enumerate(zip(
            starts.tolist(), ends.tolist(), names[labels].tolist(), gains.tolist(),
            mean_slopes.tolist(), matching.tolist())):
        start_m, end_m = float(edges[start]), float(edges[end])
        zones.append({'index': number, 'kind': kind,
                      'start_distance_m': start_m, 'end_distance_m': end_m,
                      'from_progress': start_m/total, 'until_progress': end_m/total,
                      'elevation_delta_m': gain, 'mean_slope_ratio': mean_slope,
                      'matching_distance_ratio': match/(end_m-start_m)})
    edge_values = edges.tolist()
    windows = [{'start_distance_m': start, 'end_distance_m': end, 'elevation_m': height,
                'slope_ratio': slope, 'observed_kind': kind, 'zone_index': zone}
               for start, end, height, slope, kind, zone in zip(
                   edge_values, edge_values[1:], profile_heights[1::2].tolist(),
                   slopes.tolist(), names[observed].tolist(), zone_indices.tolist())]
    profile = [{'distance_m': d, 'elevation_m': h}
               for d, h in zip(profile_distances.tolist(), profile_heights.tolist())]
    return {'version': 1, 'stage': track.stage_id, 'source_path': track.metadata.get('source_path'),
            'config': deepcopy(config), 'total_distance_m': total,
            'profile': profile, 'zones': zones, 'windows': windows}

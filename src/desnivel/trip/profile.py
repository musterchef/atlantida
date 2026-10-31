"""Descrittori neutri, pesati per distanza, del profilo analizzato."""
import math


def describe_profile(analysis, shape_points=8):
    if type(shape_points) is not int or not 2 <= shape_points <= 32:
        raise ValueError('shape_points deve essere un intero tra 2 e 32')
    total, windows = analysis['total_distance_m'], analysis['windows']
    if not math.isfinite(total) or total <= 0 or not windows:
        raise ValueError('profilo analizzato con distanza positiva richiesto')
    absolute = sum(abs(w['slope_ratio'])*(w['end_distance_m']-w['start_distance_m']) for w in windows)/total
    if not math.isfinite(absolute):
        raise ValueError('pendenza assoluta media non rappresentabile')
    levels = []
    for i in range(shape_points):
        low, high = i*total/shape_points, (i+1)*total/shape_points
        parts = [(max(0., min(high, w['end_distance_m'])-max(low, w['start_distance_m'])), w['elevation_m'])
                 for w in windows]
        distance = sum(length for length, _ in parts)
        if distance <= 0:
            raise ValueError('profilo senza copertura per un intervallo di distanza')
        levels.append(sum(length*height for length, height in parts)/distance)
    low, high = min(levels), max(levels)
    if not all(math.isfinite(value) for value in levels) or not math.isfinite(high-low):
        raise ValueError('forma altimetrica non rappresentabile')
    return {'total_distance_m': total, 'mean_absolute_slope_ratio': absolute,
            'shape_elevation_m': levels,
            'shape_normalized': [(value-low)/(high-low) for value in levels] if high > low else [.5]*shape_points}


def section_intensity(analysis, section):
    low, high = section['start_distance_m'], section['end_distance_m']
    return sum(abs(w['slope_ratio'])*max(0., min(high, w['end_distance_m'])-max(low, w['start_distance_m']))
               for w in analysis['windows'])/(high-low)

"""Selezione di tavolozze e contesti armonici da descrittori numerici."""
from copy import deepcopy
import math

from desnivel.music.patterns import SCALES


def pitch_classes(root, scale):
    return {(root+interval) % 12 for interval in SCALES[scale]}


def validate_palettes(palettes, switch_margin):
    if (type(switch_margin) not in (int, float) or not math.isfinite(switch_margin)
            or not 0 <= switch_margin <= 1):
        raise ValueError('switch_margin deve essere tra 0 e 1')
    if not isinstance(palettes, list) or not palettes:
        raise ValueError('palettes deve contenere almeno una tavolozza')
    previous, ids = -1., set()
    for palette in palettes:
        if not isinstance(palette, dict) or set(palette) != {'id', 'from_mean_absolute_slope_ratio', 'states'}:
            raise ValueError('tavolozza: richiesti id, from_mean_absolute_slope_ratio e states')
        threshold = palette['from_mean_absolute_slope_ratio']
        if (not isinstance(palette['id'], str) or not palette['id'] or palette['id'] in ids
                or type(threshold) not in (int, float) or not math.isfinite(threshold)
                or threshold < 0 or threshold <= previous):
            raise ValueError('tavolozze con id distinti e soglie crescenti non negative richieste')
        if not ids and threshold != 0:
            raise ValueError('la prima tavolozza deve partire da zero')
        ids.add(palette['id'])
        previous = threshold
        states = palette['states']
        if not isinstance(states, list) or not states:
            raise ValueError('states deve contenere almeno un contesto armonico')
        state_ids, intensities, classes = set(), set(), []
        for state in states:
            if not isinstance(state, dict) or set(state) != {'id', 'root', 'scale', 'intensity'}:
                raise ValueError('contesto della tavolozza: richiesti id, root, scale e intensity')
            validate_context(state)
            value = state['intensity']
            if (not isinstance(state['id'], str) or not state['id'] or state['id'] in state_ids
                    or type(value) not in (int, float) or not math.isfinite(value)
                    or not 0 <= value <= 1 or value in intensities):
                raise ValueError('contesti con id e intensità distinti in [0, 1] richiesti')
            state_ids.add(state['id'])
            intensities.add(value)
            classes.append(pitch_classes(state['root'], state['scale']))
        if any(len(a & b) < 3 for i, a in enumerate(classes) for b in classes[i+1:]):
            raise ValueError('i contesti di una tavolozza devono condividere almeno tre classi di altezza')


def validate_context(data):
    if 'root' in data and (type(data['root']) is not int or not 0 <= data['root'] <= 127):
        raise ValueError('root deve essere una nota MIDI intera tra 0 e 127')
    if 'scale' in data and (not isinstance(data['scale'], str) or data['scale'] not in SCALES):
        raise ValueError('scala sconosciuta')


def select_palette(palettes, mean_absolute_slope_ratio, override=None):
    if override is not None:
        choices = [p for p in palettes if p['id'] == override]
        if not choices:
            raise ValueError('override della tavolozza sconosciuto')
        return choices[0]
    return next(p for p in reversed(palettes) if mean_absolute_slope_ratio >= p['from_mean_absolute_slope_ratio'])


def choose_context(palette, target, previous, switch_margin):
    states = palette['states']
    def score(state):
        common = 1.
        if previous is not None:
            a, b = pitch_classes(previous['root'], previous['scale']), pitch_classes(state['root'], state['scale'])
            common = len(a & b)/max(len(a), len(b))
        return abs(state['intensity']-target)+.15*(1-common)
    selected = min(states, key=score)
    if previous is not None and score(previous)-score(selected) <= switch_margin:
        selected = previous
    return deepcopy(selected)

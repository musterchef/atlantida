"""Raggruppamento configurabile, conservazione del dettaglio e interruzioni."""
from copy import deepcopy

import numpy as np
import pytest

from desnivel.trip.analysis import analyze_track
from desnivel.trip.sections import group_zones
from desnivel.trip.track import Track


def analysis():
    slopes = [.04]*3 + [.08]*3 + [.04]*3 + [-.04]*3 + [.04]*3
    distance = np.arange(len(slopes)+1, dtype=float)*100
    track = Track('test', np.arange(len(distance), dtype=float),
                  {'cum_dist_m': distance, 'ele': 100+np.r_[0, np.cumsum(slopes)*100]})
    return analyze_track(track, {
        'sample_distance_m': 100, 'slope_window_m': 100, 'min_zone_distance_m': 200,
        'bands': [{'name': 'down', 'from_slope_ratio': None},
                  {'name': 'up', 'from_slope_ratio': .01},
                  {'name': 'steep_up', 'from_slope_ratio': .06}],
    })


FAMILIES = {'families': {'ascent': ['up', 'steep_up'], 'descent': ['down']}}


def test_same_family_merges_consecutive_zones_and_preserves_original_analysis():
    source = analysis()
    before = deepcopy(source)
    result = group_zones(source, FAMILIES)
    assert source == before
    assert [z['kind'] for z in source['zones']] == ['up', 'steep_up', 'up', 'down', 'up']
    sections = result['sections']
    assert [s['kind'] for s in sections] == ['ascent', 'descent', 'ascent']
    assert [s['zone_indices'] for s in sections] == [[0, 1, 2], [3], [4]]
    assert [s['start_distance_m'] for s in sections] == [0, 900, 1200]
    assert [s['end_distance_m'] for s in sections] == [900, 1200, 1500]
    assert sections[0]['elevation_delta_m'] == pytest.approx(48)
    assert sections[0]['mean_slope_ratio'] == pytest.approx(48/900)
    assert sections[0]['from_progress'] == 0
    assert sections[-1]['until_progress'] == 1
    assert [i for s in sections for i in s['zone_indices']] == list(range(5))


def test_family_membership_and_names_are_entirely_configurable():
    source = analysis()
    config = {'families': {'all_terrain': ['up', 'steep_up', 'down']}}
    result = group_zones(source, config)
    assert len(result['sections']) == 1
    assert result['sections'][0]['kind'] == 'all_terrain'
    assert result['sections'][0]['zone_indices'] == [0, 1, 2, 3, 4]
    config['families']['all_terrain'].clear()
    assert result['config']['families']['all_terrain'] == ['up', 'steep_up', 'down']


def test_separate_families_keep_each_zone_separate():
    source = analysis()
    result = group_zones(source, {'families': {band['name']: [band['name']]
                                             for band in source['config']['bands']}})
    assert len(result['sections']) == len(source['zones'])


def test_same_family_never_merges_across_a_distance_gap():
    source = analysis()
    source['zones'] = [source['zones'][0], source['zones'][2]]
    result = group_zones(source, FAMILIES)
    assert len(result['sections']) == 2


@pytest.mark.parametrize('config', [
    {}, {'families': {}}, {'families': []}, {'families': {'x': []}},
    {'families': {'': ['up', 'steep_up', 'down']}},
    {'families': {'x': 'up'}}, {'families': {'x': [False]}},
    {'families': {'x': ['up', 'up', 'down', 'steep_up']}},
    {'families': {'x': ['up', 'down'], 'y': ['up', 'steep_up']}},
    {'families': {'x': ['up', 'steep_up']}},
    {'families': {'x': ['up', 'steep_up', 'down', 'unknown']}},
    {**FAMILIES, 'tolerance_m': 200},
])
def test_invalid_or_incomplete_membership_is_rejected(config):
    with pytest.raises(ValueError):
        group_zones(analysis(), config)

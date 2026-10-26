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


def test_local_bridge_uses_both_flanks_symmetrically_without_changing_sections():
    from desnivel.trip.sections import measure_section_bridges

    def sections(lengths):
        cursor, result = 0, []
        for i, (kind, length) in enumerate(zip(['up', 'flat', 'up'], lengths)):
            result.append(dict(index=i, kind=kind, start_distance_m=cursor, end_distance_m=cursor+length))
            cursor += length
        return result

    source = sections([2000, 200, 300])
    original = deepcopy(source)
    first = measure_section_bridges(source, flank_kind='up', middle_kind='flat')['candidates'][0]
    reverse = measure_section_bridges(sections([300, 200, 2000]), flank_kind='up', middle_kind='flat')['candidates'][0]
    assert first['reference_distance_m'] == pytest.approx(2*2000*300/2300)
    assert first['distance_ratio'] == pytest.approx(200/first['reference_distance_m'])
    assert first['reference_distance_m'] == reverse['reference_distance_m']
    assert source == original
    assert [first[k] for k in ('before_index', 'middle_index', 'after_index')] == [0, 1, 2]
    # Anche le pianure molto lunghe sono mostrate per calibrare la futura soglia.
    long_flat = measure_section_bridges(sections([100, 1000, 100]), flank_kind='up', middle_kind='flat')
    assert long_flat['candidates'][0]['distance_ratio'] == 10


def test_local_bridge_requires_both_adjacent_flanks_and_leaves_edges_out():
    from desnivel.trip.sections import measure_section_bridges

    sections = [dict(index=i, kind=kind, start_distance_m=i*100, end_distance_m=(i+1)*100)
                for i, kind in enumerate(['flat', 'up', 'flat', 'down', 'flat', 'up', 'flat'])]
    assert not measure_section_bridges(sections, flank_kind='up', middle_kind='flat')['candidates']
    assert not measure_section_bridges([], flank_kind='up', middle_kind='flat')['candidates']
    with pytest.raises(ValueError):
        measure_section_bridges(sections, flank_kind='up', middle_kind='up')


def test_level_between_descents_uses_same_reference_and_excludes_mixed_flanks():
    from desnivel.trip.sections import measure_section_bridges

    sections = [dict(index=i, kind=kind, start_distance_m=start, end_distance_m=end)
                for i, (kind, start, end) in enumerate([
                    ('descent', 0, 2000), ('level', 2000, 2200), ('descent', 2200, 2500),
                    ('level', 2500, 2700), ('ascent', 2700, 3000)])]
    candidates = measure_section_bridges(sections, flank_kind='descent', middle_kind='level')['candidates']
    assert len(candidates) == 1
    assert candidates[0]['middle_index'] == 1
    assert candidates[0]['reference_distance_m'] == pytest.approx(2*2000*300/2300)
    assert candidates[0]['distance_ratio'] == pytest.approx(200/(2*2000*300/2300))

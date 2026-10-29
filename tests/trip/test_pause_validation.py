"""Misure temporali del confronto: errori distinti e campioni non confrontabili."""
from copy import deepcopy

import numpy as np
import pytest

from desnivel.cli.validate_pauses import attach_baseline
from desnivel.trip.pause_validation import compare_pauses


def test_false_and_missed_pauses_are_measured_independently_in_seconds():
    raw = dict(t_unix=np.array([0., 1., 2., 12., 13., 14.]), source_index=np.arange(1, 7))
    kept = [True, False, True, True, True]
    result = compare_pauses(raw, kept, [[0, 2], [12, 14]], np.ones(6, dtype=bool), 30)
    assert result['metrics'] == dict(matched_pause_s=0., extra_pause_s=1., missed_pause_s=10.,
                                     matched_active_s=3., compared_s=14., not_compared_s=0.)
    assert [d['kind'] for d in result['differences']] == ['extra_pause', 'missed_pause']


def test_recording_gaps_and_partial_timer_edges_are_not_called_pause_errors():
    raw = dict(t_unix=np.array([0., 2., 4., 6., 100.]), source_index=np.arange(1, 6))
    result = compare_pauses(raw, [False]*4, [[0, 1], [3, 6], [90, 100]], np.ones(5, dtype=bool), 30)
    assert result['metrics']['extra_pause_s'] == 2
    assert result['metrics']['compared_s'] == 2
    assert result['metrics']['not_compared_s'] == 98
    assert len(result['differences']) == 1


def test_invalid_motion_is_excluded_even_with_timer_running():
    raw = dict(t_unix=np.arange(3, dtype=float), source_index=np.arange(1, 4))
    result = compare_pauses(raw, [False, False], [[0, 2]], [True, False, True], 30)
    assert result['metrics']['extra_pause_s'] == 1
    assert result['metrics']['not_compared_s'] == 1


@pytest.mark.parametrize('bounds', [[], [[2, 1]], [[0, 3], [2, 4]], [[0, np.nan]]])
def test_invalid_reference_intervals_are_rejected(bounds):
    with pytest.raises(ValueError):
        compare_pauses(dict(t_unix=np.array([0., 1.])), [True], bounds, [True, True], 30)


def test_baseline_requires_same_source_files_and_comparable_duration():
    result = dict(version=1, config={}, stages=[dict(stage='one', gpx_sha256='g', fit_sha256='f',
                  metrics=dict(compared_s=100, extra_pause_s=2))], summary=dict(compared_s=100, extra_pause_s=2))
    previous = deepcopy(result)
    previous['stages'][0]['metrics']['extra_pause_s'] = 20
    attach_baseline(result, previous)
    assert result['baseline_summary']['extra_pause_s'] == 20
    previous['stages'][0]['gpx_sha256'] = 'changed'
    with pytest.raises(ValueError, match='differenti'):
        attach_baseline(result, previous)

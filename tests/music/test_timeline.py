"""Budget musicale, minimi, distribuzione del residuo e gestione del piano."""
from dataclasses import FrozenInstanceError
import json
import math
import random

import pytest

from desnivel.music.timeline import allocate_timeline, TimelineManager


def test_known_allocation_reserves_minima_before_distributing_distance_weights():
    timeline = allocate_timeline([9000, 1000, 4000], target_beats=240, window_beats=4)
    assert [s.window_count for s in timeline.spans] == [29, 11, 20]
    assert [s.start_window for s in timeline.spans] == [0, 29, 40]
    assert timeline.total_windows == 60 and timeline.total_beats == 240
    assert not timeline.extended_for_minimum
    assert not timeline.to_dict()['adjustments']


def test_insufficient_budget_is_extended_without_dropping_sections():
    timeline = allocate_timeline([100]*33, target_beats=240, window_beats=4)
    assert timeline.total_beats == 264
    assert timeline.extended_for_minimum
    assert all(s.window_count == 2 for s in timeline.spans)
    assert timeline.to_dict()['adjustments'] == [
        {'code': 'minimum_extension', 'from_beats': 240, 'to_beats': 264}]


def test_quantization_and_minimum_extension_are_distinct_and_total_is_exact():
    timeline = allocate_timeline([1, 1, 1], target_beats=17, window_beats=4)
    assert timeline.quantized_beats == 20
    assert timeline.total_beats == 24
    assert [a['code'] for a in timeline.to_dict()['adjustments']] == ['window_quantization', 'minimum_extension']
    quantized = allocate_timeline([1], target_beats=17, window_beats=4)
    assert quantized.total_beats == 20 and not quantized.extended_for_minimum


def test_zero_exponent_and_equal_remainders_preserve_source_order():
    timeline = allocate_timeline([1, 9000, 30], target_beats=28, window_beats=4,
                                 min_windows=1, distance_exponent=0)
    assert [s.window_count for s in timeline.spans] == [3, 2, 2]
    equal = allocate_timeline([1, 1, 1], target_beats=28, window_beats=4, min_windows=1)
    assert timeline.spans == equal.spans


def test_linear_distance_weights_and_extreme_distances_remain_finite():
    linear = allocate_timeline([1, 3], target_beats=24, window_beats=4,
                               min_windows=1, distance_exponent=1)
    assert [s.window_count for s in linear.spans] == [2, 4]
    extreme = allocate_timeline([1e-300, 1e300], target_beats=80, window_beats=4,
                                distance_exponent=1000)
    assert [s.window_count for s in extreme.spans] == [2, 18]
    json.dumps(extreme.to_dict(), allow_nan=False)


def test_random_allocations_keep_budget_minima_and_all_source_sections():
    rng = random.Random(17)
    for _ in range(100):
        distances = [rng.uniform(.1, 10000) for _ in range(rng.randint(1, 100))]
        target, window, minimum = rng.randint(1, 2000), rng.choice([1, 2, 4]), rng.randint(1, 5)
        plan = allocate_timeline(distances, target_beats=target, window_beats=window, min_windows=minimum)
        assert plan.total_windows == max(math.ceil(target/window), len(distances)*minimum)
        assert sum(s.window_count for s in plan.spans) == plan.total_windows
        assert [s.source_index for s in plan.spans] == list(range(len(distances)))
        assert all(s.window_count >= minimum for s in plan.spans)
        assert all(a.end_window == b.start_window for a, b in zip(plan.spans, plan.spans[1:]))


@pytest.mark.parametrize('distances, changes', [
    ([], {}), ([0], {}), ([-1], {}), ([float('inf')], {}), ([True], {}),
    ([1], {'target_beats': 0}), ([1], {'target_beats': float('nan')}),
    ([1], {'window_beats': 0}), ([1], {'min_windows': 1.5}), ([1], {'min_windows': False}),
    ([1], {'min_windows': 0}), ([1], {'distance_exponent': -1}),
    ([1], {'distance_exponent': float('nan')}),
])
def test_invalid_inputs_are_rejected(distances, changes):
    with pytest.raises(ValueError):
        allocate_timeline(distances, **{'target_beats': 480, 'window_beats': 4, **changes})


def test_manager_consumes_every_window_in_order_and_has_explicit_end_and_reset():
    timeline = allocate_timeline([9, 1, 4], target_beats=40, window_beats=4)
    manager = TimelineManager(timeline)
    observed = []
    while not manager.finished:
        observed.append(manager.current_span.source_index)
        assert manager.snapshot()['remaining_windows'] >= 1
        manager.advance()
    assert observed == [s.source_index for s in timeline.spans for _ in range(s.window_count)]
    assert manager.current_span is None
    assert manager.snapshot() == {'window_index': 10, 'beat': 40, 'source_index': None,
                                  'remaining_windows': 0, 'finished': True}
    with pytest.raises(ValueError):
        manager.advance()
    manager.reset()
    assert manager.window_index == 0 and manager.current_span.source_index == 0


def test_manager_seek_uses_exclusive_end_boundaries_and_independent_cursors():
    timeline = allocate_timeline([1, 1], target_beats=16, window_beats=4)
    manager, other = TimelineManager(timeline), TimelineManager(timeline)
    manager.seek_window(timeline.spans[0].end_window)
    assert manager.current_span.source_index == 1
    assert other.current_span.source_index == 0
    manager.seek_window(timeline.total_windows)
    assert manager.finished
    for invalid in [-1, 1.5, timeline.total_windows+1]:
        with pytest.raises(ValueError):
            manager.seek_window(invalid)
    with pytest.raises(FrozenInstanceError):
        timeline.spans[0].window_count = 100
    with pytest.raises(AttributeError):
        manager.timeline = other.timeline

import json
from pathlib import Path

import pytest

from desnivel.music import Pattern, ThresholdRule, rule_from_dict, scale_notes
from desnivel.trip_metrics import MetricName, MetricSample
from desnivel.adapters.snake import pattern_messages


def test_hysteresis_missing_values_and_rearming():
    low = Pattern((33,), (1,))
    high = Pattern((40,), (1,))
    rule = ThresholdRule(MetricName.ELEVATION_M, 200, 15, low, high)
    values = [190, 201, 214, 215, 200, float('nan'), 185, 184, 215]
    changes = [c for i, value in enumerate(values)
               if (c := rule.update(MetricSample(i, MetricName.ELEVATION_M, value))) is not None]
    assert [(c.elapsed_s, c.state) for c in changes] == [(0, 'low'), (3, 'high'), (7, 'low'), (8, 'high')]
    assert changes[1].pattern == high
    assert rule.update(MetricSample(10, MetricName.SPEED_KMH, 0)) is None


def test_initial_state_above_threshold():
    pattern = Pattern((33,), (1,))
    rule = ThresholdRule(MetricName.ELEVATION_M, 200, 15, pattern, pattern)
    assert rule.update(MetricSample(0, MetricName.ELEVATION_M, 205)).state == 'high'


def test_scale_is_independent_of_device_range():
    assert scale_notes('pentatonic_minor', 33, 6) == [33, 36, 38, 40, 43, 45]
    assert scale_notes('major', 80, 4) == [80, 82, 84, 85]
    with pytest.raises(ValueError):
        pattern_messages(Pattern((90,) * 16, (1,) * 16))


def test_preset_and_adapter():
    rule = rule_from_dict(json.loads(Path('presets/quota.json').read_text()))
    assert sum(rule.low.gates) == 4
    assert sum(rule.high.gates) == 8
    assert set(n % 12 for n in rule.high.notes) <= {9, 0, 2, 4, 7}
    messages = pattern_messages(rule.high)
    assert len(messages) == 33
    assert ('Scales', 0.0) in messages
    with pytest.raises(ValueError):
        pattern_messages(Pattern((33,), (1,)))

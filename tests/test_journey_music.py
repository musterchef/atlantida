import copy
import json
from pathlib import Path

import pytest

from desnivel.journey_music import compose
from desnivel.trip_metrics import MetricName as M, MetricSample as S


def config():
    c = json.loads(Path('presets/tappe/levanto_la_spezia.json').read_text())
    c.update(update_s=1, smoothing_s=1)
    return c


def samples():
    return [S(t, name, value) for t in range(11) for name, value in
            [(M.DISTANCE_TOTAL_M, t * 10), (M.SPEED_KMH, 30), (M.EFFORT_ESTIMATE, 0)]]


def test_weights_and_repeatability():
    c = config()
    movement = compose(samples(), c, dict(movement=1, effort=0))
    effort = compose(samples(), c, dict(movement=0, effort=1))
    mixed = compose(samples(), c, dict(movement=.6, effort=.4))
    assert sum(movement[0].pattern.gates) == 10
    assert sum(effort[0].pattern.gates) == 3
    assert sum(mixed[0].pattern.gates) == 7
    assert all(a <= b for a, b in zip(effort[0].pattern.gates, movement[0].pattern.gates))
    assert mixed == compose(samples(), c, dict(movement=6, effort=4))


def test_sections_preserve_motif_and_return():
    changes = compose(samples(), config(), dict(movement=1, effort=0))
    assert [c.elapsed_s for c in changes] == [0, 3, 8]
    before, during, after = [c.pattern.notes for c in changes]
    assert before == after
    assert [i for i in range(16) if before[i] != during[i]] == [6, 14]
    assert during[6] % 12 == 11  # Si
    assert during[14] % 12 == 5  # Fa


def test_missing_active_input_holds_and_new_replay_resets():
    data = [s for s in samples() if s.name != M.EFFORT_ESTIMATE]
    assert compose(data, config(), dict(movement=0, effort=1)) == []
    assert compose(data, config(), dict(movement=1, effort=0))
    stale = [s for s in samples() if s.name != M.SPEED_KMH or s.elapsed_s == 0]
    changes = compose(stale, config(), dict(movement=1, effort=0))
    assert [c.elapsed_s for c in changes] == [0, 3]  # niente cambio con velocità scaduta
    assert compose(data, config(), dict(movement=1, effort=0))[0].elapsed_s == 0


def test_invalid_configuration():
    with pytest.raises(ValueError):
        compose(samples(), config(), dict(movement=0, effort=0))
    c = copy.deepcopy(config())
    c['gate_priority'][1] = 0
    with pytest.raises(ValueError):
        compose(samples(), c, dict(movement=1, effort=0))


def test_identical_patterns_still_emit_section_entry():
    c = config()
    for section in c['sections']:
        section['scale'] = 'pentatonic_minor'
        section.pop('degree_overrides', None)
    changes = compose(samples(), c, dict(movement=1, effort=0))
    assert [x.section_index for x in changes] == [0, 1, 2]
    assert changes[0].pattern == changes[1].pattern


def test_snake_shape_only_on_section_entry():
    import random
    from desnivel.music import Pattern, PatternChange
    from desnivel.adapters.snake import section_pattern_messages
    p = Pattern((33,) * 16, (1,) * 16)
    changes = [PatternChange(i, 'state', p, section) for i, section in enumerate([0, 0, 1, 1, 2])]
    result = list(section_pattern_messages(changes, random.Random(7)))
    shapes = [(c.elapsed_s, value) for c, messages in result for name, value in messages if name == 'gate_shape']
    assert [t for t, _ in shapes] == [0, 2, 4]
    assert all(0 <= v <= 13 and int(v) == v for _, v in shapes)
    assert result == list(section_pattern_messages(changes, random.Random(7)))

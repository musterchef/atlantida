import random

import pytest

from desnivel.adapters import snake


def test_param_name():
    assert snake.param_name("Gate", 1) == "Gate_01"
    assert snake.param_name("Note", 16) == "Note_16"
    with pytest.raises(ValueError):
        snake.param_name("Gate", 17)


def test_parse_gate_pattern_accepts_separators():
    assert snake.parse_gate_pattern("1000 0100 0010 0001") == snake.parse_gate_pattern(
        "1000/0100/0010/0001"
    )
    with pytest.raises(ValueError):
        snake.parse_gate_pattern("101")
    with pytest.raises(ValueError):
        snake.parse_gate_pattern("2" * 16)


def test_random_gates_reproducible_and_bounds():
    a = snake.random_gates(0.5, random.Random(1))
    assert a == snake.random_gates(0.5, random.Random(1))
    assert snake.random_gates(0, random.Random()) == [0] * 16
    assert snake.random_gates(1, random.Random()) == [1] * 16


def test_scale_notes_wrap_octave_and_clamp():
    assert snake.scale_notes("major", 36, 8) == [36, 38, 40, 41, 43, 45, 47, 48]
    assert max(snake.scale_notes("chromatic", 80)) == snake.NOTE_MAX
    with pytest.raises(ValueError):
        snake.scale_notes("nope", 0)


def test_messages_names():
    assert snake.gate_messages([1] * 16)[4] == ("Gate_05", 1.0)
    msgs = snake.note_messages(list(range(16)))
    assert msgs[0] == ("Scales", 0.0)
    assert msgs[3] == ("Note_03", 2.0)

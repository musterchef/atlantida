from dataclasses import replace
import pytest
from desnivel.adapters.snake_sequence import Lane, SHAPES, SnakeState, predict


def state(**changes):
    lane = Lane(1,'16n',16,'forwards',0)
    base = SnakeState(tuple(range(40,56)), (1,)*16, (64,)*16, (100,)*16,
                      lane,lane,lane,120,0)
    return replace(base, **changes)


def test_shapes_and_independent_clocks():
    assert all(sorted(s) == list(range(16)) for s in SHAPES)
    melody = predict(state(notes_lane=Lane(3,'8n',4,'forwards',0)), 2)
    assert [n.pitch for n in melody.notes] == [40,40,44,44,48,48,52,52]
    assert [n.beat for n in melody.notes] == [0,.25,.5,.75,1,1.25,1.5,1.75]


def test_closed_gates_consume_time_and_length_follows_notes():
    melody = predict(state(gates=(0,1)+(0,)*14, lengths_ms=(100,250)+(100,)*14), 1)
    assert len(melody.notes) == 1
    assert melody.notes[0].beat == .25
    assert melody.notes[0].pitch == 41
    assert melody.notes[0].duration == .5


def test_phase_and_reverse_are_explicit():
    lane = Lane(1,'16n',4,'backwards',.25)
    assert [lane.cell_at(t) for t in [0,.25,.5,.75]] == [2,1,0,3]
    melody = predict(state(gates_lane=Lane(1,'16n',16,'forwards',.125)), 1)
    assert [n.beat for n in melody.notes] == [.125,.375,.625,.875]


def test_retriggers_close_previous_note_and_window_clips_tail():
    melody = predict(state(notes=(40,)*16, lengths_ms=(1000,)*16), 1)
    assert [n.duration for n in melody.notes] == [.25]*4
    assert predict(state(velocities=(0,)*16),1).notes == ()


def test_unknown_behavior_is_rejected():
    with pytest.raises(ValueError, match='direzione'):
        Lane(1,'16n',16,'random',0)
    with pytest.raises(ValueError, match='swing'):
        state(swing=.2)


def test_exported_phases_do_not_delay_simultaneous_lane_steps():
    # Stesso istante esportato dopo modulo su cicli differenti (2.5 e 4 beat).
    melody = predict(state(
        notes_lane=Lane(3, '8n', 5, 'backwards', .9559032501910809),
        gates_lane=Lane(1, '16n', 16, 'forwards', 3.455903250191081),
    ), 1)
    assert [n.pitch for n in melody.notes] == [48, 48, 44, 44]


def test_boundary_tolerance_preserves_real_before_and_after_positions():
    lane = Lane(1, '16n', 16, 'forwards', 0)
    assert lane.cell_at(.25 - 1e-7) == 0
    assert lane.cell_at(.25) == 1
    assert lane.cell_at(.25 + 1e-7) == 1

import pytest

from desnivel.music.coordinator import PlanningRequest
from desnivel.music.director import MusicalContext
from desnivel.music.melodic.generator import MotifGenerator


def request(role='melody', start=0, **parameters):
    return PlanningRequest(start, 4, MusicalContext(0, 'test', 60, 'major'), {}, role, parameters)


def test_melody_continues_motif_and_texture_sustains_one_note():
    generator = MotifGenerator([0, 2, 4, 1, 3, 2])
    assert [n.pitch for n in generator(request()).notes] == [60, 64, 67, 62]
    assert [n.pitch for n in generator(request(start=4)).notes] == [65, 64, 60, 64]
    held = generator(request('sustained_texture'))
    assert len(held.notes) == 1 and held.notes[0].duration == 4
    low = generator(request('bass_line', octave=-2))
    assert [n.pitch for n in low.notes] == [36, 40, 43, 38]


def test_no_silent_unknown_controls_or_out_of_range_notes():
    generator = MotifGenerator([0, 7])
    with pytest.raises(ValueError):
        generator(request(unknown=1))
    with pytest.raises(ValueError):
        generator(request(octave=5))


def test_development_retains_identity_builds_period_and_is_reproducible():
    settings = dict(development=.7, activity=.75, phrase_windows=4, seed=7)
    a = MotifGenerator([0, 2, 4, 1, 3, 2, 1, 0], settings)
    b = MotifGenerator([0, 2, 4, 1, 3, 2, 1, 0], settings)
    phrases, phases = [], []
    for i in range(24):
        req = request(start=4+i*4)
        phrase = a(req)
        assert phrase == b(req)
        phrases.append(phrase)
        phases.append(a.last_decision['phase'])
        if i % 4 == 0:
            assert [n.pitch for n in phrase.notes[:3]] == [60, 64, 67]
        if i % 4 == 3:
            assert phrase.notes[-1].pitch == 60
            assert phrase.notes[-1].duration >= 1
    assert phases[:4] == ['statement', 'development', 'contrast', 'resolution']
    assert len({tuple(n.pitch for n in p.notes) for p in phrases}) > 8
    assert len({tuple(n.beat for n in p.notes) for p in phrases}) > 8
    pitches = [n.pitch for p in phrases for n in p.notes]
    assert max(abs(x-y) for x,y in zip(pitches,pitches[1:])) <= 7
    assert all(n.pitch % 12 in (0,2,4,5,7,9,11) for p in phrases for n in p.notes)
    assert len({n.velocity for p in phrases for n in p.notes}) > 3
    assert any(sum(n.duration for n in p.notes) < 3 for p in phrases)


def test_restart_begins_statement_and_seed_changes_development():
    a = MotifGenerator([0, 2, 4, 1], dict(development=.8, seed=1))
    first = a(request(start=100))
    assert a.last_decision['phase'] == 'statement'
    a(request(start=104))
    a.reset()
    assert a(request(start=4)) == first
    b = MotifGenerator([0, 2, 4, 1], dict(development=.8, seed=2))
    assert b(request(start=4)) != first


def test_development_expresses_scale_colour_and_literal_mode_is_unchanged():
    from desnivel.music.coordinator import PlanningRequest
    minor = MotifGenerator([0,2,4,1,3,2,1,0], dict(development=.7, seed=7))
    dorian = MotifGenerator([0,2,4,1,3,2,1,0], dict(development=.7, seed=7))
    minor_notes, dorian_notes = [], []
    for i in range(16):
        base = request(start=i*4)
        minor_notes += list(minor(PlanningRequest(base.start,4,MusicalContext(0,'test',60,'minor'),{},'melody',{})).notes)
        dorian_notes += list(dorian(PlanningRequest(base.start,4,MusicalContext(0,'test',60,'dorian'),{},'melody',{})).notes)
    assert any(n.pitch % 12 == 8 for n in minor_notes)
    assert any(n.pitch % 12 == 9 for n in dorian_notes)
    assert [n.pitch for n in minor_notes] != [n.pitch for n in dorian_notes]
    literal = MotifGenerator([0,2,4,1])
    assert literal(request(start=0)) == literal(request(start=4))

from dataclasses import asdict

import pytest

from desnivel.music.director import MusicDirector
from desnivel.music.coordinator import MusicCoordinator, Voice
from desnivel.music.bass.planner import BassPlanner
from desnivel.music.bass.generator import BassSettings, generate_bass
from desnivel.music.phrases import Note, Phrase


def test_context_changes_at_section_boundary_without_changing_notes():
    director = MusicDirector([
        dict(from_progress=0, name='inizio', root=48, scale='major'),
        dict(from_progress=.5, name='seguito', root=50, scale='dorian'),
    ])
    assert director.context_at(.499).section_index == 0
    assert asdict(director.context_at(.5)) == dict(
        section_index=1, name='seguito', root=50, scale='dorian')
    assert director.context_at(1) == director.context_at(.5)
    with pytest.raises(ValueError):
        director.context_at(float('nan'))


def test_coordinator_uses_preceding_phrase_and_reset_removes_continuity():
    melody = Phrase(4, (Note(0, 60, 1, 90), Note(2, 67, 1, 90)))
    coordinator = BassPlanner()
    first = coordinator.plan(melody, 0)
    expected = generate_bass(melody, coordinator.settings, first.notes[-1].pitch, phrase_index=1)
    assert coordinator.plan(melody, 4) == expected
    coordinator.reset()
    assert coordinator.plan(melody, 4) == generate_bass(melody, coordinator.settings, phrase_index=1)


def test_transition_survives_new_sequence_without_using_old_beats():
    melody = Phrase(4, (Note(0, 60, 1, 90),))
    coordinator = BassPlanner(BassSettings(density=.5))
    coordinator.plan(melody, 20)
    coordinator.set_settings(BassSettings(density=1.5), 2)
    coordinator.plan(melody, 24)
    assert coordinator.settings.density == 1
    coordinator.reset()
    coordinator.plan(melody, 0)
    assert coordinator.settings.density == 1
    coordinator.plan(melody, 4)
    assert coordinator.settings.density == 1.25


def test_coordinator_orders_independent_voices_and_passes_common_context():
    context = MusicDirector([dict(from_progress=0, name='sezione', root=48, scale='major')]).context_at(0)
    phrase = Phrase(4, (Note(0, 60, 1, 90),))
    calls = []

    def generate(name):
        def run(request):
            calls.append((name, request))
            return phrase
        return run

    coordinator = MusicCoordinator({
        'c': Voice(generate('c'), ('a', 'b')),
        'b': Voice(generate('b')),
        'a': Voice(generate('a')),
    })
    assert coordinator.plan(8, 4, context) == dict(a=phrase, b=phrase, c=phrase)
    assert [name for name, _ in calls] == ['b', 'a', 'c']
    assert all(r.context is context and r.start == 8 for _, r in calls)
    assert dict(calls[-1][1].dependencies) == dict(a=phrase, b=phrase)
    assert not calls[0][1].dependencies


@pytest.mark.parametrize('voices', [
    {'a': Voice(lambda r: None, ('missing',))},
    {'a': Voice(lambda r: None, ('b',)), 'b': Voice(lambda r: None, ('a',))},
])
def test_invalid_dependencies_rejected_before_generating(voices):
    with pytest.raises(ValueError, match='dipendenze'):
        MusicCoordinator(voices).plan(0, 4)

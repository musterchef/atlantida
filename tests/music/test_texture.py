from dataclasses import replace

import pytest

from desnivel.cli.generators import build_generator
from desnivel.music.coordinator import PlanningRequest
from desnivel.music.director import MusicalContext
from desnivel.music.phrases import Note, Phrase
from desnivel.music.texture.generator import TextureGenerator


def request(start=0, notes=(), **parameters):
    return PlanningRequest(start, 4, MusicalContext(0, 'section', 60, 'major'),
                           {'melody': Phrase(4, tuple(notes))}, 'sustained_texture', parameters)


def test_independent_texture_uses_section_degree_register_and_velocity():
    generator = TextureGenerator(2)
    phrase = generator(request(octave=1, velocity=45))
    assert phrase == Phrase(4, (Note(0, 76, 4, 45),))
    minor = replace(request(), context=MusicalContext(1, 'minor', 62, 'minor'))
    assert generator(minor).notes[0].pitch == 65
    assert generator(replace(request(), dependencies={})).notes


def test_follow_source_uses_salience_and_continuity_and_replanning_is_stable():
    generator = TextureGenerator(settings={'follow_source': 1})
    first = request(notes=(Note(0, 60, .1, 80), Note(1, 67, 3, 100)))
    assert generator(first).notes[0].pitch == 67
    equal = request(start=4, notes=(Note(0, 60, 1, 90), Note(1, 67, 1, 90)))
    held = generator(equal)
    assert held.notes[0].pitch == 67
    assert generator(equal) == held
    assert generator.last_decision['source'] == 'melody'
    assert generator.last_decision['register'] == [60, 71]
    generator.reset()
    assert generator(equal).notes[0].pitch == 60
    generator(first)
    assert generator(replace(equal, start=20)).notes[0].pitch == 60


def test_switch_keeps_independent_mode_available_and_follows_source_silence():
    generator = TextureGenerator()
    source = request(notes=(Note(0, 67, 4, 100),))
    assert generator(source).notes[0].pitch == 60
    assert generator(replace(source, parameters={'follow_source': 1})).notes[0].pitch == 67
    assert not generator(request(4, follow_source=1)).notes
    assert generator.last_decision['silence_reason'] == 'source_silent'
    assert generator(request(8)).notes[0].pitch == 60
    assert not generator(replace(request(12, follow_source=1), dependencies={})).notes
    assert generator.last_decision['silence_reason'] == 'source_unavailable'


def test_follow_source_respects_register_and_reports_incompatible_inputs():
    generator = TextureGenerator()
    phrase = generator(request(notes=(Note(0, 48, 4, 90),), octave=1, follow_source=1))
    assert phrase.notes[0].pitch == 72
    with pytest.raises(ValueError, match='una sola sorgente'):
        generator(replace(request(follow_source=1), dependencies={'a': Phrase(4, ()), 'b': Phrase(4, ())}))
    with pytest.raises(ValueError, match='nessuna altezza sorgente'):
        generator(replace(request(notes=(Note(0, 60, 4, 90),), follow_source=1),
                          context=MusicalContext(0, 'high', 126, 'major')))
    with pytest.raises(ValueError, match='registro MIDI'):
        generator(replace(request(octave=5), context=MusicalContext(0, 'high', 72, 'major')))


@pytest.mark.parametrize('parameters', [{'follow_source': .5}, {'follow_source': True},
                                        {'follow_source': 2}, {'velocity': 0}, {'octave': 1.5},
                                        {'activity': .5}])
def test_invalid_parameters_are_rejected(parameters):
    with pytest.raises(ValueError):
        TextureGenerator().validate('sustained_texture', parameters)


def test_texture_registration_exposes_only_its_controls_and_saves_mode_in_presets():
    registered = build_generator({'type': 'sustained_texture', 'settings': {'octave': 1},
                                  'presets': {'coordinated': {'follow_source': 1}}})
    assert set(registered.controls) == {'octave', 'velocity', 'follow_source'}
    assert registered.controls['follow_source'].toggle
    assert registered.presets['coordinated'] == {'octave': 1, 'velocity': 85, 'follow_source': 1}

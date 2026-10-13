import pytest

from desnivel.bass import BassSettings, generate_bass
from desnivel.phrases import Note, Phrase
from desnivel.cli.compose_bass import main


def test_bass_preserves_attacks_classes_and_silence():
    melody = Phrase(4, (Note(0,60,.5,100), Note(.25,67,.25,80), Note(2,62,1,90)))
    bass = generate_bass(melody, BassSettings(strategy="follow"))
    assert [n.beat for n in bass.notes] == [0,2]
    assert [n.pitch % 12 for n in bass.notes] == [0,2]
    assert bass.notes[0].beat+bass.notes[0].duration < 2
    assert all(28 <= n.pitch <= 47 for n in bass.notes)
    assert generate_bass(Phrase(4,())).notes == ()


def test_density_register_and_continuity_are_configurable():
    melody = Phrase(2, (Note(0,60,1,100), Note(.5,62,1,100)))
    bass = generate_bass(melody, BassSettings(36,59,.25,1,1,strategy="follow"), previous_pitch=50)
    assert [n.pitch for n in bass.notes] == [48,50]
    assert bass.notes[0].duration == .5
    assert bass.notes[1].velocity == 100


def test_cli_generates_readable_phrase_and_refuses_overwrite(tmp_path):
    source = tmp_path/'melody.json'
    source.write_text('{"length_beats":4,"notes":[{"beat":0,"pitch":60,"duration":1,"velocity":90}]}')
    output = tmp_path/'bass.json'
    assert main(['--melody',str(source),'--output',str(output)]) == 0
    import json
    bass = Phrase.from_dict(json.loads(output.read_text()))
    assert bass.notes[0].pitch % 12 == 0
    with pytest.raises(SystemExit):
        main(['--melody',str(source),'--output',str(output)])


def test_responsive_varies_phrases_but_is_repeatable():
    melody=Phrase(4,tuple(Note(i*.5,[60,64,67,62][i%4],.2,100) for i in range(8)))
    phrases=[generate_bass(melody,phrase_index=i) for i in range(4)]
    assert len(set(p.notes for p in phrases))>1
    assert phrases[2]==generate_bass(melody,phrase_index=2)
    assert phrases[0]==generate_bass(melody,phrase_index=4)
    assert any(n.duration>.2 for p in phrases for n in p.notes)
    for p in phrases:
        assert all(n.pitch%12 in {0,2,4,7} and 28<=n.pitch<=47 for n in p.notes)
        assert all(a.beat+a.duration<=b.beat for a,b in zip(p.notes,p.notes[1:]))
        assert all(n.beat+n.duration<=4 for n in p.notes)


def test_responsive_handles_silence_and_single_note_without_inventing_harmony():
    assert generate_bass(Phrase(4,())).notes==()
    melody=Phrase(4,(Note(1,61,.1,70),))
    bass=generate_bass(melody)
    assert bass.notes[0].beat==1
    assert all(n.pitch%12==1 for n in bass.notes)


def test_responsive_density_and_dynamics_are_controls():
    melody=Phrase(4,tuple(Note(i*.25,60+i%5,.2,100) for i in range(16)))
    sparse=generate_bass(melody,BassSettings(min_spacing=2))
    dense=generate_bass(melody,BassSettings(min_spacing=.5))
    assert len(dense.notes)>len(sparse.notes)
    assert len({n.velocity for n in dense.notes})>1


def test_slap_adds_syncopation_and_octave_pop_notes():
    melody = Phrase(4, tuple(
        Note(beat, pitch, .2, 100)
        for beat, pitch in zip((0, .5, 1, 1.5, 2, 2.5, 3, 3.5),
                               (60, 64, 67, 62, 60, 64, 67, 62))
    ))
    settings = BassSettings(highest=59, strategy='slap')
    bass = generate_bass(melody, settings)
    responsive = generate_bass(melody, BassSettings(highest=59))

    assert [note.beat for note in bass.notes] == [i * .5 for i in range(8)]
    assert len(bass.notes) > len(responsive.notes)
    assert all(28 <= note.pitch <= 59 for note in bass.notes)
    assert all(note.pitch % 12 in {0, 2, 4, 7} for note in bass.notes)
    assert all(note.duration < .5 for note in bass.notes)

    repeated = Phrase(4, tuple(Note(i * .5, 60, .2, 100) for i in range(8)))
    octave_bass = generate_bass(repeated, settings)
    assert all(high.pitch - low.pitch == 12
               for low, high in zip(octave_bass.notes[::2], octave_bass.notes[1::2]))


def test_slap_varies_groove_repeats_and_preserves_silence():
    melody = Phrase(4, tuple(Note(i * .5, 60 + i % 3, .2, 90) for i in range(8)))
    settings = BassSettings(highest=59, strategy='slap')
    first = generate_bass(melody, settings, phrase_index=0)
    second = generate_bass(melody, settings, phrase_index=1)

    assert first == generate_bass(melody, settings, phrase_index=4)
    assert [n.beat for n in first.notes] != [n.beat for n in second.notes]
    assert generate_bass(Phrase(4, ()), settings).notes == ()

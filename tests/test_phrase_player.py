import pytest
from desnivel.phrases import Note, Phrase
from desnivel.adapters.phrase_player import encode
from desnivel.cli.send_phrase import main


def test_encoding():
    p = Phrase(8, (Note(4, 40, 2, 90), Note(0, 33, 3, 80)))
    address, args = encode(p, 'bass')
    assert address == '/desnivel/v1/player/bass/phrase'
    assert args == [1, 8., 2, 0., 33, 3., 80, 4., 40, 2., 90]


@pytest.mark.parametrize('note', [(0, 128, 1, 80), (0, 33, 0, 80), (float('nan'), 33, 1, 80), (0, 33, 1, 0)])
def test_invalid_note(note):
    with pytest.raises(ValueError):
        Note(*note)


def test_player_limits_and_empty_phrase():
    with pytest.raises(ValueError):
        Phrase(1, (Note(0, 33, 2, 80),))
    with pytest.raises(ValueError):
        encode(Phrase(4, (Note(0, 33, 2, 80), Note(1, 33, 1, 80))), 'bass')
    assert encode(Phrase(4, ()), 'bass')[1] == [1, 4., 0]
    assert main(['--phrase', 'presets/phrases/bass_sustained.json', '--voice', 'bass', '--dry-run']) == 0

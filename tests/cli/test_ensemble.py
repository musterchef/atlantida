import json

import pytest

from desnivel.cli.ensemble import EnsembleSession, Generator
from desnivel.music.bass.generator import generate_bass, BassSettings
from desnivel.music.phrases import Note, Phrase


def config():
    # Passaggio JSON: nessun oggetto Python incorporato nella configurazione.
    return json.loads('''{
      "selection_mode": "manual",
      "voices": {
        "a": {"generator": "source", "destination": "out_a"},
        "b": {"generator": "accompaniment", "destination": "out_b", "dependencies": ["a"]}
      },
      "sections": [
        {"name": "opening", "from_progress": 0, "root": 60, "scale": "major",
         "assignments": {"a": {"role": "melody", "parameters": {"velocity": 70}}}},
        {"name": "development", "from_progress": 0.5, "root": 62, "scale": "minor",
         "assignments": {"a": {"role": "melody", "parameters": {"velocity": 100}},
                         "b": {"role": "bass_line", "parameters": {"density": 0.5}}}}
      ]
    }''')


def setup(data=None):
    calls, sent = [], []

    def source(request):
        calls.append(('a', request))
        return Phrase(request.length_beats, (
            Note(0, request.context.root, 1, request.parameters['velocity']),))

    def accompaniment(request):
        calls.append(('b', request))
        return generate_bass(request.dependencies['a'], BassSettings(**request.parameters))

    generators = {
        'source': Generator(source, ('melody',)),
        'accompaniment': Generator(accompaniment, ('bass_line',)),
    }
    destinations = {
        'out_a': lambda start, phrase: sent.append(('a', start, phrase)),
        'out_b': lambda start, phrase: sent.append(('b', start, phrase)),
    }
    return EnsembleSession(data or config(), generators, destinations), calls, sent


def test_sections_change_active_voices_context_and_parameters_and_route_results():
    session, calls, sent = setup()
    opening = session.plan(0, 0, 4)
    assert set(opening) == {'a'}
    assert opening['a'].notes[0] == Note(0, 60, 1, 70)
    assert not sent
    development = session.plan(.5, 4, 4)
    assert set(development) == {'a', 'b'}
    assert development['a'].notes[0] == Note(0, 62, 1, 100)
    assert development['b'].notes
    assert [name for name, _ in calls] == ['a', 'a', 'b']
    assert calls[-1][1].dependencies['a'] is development['a']
    assert calls[-1][1].role == 'bass_line'
    session.send(4, development)
    assert sent == [('a', 4, development['a']), ('b', 4, development['b'])]
    # Tornare alla prima sezione non conserva le voci della seconda.
    assert set(session.plan(.1, 8, 4)) == {'a'}


@pytest.mark.parametrize('failure', ['unsupported_role', 'inactive_dependency', 'cycle'])
def test_invalid_sections_rejected_during_loading(failure):
    data = config()
    assignments = data['sections'][1]['assignments']
    if failure == 'unsupported_role':
        assignments['a']['role'] = 'pulse'
    elif failure == 'inactive_dependency':
        del assignments['a']
    else:
        data['voices']['a']['dependencies'] = ['b']
    with pytest.raises(ValueError):
        setup(data)


def test_configuration_is_copied_and_request_parameters_cannot_be_replaced():
    data = config()
    session, calls, _ = setup(data)
    data['sections'][0]['assignments']['a']['parameters']['velocity'] = 120
    assert session.plan(0, 0, 4)['a'].notes[0].velocity == 70
    with pytest.raises(TypeError):
        calls[0][1].parameters['velocity'] = 1


def test_load_json_file_and_deliver_phrase(tmp_path):
    path = tmp_path / 'ensemble.json'
    data = config()
    del data['voices']['b']
    data['sections'] = data['sections'][:1]
    path.write_text(json.dumps(data))
    sent = []
    phrase = Phrase(4, (Note(0, 60, 1, 70),))
    session = EnsembleSession.from_file(
        path, {'source': Generator(lambda request: phrase, ('melody',))},
        {'out_a': lambda start, result: sent.append((start, result))})
    session.send(8, session.plan(0, 8, 4))
    assert sent == [(8, phrase)]


@pytest.mark.parametrize('optional', [['missing'], ['b', 'b'], ['a']])
def test_invalid_optional_dependencies_are_rejected(optional):
    data = config()
    data['voices']['b']['optional_dependencies'] = optional
    with pytest.raises(ValueError, match='facoltative'):
        setup(data)

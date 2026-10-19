from copy import deepcopy
from io import StringIO

from desnivel.cli.session_view import TerminalSessionView, render_session


def snapshot():
    return {
        'state': 'playing', 'error': None,
        'trip': {'progress': .261, 'elapsed_s': 8600, 'duration_s': 32421, 'distance_m': 15682, 'speed': 50},
        'transport': {'playing': True, 'beat': 220},
        'voices': {'voice_02': {
            'name': 'Bass', 'connected': True, 'active': False,
            'role': 'bass_line', 'role_mode': 'manual', 'next_entry_progress': .3,
            'preset': None, 'controls': {'density': {'value': .8}},
        }},
        'decisions': {'director': {'section': 'opening', 'from_progress': 0, 'until_progress': .3,
                                   'root': 57, 'scale': 'minor'}, 'coordinator': None},
    }


def test_refreshes_position_during_play_without_state_transition():
    now, output = [0.], StringIO()
    view = TerminalSessionView(output, lambda: now[0])
    first = snapshot()
    view.update(first)
    second = deepcopy(first)
    second['trip']['progress'] = .27
    second['transport']['beat'] = 222
    now[0] = .5
    view.update(second)
    assert '27.00%' not in output.getvalue()
    now[0] = 1
    view.update(second)
    assert '26.10%' in output.getvalue() and '27.00%' in output.getvalue()
    assert 'beat 222.00' in output.getvalue()
    assert 'fuori organico; ingresso al 30%' in output.getvalue()
    assert 'SCOLLEGATO' not in output.getvalue()


def test_view_reports_actual_planning_order_notes_and_reference_parts():
    state = snapshot()
    state['decisions']['coordinator'] = {
        'start': 224, 'length_beats': 4, 'section': 'development', 'order': ['a', 'b'],
        'voices': {
            'a': {'role': 'melody', 'dependencies': [], 'notes': [{'pitch': 57, 'beat': 0}]},
            'b': {'role': 'bass_line', 'dependencies': ['a'], 'notes': []},
        },
    }
    frame = render_session(state)
    assert 'a -> b' in frame
    assert '57@0' in frame
    assert 'riferimenti: a' in frame
    assert '0 note MIDI@beat: silenzio' in frame
    assert '224, 228' in frame

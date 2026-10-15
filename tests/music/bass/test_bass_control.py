from dataclasses import asdict

import pytest

from desnivel.music.bass.generator import BassSettings
from desnivel.music.bass.control import BassControl


def command(parameters, **extra):
    return dict(version=1, serial=1, parameters=parameters, **extra)


def test_partial_control_preserves_unspecified_settings_and_validates_register_together():
    initial = BassSettings(strategy='slap', highest=59)
    control = BassControl.from_dict(command({'density': .8, 'lowest': 48, 'highest': 71}), initial)
    assert control.settings.density == .8
    assert control.settings.lowest == 48 and control.settings.highest == 71
    assert control.settings.mobility == initial.mobility
    assert control.settings.articulation == initial.articulation
    assert control.transition_windows == 4
    assert initial.lowest == 28 and initial.density == 1.8


@pytest.mark.parametrize('data', [
    [], dict(version=True, serial=1, parameters={'density': .8}),
    dict(version=2, serial=1, parameters={'density': .8}),
    dict(version=1, parameters={'density': .8}),
    dict(version=1, serial=True, parameters={'density': .8}),
    command({}), command({'density': None}), command({'density': True}),
    command({'density': float('nan')}), command({'density': float('inf')}),
    command({'density': -1}), command({'mobility': 2}), command({'highest': 36.5}),
    command({'lowest': 60}), command({'preset': 'slap'}), command({'unknown': 1}),
    command({'density': .8}, transition_windows=-1),
    command({'density': .8}, transition_windows=1.5),
    command({'density': .8}, transition_windows=True),
    command({'density': .8}, unexpected=1),
])
def test_invalid_control_does_not_modify_original_settings(data):
    initial = BassSettings()
    before = asdict(initial)
    with pytest.raises((ValueError, TypeError)):
        BassControl.from_dict(data, initial)
    assert asdict(initial) == before


def test_new_control_merges_with_destination_during_transition():
    from desnivel.adapters.snake_live import BassSession
    from test_snake_live import snapshot
    session = BassSession(BassSettings(density=.5, mobility=.1))
    session.update(snapshot())
    first = BassControl.from_dict(command({'density': 1.5}), session.target_settings)
    session.set_settings(first.settings, 2)
    session.update(snapshot(2, 4.125))
    assert session.settings.density == 1
    second = BassControl.from_dict(command({'mobility': .8}), session.target_settings)
    session.set_settings(second.settings, 2)
    assert session.target_settings.density == 1.5
    assert session.settings.density == 1
    session.update(snapshot(3, 8.125))
    assert session.settings.density == 1.25
    assert session.settings.mobility == pytest.approx(.45)

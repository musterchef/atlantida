from dataclasses import asdict

import pytest
from desnivel.adapters.snake_live import BassSession
from desnivel.adapters.snake_sequence import Lane, SnakeState


def snapshot(serial=1,beat=.125,epoch=0,playing=1):
    lane=Lane(1,'16n',16,'forwards',beat % 4)
    state=SnakeState(tuple(range(48,64)),(1,)*16,(90,)*16,(200,)*16,
                     lane,lane,lane,120,0)
    return dict(version=1,source='snake',serial=serial,epoch=epoch,beat=beat,
                playing=playing,state=asdict(state))


def test_future_plan_stable_across_snapshots_and_reordered_udp():
    session=BassSession()
    first=session.update(snapshot())
    assert first['start']==4
    assert first['phrase']['notes']
    second=session.update(snapshot(2,.375))
    assert second['phrase']==first['phrase']
    assert second['revision']==first['revision']
    assert second['serial']==2
    assert session.update(snapshot()) is None


def test_stop_seek_and_changes_have_explicit_plans():
    session=BassSession()
    first=session.update(snapshot())
    changed=snapshot(2,.375)
    changed['state']['notes']=(50,)*16
    second=session.update(changed)
    assert second['start']==first['start']
    assert second['revision']>first['revision']
    assert second['phrase']!=first['phrase']
    stopped=session.update(snapshot(3,0,1,0))
    assert stopped['reset'] and stopped['session']!=first['session']
    restarted=session.update(snapshot(4,0,2))
    assert restarted['start']==4


def test_unknown_state_silences_and_multiple_sources_rejected():
    session=BassSession()
    data=snapshot();data['error']='fase non disponibile'
    assert session.update(data)['reset']
    data=snapshot(2);data['source']='other'
    with pytest.raises(ValueError,match='sorgente Snake cambiata'):
        session.update(data)


def test_new_python_process_has_new_session():
    assert BassSession().update(snapshot())['session']!=BassSession().update(snapshot())['session']


def test_controls_transition_on_musical_windows_not_snapshot_count():
    from desnivel.music.bass.generator import BassSettings
    session = BassSession(BassSettings(density=.5))
    first = session.update(snapshot())
    session.set_settings(BassSettings(density=1.5), transition_windows=2)
    repeated = session.update(snapshot(2, .375))
    assert repeated['phrase'] == first['phrase']
    assert session.settings.density == .5
    halfway = session.update(snapshot(3, 4.125))
    assert halfway['start'] == 8
    assert session.settings.density == 1
    session.update(snapshot(4, 4.375))
    assert session.settings.density == 1
    session.update(snapshot(5, 8.125))
    assert session.settings.density == 1.5


def test_settings_transition_rebases_after_transport_epoch_changes():
    from desnivel.music.bass.generator import BassSettings
    session = BassSession(BassSettings(density=.5))
    session.update(snapshot(1, 20.125))
    session.set_settings(BassSettings(density=1.5), transition_windows=2)
    session.update(snapshot(2, 24.125))
    assert session.settings.density == 1
    session.update(snapshot(3, 0, epoch=1, playing=0))
    session.update(snapshot(4, .125, epoch=2))
    assert session.settings.density == 1
    session.update(snapshot(5, 4.125, epoch=2))
    assert session.settings.density == 1.25

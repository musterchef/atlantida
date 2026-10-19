import json
from pathlib import Path

import numpy as np
import pytest

from desnivel.adapters.voice_device import VoiceDeviceBridge
from desnivel.cli.ensemble_runtime import EnsembleRuntime
from desnivel.trip.track import Track


def setup():
    now, sent = [0.], []
    bridge = VoiceDeviceBridge({}, lambda *args: sent.append(args), clock=lambda: now[0])
    track = Track('test', np.array([0., 10.]), {'cum_dist_m': np.array([0., 100.])})
    config = json.loads(Path('presets/organico.json').read_text())
    # Queste prove isolano trasporto e organico variabile con due voci.
    # La configurazione completa a quattro è verificata in test_trip_direction.
    config['voices'] = {name: spec for name, spec in config['voices'].items() if name in ('voice_01', 'voice_02')}
    for section in config['sections']:
        section['assignments'] = {name: spec for name, spec in section['assignments'].items() if name in config['voices']}
    runtime = EnsembleRuntime(track, config, bridge, speed=2, clock=lambda: now[0])
    serials = {}
    def receive(voice='voice_01', beat=0., playing=1, epoch=0):
        serials[voice] = serials.get(voice, 0)+1
        msg = dict(version=1, voice=voice, instance=voice, reply_port=9101 if voice=='voice_01' else 9102,
                   serial=serials[voice], action='transport' if serials[voice]>1 else 'hello',
                   transport=dict(beat=beat, playing=playing, epoch=epoch))
        bridge.handle(msg)
        runtime.on_message(bridge, msg)
    return runtime, bridge, now, sent, receive


def test_waiting_then_continuous_plans_sections_roles_and_status():
    runtime, bridge, now, sent, receive = setup()
    runtime.tick()
    assert runtime.state == 'waiting_for_transport'
    receive(); receive('voice_02')
    runtime.tick()
    assert runtime.state == 'playing'
    assert set(bridge.last_plans) == {'voice_01'}
    count = len(sent)
    runtime.tick()
    assert len(sent) == count  # Nessuna rigenerazione dello stesso intervallo.
    now[0] = 1.6
    receive(beat=4)
    runtime.tick()
    assert runtime.progress == pytest.approx(.32)
    assert set(bridge.last_plans) == {'voice_01', 'voice_02'}
    status = runtime.snapshot()
    assert status['section']['name'] == 'development'
    assert status['voices']['voice_02']['dependencies'] == ['voice_01']
    assert status['voices']['voice_01']['supported_roles'] == ['melody', 'sustained_texture', 'bass_line']
    json.dumps(status, allow_nan=False)
    # Override valido anche durante i successivi cambi di sezione.
    runtime.session.set_role('voice_01', 'sustained_texture')
    now[0] = 2
    receive(beat=8)
    runtime.tick()
    assert bridge.last_plans['voice_01']['notes'] == 1


def test_stop_pauses_trip_and_seek_replans_without_rewinding_trip():
    runtime, bridge, now, _, receive = setup()
    receive(); runtime.tick()
    now[0] = .5
    receive(beat=1, playing=0, epoch=1)
    runtime.tick()
    elapsed = runtime.elapsed
    assert not bridge.last_plans
    now[0] = 1
    runtime.tick()
    assert runtime.elapsed == elapsed
    receive(beat=0, playing=1, epoch=2)
    runtime.tick()
    assert runtime.elapsed == elapsed
    assert bridge.last_plans['voice_01']['start'] == 4
    now[0] = 1.1
    receive(beat=0, playing=1, epoch=3)
    runtime.tick()
    assert runtime.elapsed >= elapsed
    assert runtime.elapsed < 2


def test_missing_active_device_pauses_trip_and_lost_transport_cancels_plans():
    runtime, bridge, now, _, receive = setup()
    receive(); runtime.tick()
    now[0] = 1.6
    receive(beat=4); runtime.tick()
    assert runtime.state == 'waiting_for_devices'
    elapsed = runtime.elapsed
    now[0] = 2
    runtime.tick()
    assert runtime.elapsed == elapsed
    receive('voice_02'); receive(beat=5)
    runtime.tick()
    assert runtime.state == 'playing'
    now[0] = 6
    runtime.tick()
    assert runtime.state == 'waiting_for_transport'
    assert not runtime.sounding


def test_manual_parameters_reflected_in_status_and_applied_to_next_plan():
    runtime, bridge, now, sent, receive = setup()
    receive(); runtime.tick()
    bridge.handle(dict(version=1, voice='voice_01', instance='voice_01', reply_port=9101,
                       serial=2, action='parameter', parameter='velocity', value=45))
    # Usa il seriale successivo per il trasporto.
    bridge.handle(dict(version=1, voice='voice_01', instance='voice_01', reply_port=9101,
                       serial=3, action='hello'))
    assert runtime.snapshot()['voices']['voice_01']['controls']['velocity']['value'] == 45
    phrases = runtime.session.plan(0, 8, 4)
    assert all(35 <= n.velocity <= 53 for n in phrases['voice_01'].notes)


def test_invalid_controls_do_not_mutate_manual_values():
    runtime, _, _, _, _ = setup()
    with pytest.raises(ValueError):
        runtime.session.set_parameters('voice_01', {'velocity': 300})
    assert runtime.session.parameters_at('voice_01', 0) == {}


def test_inactive_reason_and_decisions_match_section_and_executed_plan():
    runtime, bridge, now, _, receive = setup()
    receive(); receive('voice_02'); runtime.tick()
    status = runtime.snapshot()
    part = status['voices']['voice_02']
    assert part['connected'] and not part['active']
    assert part['inactive_reason'] == 'not_assigned_to_section'
    assert part['next_entry_progress'] == .3
    assert status['decisions']['director']['until_progress'] == .3
    assert status['decisions']['coordinator']['order'] == ['voice_01']
    now[0] = 1.6
    receive(beat=4); runtime.tick()
    status = runtime.snapshot()
    plan = status['decisions']['coordinator']
    assert plan['order'] == ['voice_01', 'voice_02']
    assert plan['voices']['voice_02']['dependencies'] == ['voice_01']
    assert len(plan['voices']['voice_02']['notes']) == bridge.last_plans['voice_02']['notes']
    assert status['decisions']['director']['assignments']['voice_02']['source'] == 'section'
    runtime.session.set_role('voice_01', 'sustained_texture')
    assert runtime.snapshot()['decisions']['director']['assignments']['voice_01']['source'] == 'manual'

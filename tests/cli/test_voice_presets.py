import json

import pytest

from desnivel.adapters.voice_device import Control, DeviceVoice, VoiceDeviceBridge
from desnivel.cli.voice_presets import connect_preset_library
from desnivel.sinks.voice_presets import VoicePresetLibrary


def voices():
    return {'part': DeviceVoice(controls={'amount': Control(0, 1)}, values={'amount': .4},
                                presets={'base': {'amount': .1}}, apply=lambda values: None)}


def test_preset_creation_update_and_reload_are_distinct_from_base_configuration(tmp_path):
    path = tmp_path / 'custom.json'
    library = VoicePresetLibrary(path)
    parts = voices()
    connect_preset_library(library, parts)
    bridge = VoiceDeviceBridge(parts, lambda *args: None)
    def send(serial, action, **kwargs):
        return bridge.handle(dict(version=1, voice='part', instance='instance', reply_port=9101,
                                  serial=serial, action=action, **kwargs))
    send(1, 'hello')
    send(2, 'save_preset', preset='my groove')
    assert json.loads(path.read_text())['voices']['part']['my groove'] == {'amount': .4}
    with pytest.raises(ValueError, match='già presente'):
        send(3, 'save_preset', preset='my groove')
    with pytest.raises(ValueError, match='base protetto'):
        send(3, 'save_preset', preset='base', overwrite=True)
    send(3, 'parameter', parameter='amount', value=.7)
    send(4, 'save_preset', preset='my groove', overwrite=True)
    fresh = voices()
    connect_preset_library(VoicePresetLibrary(path), fresh)
    assert fresh['part'].presets['my groove'] == {'amount': .7}
    assert fresh['part'].presets['base'] == {'amount': .1}
    assert fresh['part'].editable_presets == {'my groove'}
    assert list(tmp_path.iterdir()) == [path]


def test_failed_write_does_not_add_a_preset_to_the_live_device(tmp_path, monkeypatch):
    library = VoicePresetLibrary(tmp_path / 'custom.json')
    parts = voices()
    connect_preset_library(library, parts)
    def reject(*args):
        raise OSError('disk full')
    parts['part'].save_preset = reject
    bridge = VoiceDeviceBridge(parts, lambda *args: None)
    base = dict(version=1, voice='part', instance='instance', reply_port=9101)
    bridge.handle(dict(base, serial=1, action='hello'))
    with pytest.raises(OSError):
        bridge.handle(dict(base, serial=2, action='save_preset', preset='new'))
    assert set(parts['part'].presets) == {'base'}


def test_incompatible_library_is_rejected_before_the_session_starts(tmp_path):
    path = tmp_path / 'custom.json'
    path.write_text(json.dumps({'version': 1, 'voices': {'part': {'custom': {'other': 1}}}}))
    with pytest.raises(ValueError, match='incompatibili'):
        connect_preset_library(VoicePresetLibrary(path), voices())

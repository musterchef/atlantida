import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('build_voice_device', ROOT / 'tools/build_voice_device.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_device_has_valid_connections_and_native_midi_output():
    patch = json.loads((ROOT / 'm4l/desnivel_voice.maxpat').read_text())['patcher']
    boxes = {entry['box']['id']: entry['box'] for entry in patch['boxes']}
    for line in patch['lines']:
        assert line['patchline']['source'][0] in boxes
        assert line['patchline']['destination'][0] in boxes
    assert boxes['midi_format']['text'] == 'midiformat'
    assert boxes['midi_out']['text'] == 'midiout'
    assert boxes['notes_unpack']['varname'] == 'notes_unpack'
    assert boxes['notes_flush']['varname'] == 'notes_flush'
    assert all('bass' not in box.get('text', '').lower() for box in boxes.values())
    ui = [b['presentation_rect'] for b in boxes.values() if b.get('presentation')]
    assert all(x >= 0 and y >= 0 and x+w <= 650 and y+h <= 169 for x,y,w,h in ui)


def test_build_preserves_midi_type_and_packages_source():
    document = json.loads((ROOT / 'm4l/desnivel_voice.maxpat').read_text())
    empty = b'{"patcher":{}}\0'
    template = b'ampf' + struct.pack('<I', 4) + b'mmmmmeta' + struct.pack('<II',4,0) + b'ptch' + struct.pack('<I',len(empty)) + empty
    raw = builder.build(template, document)
    assert raw[:28] == template[:28]
    assert struct.unpack_from('<I', raw, 28)[0] == len(raw)-32
    assert json.loads(raw[32:].rstrip(b'\0\n')) == document

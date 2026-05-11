"""Test del bridge OSC -> MIDI.

Copre:
- traduzione valore (`osc_to_midi_value`) per canali float e int;
- handler `OscToMidiBridge.handle_mod` / `handle_event` con
  `FakeMidiOut`;
- canali e eventi non mappati: ignorati silenziosamente.
"""
from __future__ import annotations

from desnivel.bridges.osc_to_midi import (
    CHANNEL_TO_CC,
    EVENT_TO_NOTE,
    MIDI_CHANNEL_CC,
    MIDI_CHANNEL_EVENTS,
    CcMapping,
    FakeMidiOut,
    OscToMidiBridge,
    osc_to_midi_value,
)


# ──────────────────── osc_to_midi_value ─────────────────────────────


def test_float_channel_scales_to_0_127() -> None:
    m = CcMapping(cc=20, is_int=False)
    assert osc_to_midi_value(m, 0.0) == 0
    assert osc_to_midi_value(m, 1.0) == 127
    assert osc_to_midi_value(m, 0.5) == 64


def test_float_channel_clips_out_of_range() -> None:
    m = CcMapping(cc=20, is_int=False)
    assert osc_to_midi_value(m, -1.0) == 0
    assert osc_to_midi_value(m, 2.0) == 127


def test_int_channel_passes_through_clipped() -> None:
    m = CcMapping(cc=23, is_int=True)
    assert osc_to_midi_value(m, 0) == 0
    assert osc_to_midi_value(m, 7) == 7
    assert osc_to_midi_value(m, 200) == 127
    assert osc_to_midi_value(m, -3) == 0


# ──────────────────── OscToMidiBridge.handle_mod ────────────────────


def test_known_mod_address_emits_cc() -> None:
    midi = FakeMidiOut()
    bridge = OscToMidiBridge(midi=midi)
    bridge.handle_mod("/mod/journey/energy", 0.5)
    assert midi.messages == [("cc", MIDI_CHANNEL_CC, 21, 64)]


def test_int_mod_address_emits_cc_without_scaling() -> None:
    midi = FakeMidiOut()
    bridge = OscToMidiBridge(midi=midi)
    bridge.handle_mod("/mod/macro/scale", 5)
    assert midi.messages == [("cc", MIDI_CHANNEL_CC, 23, 5)]


def test_unknown_mod_address_is_ignored() -> None:
    midi = FakeMidiOut()
    bridge = OscToMidiBridge(midi=midi)
    bridge.handle_mod("/mod/cosmic/vibe", 0.7)
    assert midi.messages == []


# ──────────────────── OscToMidiBridge.handle_event ──────────────────


def test_known_event_emits_note_on_and_off() -> None:
    midi = FakeMidiOut()
    bridge = OscToMidiBridge(midi=midi)
    bridge.handle_event("/event/major/summit", "{}")
    note = EVENT_TO_NOTE["/event/major/summit"]
    assert midi.messages == [
        ("note_on", MIDI_CHANNEL_EVENTS, note, 100),
        ("note_off", MIDI_CHANNEL_EVENTS, note, 0),
    ]


def test_unknown_event_is_ignored() -> None:
    midi = FakeMidiOut()
    bridge = OscToMidiBridge(midi=midi)
    bridge.handle_event("/event/minor/something_we_dont_map", "{}")
    assert midi.messages == []


# ──────────────────── Mappa: invarianti minime ──────────────────────


def test_mapping_has_no_duplicate_cc_numbers() -> None:
    cc_numbers = [m.cc for m in CHANNEL_TO_CC.values()]
    assert len(cc_numbers) == len(set(cc_numbers)), \
        "Due canali OSC mappano sullo stesso CC: c'e' un conflitto."


def test_mapping_has_no_duplicate_event_notes() -> None:
    notes = list(EVENT_TO_NOTE.values())
    assert len(notes) == len(set(notes)), \
        "Due eventi mappano sulla stessa nota: c'e' un conflitto."


def test_all_cc_numbers_in_valid_midi_range() -> None:
    for addr, m in CHANNEL_TO_CC.items():
        assert 0 <= m.cc <= 127, f"CC fuori range per {addr}"


def test_all_event_notes_in_valid_midi_range() -> None:
    for addr, note in EVENT_TO_NOTE.items():
        assert 0 <= note <= 127, f"Nota fuori range per {addr}"

"""Bridges: traduttori provvisori verso target che non parlano OSC nativo.

Vedi `osc_to_midi.py` per il contesto: tutto qui dentro e' provvisorio
e si butta quando arriva un client OSC nativo (es. patch M4L).
"""
from .osc_to_midi import (
    CHANNEL_TO_CC,
    EVENT_TO_NOTE,
    CcMapping,
    FakeMidiOut,
    MidiOut,
    MidoMidiOut,
    OscToMidiBridge,
    osc_to_midi_value,
    run_bridge,
)

__all__ = [
    "CHANNEL_TO_CC",
    "EVENT_TO_NOTE",
    "CcMapping",
    "FakeMidiOut",
    "MidiOut",
    "MidoMidiOut",
    "OscToMidiBridge",
    "osc_to_midi_value",
    "run_bridge",
]

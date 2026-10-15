"""Test della specifica semantica del Rack DESNIVEL.

Verifica che `rack_spec.py` (fonte musicale) e `osc_to_midi.py`
(tabella tecnica) restino in sincrono: NON deve essere possibile
aggiungere un canale OSC senza aggiornare entrambi.
"""
from __future__ import annotations

from desnivel.bridges.osc_to_midi import CHANNEL_TO_CC
from desnivel.bridges.rack_spec import (
    AUX_CC,
    SPEC_BY_CC,
    VOICE_RACK,
    voice_macro_names,
)


def test_voice_rack_has_8_macros() -> None:
    """Il Rack principale ha esattamente 8 macro (limite Ableton)."""
    assert len(VOICE_RACK) == 8


def test_macro_names_are_unique() -> None:
    names = [m.name for m in (*VOICE_RACK, *AUX_CC)]
    assert len(names) == len(set(names))


def test_cc_numbers_are_unique_across_rack_and_aux() -> None:
    ccs = [m.cc for m in (*VOICE_RACK, *AUX_CC)]
    assert len(ccs) == len(set(ccs))


def test_every_spec_cc_exists_in_bridge() -> None:
    """Ogni CC dichiarato in rack_spec deve esistere nel bridge tecnico."""
    bridge_ccs = {m.cc for m in CHANNEL_TO_CC.values()}
    for spec in (*VOICE_RACK, *AUX_CC):
        assert spec.cc in bridge_ccs, (
            f"CC {spec.cc} ({spec.name}) e' in rack_spec ma "
            f"non in CHANNEL_TO_CC"
        )


def test_every_bridge_cc_exists_in_spec() -> None:
    """Ogni CC del bridge deve avere una semantica documentata."""
    spec_ccs = {m.cc for m in (*VOICE_RACK, *AUX_CC)}
    for addr, m in CHANNEL_TO_CC.items():
        assert m.cc in spec_ccs, (
            f"CC {m.cc} ({addr}) e' nel bridge ma "
            f"non in rack_spec"
        )


def test_spec_osc_address_matches_bridge() -> None:
    """L'address OSC della spec deve corrispondere a quello del bridge."""
    bridge_by_cc = {m.cc: addr for addr, m in CHANNEL_TO_CC.items()}
    for spec in (*VOICE_RACK, *AUX_CC):
        assert bridge_by_cc[spec.cc] == spec.osc_address


def test_spec_by_cc_indexes_all() -> None:
    total = len(VOICE_RACK) + len(AUX_CC)
    assert len(SPEC_BY_CC) == total


def test_voice_macro_names_in_order() -> None:
    names = voice_macro_names()
    assert names[0] == "Root"
    assert names[1] == "Mode"
    assert names[2] == "Brightness"
    assert len(names) == 8


def test_range_tuples_have_two_elements() -> None:
    for spec in (*VOICE_RACK, *AUX_CC):
        assert len(spec.range_ableton) == 2

"""Specifica semantica del Rack DESNIVEL in Ableton.

**Fonte di verita' unica** della mappatura "canale OSC ↔ macro del
Rack ↔ device/parametro Ableton ↔ range musicalmente sensato".

Questo modulo NON contiene logica MIDI: lavora solo come tabella
dichiarativa. La traduzione OSC → CC vive in `osc_to_midi.py` e usa
`CHANNEL_TO_CC` (la tabella tecnica). Qui invece descriviamo il
livello sopra: quale macro semantica del rack riceve quel CC, su
quale device/parametro Ableton va instradata, e quale range Ableton
va impostato per ottenere musica e non rumore.

L'utente costruisce il rack UNA VOLTA seguendo `doc/ABLETON-RACK.md`.
Da quel momento qualsiasi preset (Wavetable, Operator, sample) cala
dentro la "instrument chain" del rack senza dover rifare niente.

Convenzioni di ``range_ableton``:
- Per i parametri **continui** (filtro, riverbero, drive): tupla
  (min, max) in unita' "umane" leggibili (es. "200 Hz", "12 kHz").
- Per i parametri **discreti** (Pitch in semitoni, Chain Selector):
  tupla (min, max) di interi.
- Sono i valori da inserire nel campo "Min" / "Max" della riga di
  binding MIDI in Ableton (Cmd-M).
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class MacroSpec:
    """Una macro del Rack DESNIVEL.

    Attributes:
        name: nome semantico (sara' anche il nome della macro in
            Ableton). Es: ``"Root"``, ``"Brightness"``.
        cc: numero MIDI CC che la pilota (combacia con
            `osc_to_midi.CHANNEL_TO_CC`).
        osc_address: address OSC sorgente. Documentazione.
        device: device Ableton di destinazione (es. ``"Pitch"``,
            ``"Auto Filter"``, ``"Reverb"``). Stringa libera, serve
            al documento, non al codice.
        parameter: parametro del device su cui mappare la macro.
        range_ableton: (min, max) da impostare nel binding MIDI di
            Ableton. Stringhe per i continui, int per i discreti.
        description: significato musicale, una frase.
    """

    name: str
    cc: int
    osc_address: str
    device: str
    parameter: str
    range_ableton: tuple[str, str] | tuple[int, int]
    description: str


# ──────────────────── Rack principale "Voice" (8 macro) ────────────


#: 8 macro del Rack principale, in ordine di importanza musicale.
#: Le prime 4 sono ESSENZIALI per il drone armonico. Le ultime 4
#: aggiungono respiro e dinamica.
VOICE_RACK: tuple[MacroSpec, ...] = (
    MacroSpec(
        name="Root",
        cc=25,
        osc_address="/mod/meso/root",
        device="Pitch (MIDI device)",
        parameter="Pitch",
        range_ableton=(-12, 12),
        description=(
            "Fondamentale del momento. Cambia ogni ~8 km lungo la "
            "sequenza modale di HarmonyConfig."
        ),
    ),
    MacroSpec(
        name="Mode",
        cc=23,
        osc_address="/mod/macro/scale",
        device="Rack Chain Selector",
        parameter="Chain Selector",
        range_ableton=(0, 5),
        description=(
            "Modalita' musicale: 0=ionian 1=dorian 2=phrygian "
            "3=lydian 4=mixolydian 5=whole-tone. Cambia per sezione "
            "macro (~60s di tappa). Implementato come Chain Selector "
            "del Rack: 6 catene, una per modo."
        ),
    ),
    MacroSpec(
        name="Brightness",
        cc=31,
        osc_address="/mod/macro/brightness",
        device="Auto Filter",
        parameter="Frequency",
        range_ableton=("400 Hz", "12 kHz"),
        description=(
            "Brillantezza generale. Si apre col mondo timbrico "
            "(alto = bells/granular) e col registro."
        ),
    ),
    MacroSpec(
        name="Space",
        cc=30,
        osc_address="/mod/macro/space",
        device="Reverb",
        parameter="Dry/Wet",
        range_ableton=("0 %", "45 %"),
        description=(
            "Apertura spaziale. Alias dell'openness: paesaggio aperto "
            "= piu' riverbero. Range stretto per non annegare il suono."
        ),
    ),
    MacroSpec(
        name="Tension",
        cc=26,
        osc_address="/mod/meso/tension",
        device="Auto Filter",
        parameter="Resonance",
        range_ableton=("0 %", "55 %"),
        description=(
            "Tensione muscolare di decine di secondi: salite, "
            "cambi di pendenza. Stringe il filtro."
        ),
    ),
    MacroSpec(
        name="Energy",
        cc=21,
        osc_address="/mod/journey/energy",
        device="Saturator",
        parameter="Drive",
        range_ableton=("0 dB", "12 dB"),
        description=(
            "Sforzo locale. Drive di saturazione, NON volume (cosi' "
            "il livello complessivo resta stabile)."
        ),
    ),
    MacroSpec(
        name="Register",
        cc=29,
        osc_address="/mod/macro/register",
        device="Pitch (secondo)",
        parameter="Pitch",
        range_ableton=(-12, 12),
        description=(
            "Registro: -12 sui passaggi bassi della tappa, +12 sulle "
            "quote alte. Si SOMMA a Root: in cima al colle, root sale "
            "di un'ottava."
        ),
    ),
    MacroSpec(
        name="Openness",
        cc=22,
        osc_address="/mod/journey/openness",
        device="Auto Filter (secondo)",
        parameter="Frequency",
        range_ableton=("200 Hz", "6 kHz"),
        description=(
            "Varianza altimetrica = ariosita'. Apre un secondo filtro "
            "in parallelo a Brightness per dare un secondo respiro."
        ),
    ),
)


# ──────────────────── CC ausiliari (fuori dal Rack) ────────────────


#: CC che NON entrano nelle 8 macro principali. Disponibili per:
#: - un secondo rack "Pulse" (sequencer + percussioni)
#: - automazioni libere su effetti send/return
#: - mappature future via M4L
AUX_CC: tuple[MacroSpec, ...] = (
    MacroSpec(
        name="Phase",
        cc=20,
        osc_address="/mod/journey/phase",
        device="(libero)",
        parameter="(libero)",
        range_ableton=("0 %", "100 %"),
        description=(
            "Avanzamento 0→1 lungo la tappa. Utile per automazioni "
            "lente: crossfade fra layer, apertura progressiva di un send."
        ),
    ),
    MacroSpec(
        name="Palette",
        cc=24,
        osc_address="/mod/macro/palette",
        device="(secondo rack)",
        parameter="Chain Selector",
        range_ableton=(0, 5),
        description=(
            "Famiglia timbrica (pad/strings/bells/granular/brass). "
            "Pilota il Chain Selector di un secondo rack opzionale, "
            "una catena per famiglia. Se non usato, ignora."
        ),
    ),
    MacroSpec(
        name="Density",
        cc=27,
        osc_address="/mod/body/euclid_k",
        device="EuclidStep / sequencer",
        parameter="Hits (k)",
        range_ableton=(3, 11),
        description=(
            "Numero di hit nel pattern euclideo E(k, 16). Va su un "
            "sequencer (EuclidStep, M4L sequencer). NON va su un "
            "parametro audio continuo: e' un intero ritmico."
        ),
    ),
    MacroSpec(
        name="Rotation",
        cc=28,
        osc_address="/mod/body/euclid_rot",
        device="EuclidStep / sequencer",
        parameter="Rotation",
        range_ableton=(0, 15),
        description=(
            "Rotazione del pattern euclideo. Anche questo intero "
            "ritmico: NON usare su un knob audio."
        ),
    ),
)


# ──────────────────── Lookup helpers ───────────────────────────────


#: Indice CC# -> MacroSpec, comprende sia VOICE_RACK che AUX_CC.
#: Immutabile.
SPEC_BY_CC: Mapping[int, MacroSpec] = MappingProxyType({
    m.cc: m for m in (*VOICE_RACK, *AUX_CC)
})


def voice_macro_names() -> tuple[str, ...]:
    """Nomi delle 8 macro del Rack principale, in ordine."""
    return tuple(m.name for m in VOICE_RACK)


__all__ = [
    "MacroSpec",
    "VOICE_RACK",
    "AUX_CC",
    "SPEC_BY_CC",
    "voice_macro_names",
]

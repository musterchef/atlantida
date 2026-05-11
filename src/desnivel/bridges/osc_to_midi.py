"""Bridge OSC -> MIDI: ponte provvisorio verso Ableton (Binario A).

**Status**: provvisorio dichiarato. Destinazione finale = patch
Max for Live nativo che riceve OSC. Questo modulo esiste solo per
arrivare all'ascolto in mezz'ora senza scrivere Max. Vedi `TODO.md`
sezione "Contratto Ableton" per i vincoli.

Architettura modulare (stesso stile di `sinks.osc`):

1. **Tabella di mapping dichiarativa** (`CHANNEL_TO_CC`,
   `EVENT_TO_NOTE`): dati puri, niente logica musicale. Quando un
   canale OSC arriva, il bridge consulta la tabella e basta.

2. **MidiOut Protocol** (`MidoMidiOut` reale, `FakeMidiOut` per i
   test): lazy import di `mido`.

3. **OscToMidiBridge**: handler delle rotte OSC. Stateless. Il
   server (`run_bridge`) e' un thin layer che apre la porta UDP e
   passa i messaggi.

Convenzioni:

- Modulazioni continue -> MIDI CC sul canale 1, CC# 20-31 (zona libera
  per general purpose nella spec MIDI).
- Eventi -> Note On (+ Note Off immediato) sul canale 16, note 60+.
  E' un trigger grezzo: tutti i metadati dell'evento si perdono.
  Quando passeremo a M4L recupereremo location e source_id.
- Canali OSC non mappati: ignorati silenziosamente. La tabella e'
  intenzionalmente minima.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np


# ──────────────────── Tabelle di mapping (dati puri) ───────────────


@dataclass(frozen=True)
class CcMapping:
    """Come tradurre un canale OSC continuo in un MIDI CC.

    Args:
        cc: numero del CC (0-127).
        is_int: se ``True``, il valore arriva gia' come intero
            (es. ``macro_scale``, ``meso_root``) e va solo clippato
            in 0-127. Se ``False``, e' un float in 0..1 e va
            scalato a 0-127.
    """

    cc: int
    is_int: bool = False


#: Mappa address OSC -> CC. Volutamente piccola: solo i canali che
#: vogliamo sentire subito. Tutto il resto si recupera in M4L.
CHANNEL_TO_CC: dict[str, CcMapping] = {
    "/mod/journey/phase":    CcMapping(cc=20),
    "/mod/journey/energy":   CcMapping(cc=21),
    "/mod/journey/openness": CcMapping(cc=22),
    "/mod/macro/scale":      CcMapping(cc=23, is_int=True),
    "/mod/macro/palette":    CcMapping(cc=24, is_int=True),
    "/mod/meso/root":        CcMapping(cc=25, is_int=True),
    "/mod/meso/tension":     CcMapping(cc=26),
    "/mod/body/euclid_k":    CcMapping(cc=27, is_int=True),
    "/mod/body/euclid_rot":  CcMapping(cc=28, is_int=True),
}


#: Mappa address evento -> nota MIDI. Note diverse per kind cosi'
#: in Ableton si possono usare Drum Rack / Simpler per triggerare
#: clip diverse.
EVENT_TO_NOTE: dict[str, int] = {
    "/event/major/start":          60,
    "/event/major/end":            61,
    "/event/major/summit":         62,
    "/event/major/sea_first_view": 63,
    "/event/major/poi":            64,
}

# CC su canale 1 (0-indexed = 0), eventi su canale 16 (0-indexed = 15).
MIDI_CHANNEL_CC = 0
MIDI_CHANNEL_EVENTS = 15
EVENT_VELOCITY = 100


def osc_to_midi_value(mapping: CcMapping, value: float) -> int:
    """Funzione pura: traduce un valore OSC in un CC MIDI 0-127.

    - ``is_int``: clip a 0-127 dopo round (il valore arriva gia' come
      indice discreto, es. modo musicale).
    - altrimenti: assume 0..1 e scala a 0-127.
    """
    if mapping.is_int:
        return int(np.clip(round(float(value)), 0, 127))
    scaled = round(float(value) * 127.0)
    return int(np.clip(scaled, 0, 127))


# ──────────────────── MidiOut (Protocol + impl) ────────────────────


@runtime_checkable
class MidiOut(Protocol):
    """Interfaccia minima per inviare messaggi MIDI."""

    def send_cc(self, channel: int, cc: int, value: int) -> None: ...
    def send_note_on(self, channel: int, note: int, velocity: int) -> None: ...
    def send_note_off(self, channel: int, note: int) -> None: ...
    def close(self) -> None: ...


class MidoMidiOut:
    """Wrapper su `mido.open_output`. Import lazy."""

    def __init__(self, port_name: str) -> None:
        try:
            import mido
        except ImportError as exc:
            raise ImportError(
                "mido non installato. `pip install -e .[midi]`."
            ) from exc
        self._mido = mido
        names = mido.get_output_names()
        if port_name not in names:
            raise SystemExit(
                f"Porta MIDI '{port_name}' non trovata.\n"
                f"Disponibili: {names}\n"
                f"Suggerimento: abilita 'IAC Bus 1' in Audio MIDI Setup.",
            )
        self._port = mido.open_output(port_name)

    def send_cc(self, channel: int, cc: int, value: int) -> None:
        self._port.send(self._mido.Message(
            "control_change", channel=channel, control=cc, value=value,
        ))

    def send_note_on(self, channel: int, note: int, velocity: int) -> None:
        self._port.send(self._mido.Message(
            "note_on", channel=channel, note=note, velocity=velocity,
        ))

    def send_note_off(self, channel: int, note: int) -> None:
        self._port.send(self._mido.Message(
            "note_off", channel=channel, note=note, velocity=0,
        ))

    def close(self) -> None:
        self._port.close()


class FakeMidiOut:
    """MidiOut che accumula messaggi in memoria. Usato nei test."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, int, int, int]] = []
        self.closed = False

    def send_cc(self, channel: int, cc: int, value: int) -> None:
        self.messages.append(("cc", channel, cc, value))

    def send_note_on(self, channel: int, note: int, velocity: int) -> None:
        self.messages.append(("note_on", channel, note, velocity))

    def send_note_off(self, channel: int, note: int) -> None:
        self.messages.append(("note_off", channel, note, 0))

    def close(self) -> None:
        self.closed = True


# ──────────────────── Bridge (handler OSC -> MidiOut) ──────────────


@dataclass
class OscToMidiBridge:
    """Handler stateless: riceve un address+valore OSC, emette MIDI.

    Non parla con la rete: il server OSC (vedi `run_bridge`) chiama
    `handle_mod` / `handle_event` per ogni messaggio ricevuto.
    """

    midi: MidiOut

    def handle_mod(self, address: str, value: float) -> None:
        mapping = CHANNEL_TO_CC.get(address)
        if mapping is None:
            return
        midi_value = osc_to_midi_value(mapping, value)
        self.midi.send_cc(MIDI_CHANNEL_CC, mapping.cc, midi_value)

    def handle_event(self, address: str, _payload_json: str = "") -> None:
        note = EVENT_TO_NOTE.get(address)
        if note is None:
            return
        self.midi.send_note_on(MIDI_CHANNEL_EVENTS, note, EVENT_VELOCITY)
        # Note Off immediato: e' un trigger, non una nota tenuta.
        self.midi.send_note_off(MIDI_CHANNEL_EVENTS, note)


# ──────────────────── Server (thin layer su python-osc) ────────────


def _osc_mod_handler(bridge: OscToMidiBridge):
    def handler(address: str, *args: Any) -> None:
        if not args:
            return
        try:
            value = float(args[0])
        except (TypeError, ValueError):
            return
        bridge.handle_mod(address, value)
    return handler


def _osc_event_handler(bridge: OscToMidiBridge):
    def handler(address: str, *args: Any) -> None:
        payload = str(args[0]) if args else ""
        bridge.handle_event(address, payload)
    return handler


def build_dispatcher(bridge: OscToMidiBridge):
    """Crea un `pythonosc.dispatcher.Dispatcher` con le rotte standard."""
    try:
        from pythonosc.dispatcher import Dispatcher
    except ImportError as exc:
        raise ImportError(
            "python-osc non installato. `pip install -e .[osc]`.",
        ) from exc
    d = Dispatcher()
    d.map("/mod/*/*", _osc_mod_handler(bridge))
    d.map("/event/major/*", _osc_event_handler(bridge))
    d.map("/event/minor/*", _osc_event_handler(bridge))
    return d


def print_mapping() -> None:
    """Stampa la mappa attiva (utile all'avvio)."""
    print("[bridge] canali continui -> CC (MIDI channel "
          f"{MIDI_CHANNEL_CC + 1}):")
    for addr, m in CHANNEL_TO_CC.items():
        kind = "int" if m.is_int else "float 0..1"
        print(f"  {addr:32s} -> CC {m.cc:3d}   [{kind}]")
    print(f"[bridge] eventi -> Note On (MIDI channel "
          f"{MIDI_CHANNEL_EVENTS + 1}):")
    for addr, note in EVENT_TO_NOTE.items():
        print(f"  {addr:32s} -> note {note}")


def run_bridge(host: str, port: int, midi: MidiOut) -> None:
    """Apre il server OSC bloccante. Ctrl+C per uscire."""
    try:
        from pythonosc.osc_server import BlockingOSCUDPServer
    except ImportError as exc:
        raise ImportError(
            "python-osc non installato. `pip install -e .[osc]`.",
        ) from exc
    bridge = OscToMidiBridge(midi=midi)
    dispatcher = build_dispatcher(bridge)
    server = BlockingOSCUDPServer((host, port), dispatcher)
    print(f"[bridge] in ascolto su {host}:{port} -> MIDI.  Ctrl+C per uscire.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] stop.")
    finally:
        midi.close()


# ──────────────────── CLI ──────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="desnivel-bridge-midi",
        description=(
            "Bridge OSC -> MIDI (provvisorio, Binario A). "
            "Riceve OSC da desnivel-play e lo ribattezza in CC/Note "
            "su una porta MIDI virtuale (es. IAC Bus 1)."
        ),
    )
    parser.add_argument(
        "--osc-host", default="127.0.0.1",
        help="Host OSC in ascolto (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--osc-port", type=int, default=9000,
        help="Porta OSC in ascolto (default: 9000).",
    )
    parser.add_argument(
        "--midi-port", default=None,
        help="Nome della porta MIDI di output (es. 'IAC Bus 1').",
    )
    parser.add_argument(
        "--list-midi-ports", action="store_true",
        help="Elenca le porte MIDI disponibili ed esce.",
    )
    parser.add_argument(
        "--show-mapping", action="store_true",
        help="Stampa la mappa canale->CC e esce.",
    )
    args = parser.parse_args(argv)

    if args.show_mapping:
        print_mapping()
        return 0

    if args.list_midi_ports:
        try:
            import mido
        except ImportError:
            print("mido non installato. `pip install -e .[midi]`.")
            return 1
        for name in mido.get_output_names():
            print(name)
        return 0

    if args.midi_port is None:
        parser.error("--midi-port e' richiesto (usa --list-midi-ports per "
                     "vedere quelle disponibili).")

    print_mapping()
    midi = MidoMidiOut(args.midi_port)
    run_bridge(args.osc_host, args.osc_port, midi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CcMapping",
    "CHANNEL_TO_CC",
    "EVENT_TO_NOTE",
    "MIDI_CHANNEL_CC",
    "MIDI_CHANNEL_EVENTS",
    "osc_to_midi_value",
    "MidiOut",
    "MidoMidiOut",
    "FakeMidiOut",
    "OscToMidiBridge",
    "build_dispatcher",
    "run_bridge",
    "main",
]

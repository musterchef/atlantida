"""Tool: invia uno sweep MIDI continuo su tutti i CC del bridge.

Serve per **mappare comodamente in Ableton MIDI Map mode**: ogni CC
viene attraversato ripetutamente da 0 a 127 e ritorno, cosi' puoi
cliccare un knob e aspettare 1-2 secondi che il binding si chiuda.

Non passa per OSC: scrive direttamente sulla porta MIDI (stesso
canale e CC# del bridge `osc_to_midi.py`). Si usa al posto del
bridge, non insieme.

Esempio::

    desnivel-midi-sweep --midi-port "IAC Driver Bus 1"

Ctrl+C per fermarlo.
"""
from __future__ import annotations

import argparse
import time

from desnivel.bridges.osc_to_midi import (
    CHANNEL_TO_CC,
    EVENT_TO_NOTE,
    MIDI_CHANNEL_CC,
    MIDI_CHANNEL_EVENTS,
    EVENT_VELOCITY,
    MidoMidiOut,
)


def _sweep_value(t: float, period_s: float) -> int:
    """Triangolare 0..127..0 con periodo `period_s`."""
    phase = (t % period_s) / period_s  # 0..1
    tri = 1.0 - abs(2.0 * phase - 1.0)  # 0..1..0
    return int(round(tri * 127.0))


def _run_solo(midi: "MidoMidiOut", period: float, rate_hz: float) -> None:
    """Modalita' assistita: un CC alla volta, INVIO per passare al successivo.

    Workflow consigliato:
      1. Lancia con --solo.
      2. In Ableton: Cmd+M, clicca il knob, attendi 1-2s -> bind.
      3. Cmd+M per uscire dal MIDI Map (opzionale).
      4. Premi INVIO sul terminale per passare al CC successivo.
    """
    import threading

    items = list(CHANNEL_TO_CC.items())
    print("\n[sweep --solo] mapping assistito.")
    print("Per ogni CC: Cmd+M in Ableton, clicca il knob, INVIO qui.")
    print("Ctrl+C per uscire.\n")

    period = max(period, 0.1)
    dt = 1.0 / max(rate_hz, 1.0)

    try:
        for addr, m in items:
            print(f"--> CC {m.cc:3d}   ({addr})    [INVIO per il prossimo]")
            stop = threading.Event()

            def _emit() -> None:
                start = time.monotonic()
                while not stop.is_set():
                    t = time.monotonic() - start
                    midi.send_cc(MIDI_CHANNEL_CC, m.cc, _sweep_value(t, period))
                    time.sleep(dt)

            th = threading.Thread(target=_emit, daemon=True)
            th.start()
            try:
                input()
            except EOFError:
                stop.set(); th.join()
                break
            stop.set()
            th.join()
        print("[sweep --solo] tutti i CC scorsi. Fine.")
    finally:
        midi.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="desnivel-midi-sweep",
        description=(
            "Sweep MIDI continuo su tutti i CC mappati dal bridge. "
            "Utile per fare MIDI Map in Ableton con calma."
        ),
    )
    parser.add_argument(
        "--midi-port", required=True,
        help="Nome porta MIDI (es. 'IAC Driver Bus 1').",
    )
    parser.add_argument(
        "--period", type=float, default=4.0,
        help="Periodo del triangolo in secondi (default: 4.0).",
    )
    parser.add_argument(
        "--rate-hz", type=float, default=20.0,
        help="Frequenza di update (default: 20 Hz).",
    )
    parser.add_argument(
        "--with-events", action="store_true",
        help="Invia anche le Note On di tutti gli eventi, in loop.",
    )
    parser.add_argument(
        "--event-period", type=float, default=2.0,
        help="Intervallo tra eventi se --with-events (default: 2 s).",
    )
    parser.add_argument(
        "--cc", type=int, default=None,
        help="Sweep di un solo CC (es. --cc 21). Default: tutti insieme.",
    )
    parser.add_argument(
        "--solo", action="store_true",
        help="Modalita' assistita: sweep un CC alla volta, premi INVIO "
             "per passare al successivo (Cmd+M -> click knob -> INVIO).",
    )
    args = parser.parse_args(argv)

    midi = MidoMidiOut(args.midi_port)
    print(f"[sweep] -> {args.midi_port}")

    if args.solo:
        _run_solo(midi, args.period, args.rate_hz)
        return 0

    if args.cc is not None:
        cc_list = [args.cc]
        print(f"[sweep] sweep solo CC {args.cc}, "
              f"periodo={args.period}s, {args.rate_hz} Hz. Ctrl+C per uscire.")
    else:
        cc_list = [m.cc for m in CHANNEL_TO_CC.values()]
        print(f"[sweep] {len(CHANNEL_TO_CC)} CC in sweep "
              f"(periodo={args.period}s, {args.rate_hz} Hz). Ctrl+C per uscire.")
        for addr, m in CHANNEL_TO_CC.items():
            print(f"  CC {m.cc:3d}  <-  {addr}")
    if args.with_events:
        print(f"[sweep] eventi: 1 Note On ogni {args.event_period}s, "
              "ciclica.")

    period = max(args.period, 0.1)
    dt = 1.0 / max(args.rate_hz, 1.0)
    event_notes = list(EVENT_TO_NOTE.values())
    event_idx = 0
    start = time.monotonic()
    next_event = start + args.event_period

    try:
        while True:
            now = time.monotonic()
            t = now - start
            value = _sweep_value(t, period)
            for cc in cc_list:
                midi.send_cc(MIDI_CHANNEL_CC, cc, value)
            if args.with_events and now >= next_event:
                note = event_notes[event_idx % len(event_notes)]
                midi.send_note_on(MIDI_CHANNEL_EVENTS, note, EVENT_VELOCITY)
                midi.send_note_off(MIDI_CHANNEL_EVENTS, note)
                event_idx += 1
                next_event += args.event_period
            time.sleep(dt)
    except KeyboardInterrupt:
        print("\n[sweep] stop.")
    finally:
        midi.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

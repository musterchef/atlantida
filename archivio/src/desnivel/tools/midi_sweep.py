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


def _run_solo(
    midi: "MidoMidiOut",
    period: float,
    rate_hz: float,
    cc_order: list[int] | None = None,
) -> None:
    """Modalita' assistita: un CC alla volta, due INVIO per ognuno.

    Args:
        cc_order: lista ordinata di CC# da scorrere. Se None, usa
            l'ordine di `CHANNEL_TO_CC`. Se un CC# non e' nel bridge,
            viene saltato con un warning.

    Flusso di mappatura SICURO (evita di sovrascrivere il binding
    precedente quando si avanza al CC successivo):

      1. Cmd+M in Ableton -> entri in MIDI Map mode.
      2. INVIO qui -> parte lo sweep del CC corrente.
      3. Click sul knob target in Ableton -> bind fatto.
      4. INVIO qui -> ferma lo sweep (smette di emettere).
      5. Cmd+M in Ableton -> esci dal Map mode (cosi' il knob non
         e' piu' "armato" e il prossimo CC non lo sovrascrive).
      6. INVIO qui -> passa al CC successivo, torna al punto 1.
    """
    import threading

    # Indice inverso: CC# -> address OSC (per stampe leggibili).
    cc_to_addr = {m.cc: addr for addr, m in CHANNEL_TO_CC.items()}

    if cc_order is None:
        items = [(addr, m.cc) for addr, m in CHANNEL_TO_CC.items()]
    else:
        items = []
        for cc in cc_order:
            if cc in cc_to_addr:
                items.append((cc_to_addr[cc], cc))
            else:
                print(f"[sweep --solo] WARN: CC {cc} non e' nel bridge, salto.")
        if not items:
            print("[sweep --solo] nessun CC valido in --cc-list. Esco.")
            midi.close()
            return

    print("\n[sweep --solo] mapping assistito.")
    print(f"Ordine: {[cc for _, cc in items]}")
    print("Per ogni CC: INVIO per partire, mappa, INVIO per fermare,")
    print("esci da Map mode (Cmd+M), INVIO per il prossimo.")
    print("Ctrl+C per uscire.\n")

    period = max(period, 0.1)
    dt = 1.0 / max(rate_hz, 1.0)

    def _prompt(msg: str) -> bool:
        """INVIO -> True. EOF/Ctrl+D -> False (uscita pulita)."""
        try:
            input(msg)
            return True
        except EOFError:
            return False

    try:
        for addr, cc in items:
            print(f"\n--- CC {cc:3d}   ({addr}) ---")
            if not _prompt("  [INVIO per AVVIARE lo sweep] "):
                break

            stop = threading.Event()

            def _emit(cc_num: int = cc) -> None:
                start = time.monotonic()
                while not stop.is_set():
                    t = time.monotonic() - start
                    midi.send_cc(MIDI_CHANNEL_CC, cc_num, _sweep_value(t, period))
                    time.sleep(dt)

            th = threading.Thread(target=_emit, daemon=True)
            th.start()
            ok = _prompt("  [mappa adesso, poi INVIO per FERMARE] ")
            stop.set()
            th.join()
            if not ok:
                break

            if not _prompt("  [esci da Map mode in Ableton, poi INVIO per il prossimo CC] "):
                break
        print("\n[sweep --solo] tutti i CC scorsi. Fine.")
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
    parser.add_argument(
        "--cc-list", type=str, default=None,
        help="Lista ordinata di CC# per --solo, separati da virgola "
             "(es. '25,23,31,30'). Ignorato senza --solo. "
             "I CC non nel bridge vengono saltati con un warning.",
    )
    args = parser.parse_args(argv)

    cc_order: list[int] | None = None
    if args.solo:
        if args.cc_list:
            try:
                cc_order = [int(x.strip()) for x in args.cc_list.split(",")
                            if x.strip()]
            except ValueError as exc:
                parser.error(f"--cc-list malformato: {exc}")

    midi = MidoMidiOut(args.midi_port)
    print(f"[sweep] -> {args.midi_port}")

    if args.solo:
        _run_solo(midi, args.period, args.rate_hz, cc_order=cc_order)
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

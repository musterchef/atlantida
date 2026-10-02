"""Adattatore MDD Snake: nomi dei parametri, range e conversioni.

Funzioni pure: restituiscono liste ``(nome_parametro, valore)``. L'invio
OSC sta nei comandi CLI; la risoluzione nome -> parametro Live sta in M4L.
"""
from __future__ import annotations

import random

STEPS = 16
COLUMNS = 4
NOTE_MIN, NOTE_MAX = 0, 83
VELOCITY_MIN, VELOCITY_MAX = 0, 127

#: Snake quantizza le note sulla propria scala; con Chromatic (0) i valori
#: inviati restano quelli richiesti. Verificato ascoltando.
SCALES_PARAM = "Scales"
SCALE_CHROMATIC = 0

#: Intervalli in semitoni dalla tonica.
SCALES: dict[str, tuple[int, ...]] = {
    "chromatic": tuple(range(12)),
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
}


def param_name(kind: str, step: int) -> str:
    """``param_name("Gate", 1)`` -> ``"Gate_01"``. Step da 1 a 16."""
    if not 1 <= step <= STEPS:
        raise ValueError(f"step fuori da 1..{STEPS}: {step}")
    return f"{kind}_{step:02d}"


def parse_gate_pattern(text: str) -> list[int]:
    """Legge 16 gate da una stringa di 1 e 0.

    Spazi, ``/`` e ``|`` sono separatori ignorati, quindi sono validi
    ``"1000 0100 0010 0001"`` e ``"1000/0100/0010/0001"``.
    Ordine: riga per riga, Gate_01 in alto a sinistra (verificato in Snake).
    """
    bits = [c for c in text if c not in " /|"]
    if len(bits) != STEPS or any(c not in "01" for c in bits):
        raise ValueError(f"servono {STEPS} valori 0/1, ricevuto: {text!r}")
    return [int(c) for c in bits]


def random_gates(density: float, rng: random.Random) -> list[int]:
    """Gate casuali; ``density`` e' la probabilita' (0..1) di un gate acceso."""
    if not 0.0 <= density <= 1.0:
        raise ValueError("density deve essere tra 0 e 1")
    return [1 if rng.random() < density else 0 for _ in range(STEPS)]


def gate_messages(gates: list[int]) -> list[tuple[str, float]]:
    if len(gates) != STEPS:
        raise ValueError(f"servono {STEPS} gate")
    return [(param_name("Gate", i + 1), float(g)) for i, g in enumerate(gates)]


def scale_notes(scale: str, root: int, count: int = STEPS) -> list[int]:
    """Prime ``count`` note ascendenti della scala a partire da ``root``.

    Le note oltre l'ultimo grado salgono di ottava; i valori sono limitati
    al range di Snake. La corrispondenza con le note MIDI emesse resta
    da verificare ascoltando.
    """
    try:
        intervals = SCALES[scale]
    except KeyError:
        raise ValueError(f"scala sconosciuta: {scale}. Disponibili: {', '.join(SCALES)}")
    notes = []
    for i in range(count):
        octave, degree = divmod(i, len(intervals))
        note = root + 12 * octave + intervals[degree]
        notes.append(max(NOTE_MIN, min(NOTE_MAX, note)))
    return notes


def note_messages(notes: list[int]) -> list[tuple[str, float]]:
    """Messaggi per le 16 note, preceduti dal passaggio di Snake a Chromatic."""
    if len(notes) != STEPS:
        raise ValueError(f"servono {STEPS} note")
    return [(SCALES_PARAM, float(SCALE_CHROMATIC))] + [
        (param_name("Note", i + 1), float(n)) for i, n in enumerate(notes)
    ]

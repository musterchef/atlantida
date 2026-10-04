"""Adattatore MDD Snake: nomi dei parametri, range e conversioni.

Funzioni pure: restituiscono liste ``(nome_parametro, valore)``. L'invio
OSC sta nei comandi CLI; la risoluzione nome -> parametro Live sta in M4L.
"""
from __future__ import annotations

import random

from desnivel.music import SCALES, Pattern, scale_notes as musical_scale_notes

ADDRESS = "/desnivel/v1/control/snake/set"
STEPS = 16
COLUMNS = 4
NOTE_MIN, NOTE_MAX = 0, 83
VELOCITY_MIN, VELOCITY_MAX = 0, 127

#: Snake quantizza le note sulla propria scala; con Chromatic (0) i valori
#: inviati restano quelli richiesti. Verificato ascoltando.
SCALES_PARAM = "Scales"
SCALE_CHROMATIC = 0



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
    return [max(NOTE_MIN, min(NOTE_MAX, n))
            for n in musical_scale_notes(scale, root, count)]


def note_messages(notes: list[int]) -> list[tuple[str, float]]:
    """Messaggi per le 16 note, preceduti dal passaggio di Snake a Chromatic."""
    if len(notes) != STEPS:
        raise ValueError(f"servono {STEPS} note")
    return [(SCALES_PARAM, float(SCALE_CHROMATIC))] + [
        (param_name("Note", i + 1), float(n)) for i, n in enumerate(notes)
    ]


def pattern_messages(pattern: Pattern) -> list[tuple[str, float]]:
    """Traduzione del pattern; rifiuta note non rappresentabili da Snake.

    Offset di ottava tra parametro e MIDI emesso ancora da verificare.
    """
    if any(not NOTE_MIN <= n <= NOTE_MAX for n in pattern.notes):
        raise ValueError("Snake supporta valori nota da 0 a 83")
    return note_messages(list(pattern.notes)) + gate_messages(list(pattern.gates))


def section_pattern_messages(changes, rng):
    """Shape Gates casuale una volta per sezione, compresa la prima."""
    previous_section = None
    for change in changes:
        messages = pattern_messages(change.pattern)
        if change.section_index is not None and change.section_index != previous_section:
            messages.append(("gate_shape", float(rng.randint(0, 13))))
            previous_section = change.section_index
        yield change, messages

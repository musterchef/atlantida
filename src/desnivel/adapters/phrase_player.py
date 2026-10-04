"""Protocollo OSC v1 del player M4L, un datagramma per frase."""
import re

from desnivel.phrases import Phrase


def encode(phrase: Phrase, voice: str):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', voice):
        raise ValueError('voice ammette lettere, numeri, trattino e underscore')
    if len(phrase.notes) > 32:
        raise ValueError('il player v1 supporta al massimo 32 note per frase')
    notes = sorted(phrase.notes, key=lambda n: (n.beat, n.pitch))
    ends = {}
    for n in notes:
        if n.beat < ends.get(n.pitch, 0):
            raise ValueError('il player v1 non supporta sovrapposizioni della stessa altezza')
        ends[n.pitch] = n.beat + n.duration
    args = [1, float(phrase.length_beats), len(notes)]
    for n in notes:
        args.extend([float(n.beat), n.pitch, float(n.duration), n.velocity])
    return f'/desnivel/v1/player/{voice}/phrase', args

"""Materiale in gradi ricavato dalla forma normalizzata del percorso."""
import math


def route_motif(shape, span_degrees):
    if type(span_degrees) is not int or not 1 <= span_degrees <= 12:
        raise ValueError('span_degrees deve essere un intero tra 1 e 12')
    if not shape or any(not math.isfinite(value) or not 0 <= value <= 1 for value in shape):
        raise ValueError('forma normalizzata del percorso richiesta in [0, 1]')
    return [int(math.floor(value*span_degrees+.5)) for value in shape]


def validate_motif(degrees):
    if not isinstance(degrees, list) or not degrees or any(type(d) is not int or d < 0 for d in degrees):
        raise ValueError('motif_degrees richiede una lista non vuota di gradi interi non negativi')

"""Contratto dei cambi di parametri del basso, indipendente da OSC e Snake."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math

from desnivel.music.bass.generator import BassSettings

PARAMETERS = frozenset(field.name for field in fields(BassSettings) if field.name != 'strategy')
INTEGER_PARAMETERS = frozenset(('lowest', 'highest', 'seed', 'variation_period'))


@dataclass(frozen=True)
class BassControl:
    serial: int
    settings: BassSettings
    transition_windows: int

    @classmethod
    def from_dict(cls, data, target: BassSettings):
        """Valida tutto il cambio prima di restituirlo; i campi omessi restano invariati."""
        if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
            raise ValueError('versione del controllo basso non supportata')
        if set(data) - {'version', 'serial', 'parameters', 'transition_windows'}:
            raise ValueError('campi del controllo basso sconosciuti')
        serial = data.get('serial')
        if type(serial) is not int or serial < 0:
            raise ValueError('seriale del controllo basso deve essere un intero non negativo')
        windows = data.get('transition_windows', 4)
        if type(windows) is not int or windows < 0:
            raise ValueError('transition_windows deve essere un intero non negativo')
        parameters = data.get('parameters')
        if not isinstance(parameters, dict) or not parameters:
            raise ValueError('parameters deve contenere almeno un controllo')
        unknown = set(parameters) - PARAMETERS
        if unknown:
            raise ValueError('parametri basso sconosciuti: ' + ', '.join(sorted(unknown)))
        for name, value in parameters.items():
            if name in INTEGER_PARAMETERS:
                if type(value) is not int:
                    raise ValueError(name + ' deve essere intero')
            elif type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(name + ' deve essere numerico e finito')
        settings = replace(target, **parameters)
        return cls(serial, settings, windows)

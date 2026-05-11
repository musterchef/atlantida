"""Filtri di smoothing comuni.

Funzioni vettoriali numpy, pure, riusabili dai modulatori. Operano su
una griglia temporale **uniforme**: chi le chiama garantisce che ``dt``
sia costante.
"""
from __future__ import annotations

import numpy as np


def asymmetric_leaky_integrator(
    source: np.ndarray,
    dt: float,
    charge_tau_s: float,
    decay_tau_s: float,
    initial: float = 0.0,
) -> np.ndarray:
    """Integratore con costanti di tempo distinte per carica e scarica.

    Quando ``source`` è sopra l'uscita corrente, l'uscita sale con costante
    ``charge_tau_s``; altrimenti decade con ``decay_tau_s``.
    Modello continuo discretizzato esplicitamente:

        y[n] = y[n-1] + (source[n] - y[n-1]) * (dt / tau)

    dove ``tau`` è scelto in base al segno della differenza.

    Args:
        source: segnale di ingresso.
        dt: passo temporale uniforme in secondi.
        charge_tau_s: costante di tempo (s) quando si sale.
        decay_tau_s: costante di tempo (s) quando si scende.
        initial: valore iniziale dell'uscita.

    Returns:
        Array della stessa lunghezza di ``source``.
    """
    if dt <= 0:
        raise ValueError("dt deve essere positivo")
    if charge_tau_s <= 0 or decay_tau_s <= 0:
        raise ValueError("le costanti di tempo devono essere positive")

    alpha_charge = dt / charge_tau_s
    alpha_decay = dt / decay_tau_s
    out = np.empty_like(source, dtype=float)
    y = float(initial)
    for i, x in enumerate(source):
        alpha = alpha_charge if x > y else alpha_decay
        y = y + (x - y) * alpha
        out[i] = y
    return out

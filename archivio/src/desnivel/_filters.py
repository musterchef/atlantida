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


def _savgol_coeffs(window_length: int, polyorder: int) -> np.ndarray:
    """Coefficienti Savitzky-Golay per il punto centrale della finestra.

    Calcolati via pseudoinversa di Vandermonde: per qualunque
    ``(window_length, polyorder)`` valido restituisce i pesi che, applicati
    in convoluzione, valutano nel punto centrale il polinomio di grado
    ``polyorder`` che meglio approssima ai minimi quadrati i campioni
    della finestra.
    """
    if window_length % 2 == 0:
        raise ValueError("window_length deve essere dispari")
    if window_length < polyorder + 1:
        raise ValueError(
            f"window_length ({window_length}) deve essere > polyorder ({polyorder})"
        )

    half = window_length // 2
    x = np.arange(-half, half + 1, dtype=float)
    # Matrice di Vandermonde A[i, p] = x[i]**p
    A = np.vander(x, polyorder + 1, increasing=True)
    # I coefficienti del filtro per il punto centrale (x = 0) sono la
    # prima riga della pseudoinversa di A.
    return np.linalg.pinv(A)[0]


def savgol_filter(
    data: np.ndarray,
    window_length: int = 5,
    polyorder: int = 2,
) -> np.ndarray:
    """Filtro Savitzky-Golay vettoriale con padding ai bordi.

    Smoothing che preserva i picchi meglio di una mediana o di una EMA:
    fitta localmente un polinomio di grado ``polyorder`` su una finestra
    di ``window_length`` campioni e usa il valore del polinomio al centro.

    Args:
        data: serie 1D campionata su griglia uniforme.
        window_length: lunghezza finestra in campioni (deve essere dispari).
        polyorder: ordine del polinomio locale (tipicamente 2 o 3).

    Returns:
        Array della stessa lunghezza di ``data``.
    """
    arr = np.asarray(data, dtype=float)
    if arr.ndim != 1:
        raise ValueError("savgol_filter accetta solo array 1D")
    if window_length % 2 == 0:
        raise ValueError("window_length deve essere dispari")
    if window_length < 3:
        raise ValueError("window_length deve essere >= 3")
    if arr.size < window_length:
        # Niente da smussare: serie più corta della finestra.
        return arr.copy()

    coeffs = _savgol_coeffs(window_length, polyorder)
    half = window_length // 2
    # Padding "edge": estende il primo/ultimo valore. Evita artefatti di
    # discontinuità ai bordi senza assumere periodicità.
    padded = np.pad(arr, half, mode="edge")
    # Convoluzione con coefficienti rovesciati = correlazione → output
    # allineato al centro della finestra.
    return np.convolve(padded, coeffs[::-1], mode="valid")

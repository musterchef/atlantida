"""Helper condivisi dai detector basati sull'elevazione.

Funzioni pure, niente stato. Concentrano in un solo punto:
- lo smoothing standard dell'elevazione (Savitzky-Golay ~30s);
- l'estrazione sicura di un campione da un canale di un Track.
"""
from __future__ import annotations

import numpy as np

from .._filters import savgol_filter
from ..track import Track

# Finestra di smoothing dell'elevazione: ~30 secondi a 10 Hz.
# Riduce il rumore GPS sull'altimetria barometrica senza alterare la
# forma delle salite/discese (durata >> 30 s).
SMOOTH_WINDOW_S = 30.0


def smooth_elevation(ele: np.ndarray, rate_hz: float) -> np.ndarray:
    """Smussa l'elevazione con savgol su finestra ~30s, polyorder 2.

    Restituisce l'array originale se troppo corto per la finestra:
    chi chiama non deve gestire il caso.
    """
    window = int(SMOOTH_WINDOW_S * rate_hz)
    if window % 2 == 0:
        window += 1
    if window < 3 or ele.size < window:
        return ele
    return savgol_filter(ele, window_length=window, polyorder=2)


def sample_at(track: Track, channel: str, idx: int) -> float | None:
    """Ritorna il valore del canale all'indice indicato, o None se non
    presente o non finito."""
    arr = track.samples.get(channel)
    if arr is None:
        return None
    value = float(arr[idx])
    return value if np.isfinite(value) else None

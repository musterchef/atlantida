"""Ricampionamento dei canali su una griglia temporale uniforme."""
from __future__ import annotations

import numpy as np


def resample_to_uniform_grid(
    elapsed_s: np.ndarray,
    channels: dict[str, np.ndarray],
    rate_hz: float,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Ricampiona linearmente i canali sulla griglia ``[0, T]`` a ``rate_hz``.

    Args:
        elapsed_s: vettore (non necessariamente uniforme) dei tempi sorgente.
        channels: dizionario nome → array. Tutti devono avere la stessa
            lunghezza di ``elapsed_s``.
        rate_hz: frequenza della griglia di destinazione.

    Returns:
        ``(t_uniform, channels_uniform)``. Se ``elapsed_s`` è vuoto o ha
        durata nulla, ritorna ``(elapsed_s, channels)`` invariati.
    """
    if rate_hz <= 0:
        raise ValueError("rate_hz deve essere positivo")
    if elapsed_s.size < 2:
        return elapsed_s, channels

    duration = float(elapsed_s[-1] - elapsed_s[0])
    if duration <= 0:
        return elapsed_s, channels

    n = int(np.floor(duration * rate_hz)) + 1
    t = np.arange(n, dtype=float) / rate_hz
    src_t = elapsed_s - elapsed_s[0]

    out: dict[str, np.ndarray] = {}
    for name, values in channels.items():
        if values.shape != elapsed_s.shape:
            raise ValueError(
                f"Canale '{name}' ha forma {values.shape}, attesa {elapsed_s.shape}",
            )
        out[name] = np.interp(t, src_t, values.astype(float))
    return t, out

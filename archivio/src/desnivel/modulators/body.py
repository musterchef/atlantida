"""Modulatore del corpo ritmico: i canali ``/mod/body/euclid_*``.

Pilota un pattern ritmico euclideo `E(k, n)` lato Ableton:

- `body_euclid_k`  = numero di hit (densita'). Cresce con `journey_energy`.
- `body_euclid_rot` = rotazione del pattern. Avanza con `journey_phase`.

La risoluzione `n` (default 16 step) e' una convenzione fra Python e
Ableton, non un canale OSC.

Mapping:
- `k = round(min_k + energy * (max_k - min_k))`, clip su `[min_k, max_k]`.
- `rot = round(phase * (steps - 1))`, clip su `[0, steps-1]`.

Anti-flicker via `_apply_dwell` riutilizzato dal macro.
"""
from __future__ import annotations

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..modulation import ModulationFrame
from ..track import Track
from .macro import _apply_dwell

_CHANNELS = ("body_euclid_k", "body_euclid_rot")


class BodyModulator:
    """Calcola `body_euclid_k` e `body_euclid_rot` (entrambi int)."""

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    @property
    def output_channels(self) -> tuple[str, ...]:
        return _CHANNELS

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        cfg = self.config.body
        n = track.n_samples

        if n == 0:
            frame.add("body_euclid_k", np.zeros(0, dtype=float))
            frame.add("body_euclid_rot", np.zeros(0, dtype=float))
            return frame

        # Sorgenti (richiedono che Journey abbia girato prima nello stack).
        energy = self._read_unit(frame, cfg.energy_channel, n)
        phase = self._read_unit(frame, cfg.phase_channel, n)

        # k: densita' ritmica scalata in [min_k, max_k].
        k = np.round(cfg.min_k + energy * (cfg.max_k - cfg.min_k)).astype(int)
        k = np.clip(k, cfg.min_k, cfg.max_k)

        # rot: rotazione lungo la fase di tappa, in [0, steps-1].
        rot = np.round(phase * (cfg.steps - 1)).astype(int)
        rot = np.clip(rot, 0, cfg.steps - 1)

        # Anti-flicker.
        rate = self.config.timing.internal_rate_hz
        dwell_n = max(1, int(cfg.dwell_s * rate))
        k = _apply_dwell(k, dwell_n)
        rot = _apply_dwell(rot, dwell_n)

        frame.add("body_euclid_k", k.astype(float))
        frame.add("body_euclid_rot", rot.astype(float))
        return frame

    @staticmethod
    def _read_unit(frame: ModulationFrame, name: str, n: int) -> np.ndarray:
        """Legge un canale in [0,1] dal frame; fallback a 0.5 costante."""
        ch = frame.channels.get(name)
        if ch is None:
            return np.full(n, 0.5)
        arr = np.asarray(ch, dtype=float)
        if arr.size != n:
            return np.full(n, 0.5)
        return np.clip(arr, 0.0, 1.0)


__all__ = ["BodyModulator"]

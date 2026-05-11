"""Modulatore di arco di tappa.

Produce i canali ``/mod/journey/*``:

- ``journey_phase``: avanzamento lineare da 0 a 1 lungo la tappa.
- ``journey_energy``: integratore lentissimo (carica/scarica) sullo
  sforzo accumulato dall'inizio. Indipendente dalla tensione di mesotempo.
- ``journey_openness``: curva narrativa di apertura del sistema, funzione
  combinata di ``phase`` ed ``energy``.

Riferimenti: CONTRATTO-MODULAZIONI.md §2.0, IMPLEMENTAZIONE.md §3.
"""
from __future__ import annotations

import numpy as np

from .._filters import asymmetric_leaky_integrator
from ..config import DEFAULT_CONFIG, Config
from ..modulation import ModulationFrame
from ..track import Track

_CHANNELS = ("journey_phase", "journey_energy", "journey_openness")


class JourneyModulator:
    """Calcola i canali di arco di tappa.

    Attributes:
        config: configurazione del sistema (legge ``timing`` e ``journey``).
    """

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    @property
    def output_channels(self) -> tuple[str, ...]:
        return _CHANNELS

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        phase = self._phase(track)
        energy = self._energy(track)
        openness = self._openness(phase, energy)

        frame.add("journey_phase", phase)
        frame.add("journey_energy", energy)
        frame.add("journey_openness", openness)
        return frame

    # ------------------------------------------------------------------ phase
    def _phase(self, track: Track) -> np.ndarray:
        duration = track.duration_s
        if duration <= 0:
            return np.zeros(track.n_samples, dtype=float)
        return np.clip((track.t - track.t[0]) / duration, 0.0, 1.0)

    # ----------------------------------------------------------------- energy
    def _energy(self, track: Track) -> np.ndarray:
        cfg = self.config.journey
        effort = track.samples.get(cfg.effort_channel)
        if effort is None or track.n_samples == 0:
            return np.zeros(track.n_samples, dtype=float)

        source = np.clip(np.asarray(effort, dtype=float), 0.0, 1.0)
        dt = 1.0 / self.config.timing.internal_rate_hz
        return asymmetric_leaky_integrator(
            source=source,
            dt=dt,
            charge_tau_s=cfg.energy_charge_tau_s,
            decay_tau_s=cfg.energy_decay_tau_s,
        )

    # --------------------------------------------------------------- openness
    def _openness(self, phase: np.ndarray, energy: np.ndarray) -> np.ndarray:
        cfg = self.config.journey
        # Curva narrativa: una base + crescita dolce con la fase + spinta
        # proporzionale all'energia. La fase entra con una smoothstep per
        # avere ingresso e uscita morbidi.
        smooth_phase = phase * phase * (3.0 - 2.0 * phase)
        out = (
            cfg.openness_base
            + cfg.openness_phase_weight * smooth_phase
            + cfg.openness_energy_weight * energy
        )
        return np.clip(out, 0.0, 1.0)

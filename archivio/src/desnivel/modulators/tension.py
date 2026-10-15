"""Modulatore di tensione (scala meso).

Produce il canale ``/mod/meso/tension``: un accumulatore di sforzo a
scala di decine di secondi, complementare a ``journey_energy`` (che vive
sulla scala dei minuti).

La tensione cresce rapidamente quando lo sforzo sale (charge_tau breve)
e decade più lentamente quando lo sforzo cala (decay_tau più lungo):
è il "lingering" tipico di una salita che ti resta nelle gambe ben dopo
il GPM. Asimmetria → memoria emotiva del meso-tempo.

Riferimenti: CONTRATTO-MODULAZIONI.md §2.2, ARCHITETTURA-MUSICALE.md §3 (meso).
"""
from __future__ import annotations

import numpy as np

from .._filters import asymmetric_leaky_integrator
from ..config import DEFAULT_CONFIG, Config
from ..modulation import ModulationFrame
from ..track import Track

_CHANNELS = ("meso_tension",)


class TensionModulator:
    """Calcola il canale ``meso_tension``.

    Distinzione di scala con ``journey_energy``:

    - ``journey_energy``: charge 300s / decay 600s → memoria dell'intera
      tappa.
    - ``meso_tension``: charge 30s / decay 60s → reazione "muscolare"
      di decine di secondi.

    I due canali sono indipendenti: si possono usare insieme in patch
    musicali (uno modula il timbro, l'altro l'intensità del beat).
    """

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    @property
    def output_channels(self) -> tuple[str, ...]:
        return _CHANNELS

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        frame.add("meso_tension", self._tension(track))
        return frame

    def _tension(self, track: Track) -> np.ndarray:
        # Usa lo stesso canale ``effort`` di JourneyModulator: unica
        # fonte di verità sullo sforzo, già normalizzata in [0,1] dal loader.
        cfg_j = self.config.journey
        cfg_s = self.config.smoothing
        effort = track.samples.get(cfg_j.effort_channel)
        if effort is None or track.n_samples == 0:
            return np.zeros(track.n_samples, dtype=float)

        source = np.clip(np.asarray(effort, dtype=float), 0.0, 1.0)
        dt = 1.0 / self.config.timing.internal_rate_hz
        return asymmetric_leaky_integrator(
            source=source,
            dt=dt,
            charge_tau_s=cfg_s.tension_charge_tau_s,
            decay_tau_s=cfg_s.tension_decay_tau_s,
        )

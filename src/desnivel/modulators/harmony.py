"""Modulatore armonico: il canale ``/mod/meso/root``.

Decide la **fondamentale** (tonica) del momento: la nota MIDI attorno
a cui si organizza l'armonia. Cambia ogni `km_per_change` km percorsi,
scorrendo ciclicamente una sequenza modale di offset in semitoni.

Esempio (default):
- Sezione 0: base + 0   -> C
- Sezione 1: base - 2   -> Bb (movimento al ♭VII)
- Sezione 2: base + 5   -> F  (sottodominante)
- Sezione 3: base + 3   -> Eb (mediante minore)
- Sezione 4: base + 7   -> G  (dominante)
- ... e ripete.

Tutto dichiarativo in `HarmonyConfig`: cambiare la "tonalita' del
viaggio" e' una modifica di config, non di codice.

POI override (opzionale): quando si attraversa un POI, la fondamentale
torna alla tonica per dare al luogo un "atterraggio armonico".
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..geo.poi import POIRegistry, load_poi_registry
from ..modulation import ModulationFrame
from ..track import Track
from .macro import _apply_dwell, _poi_mask

_CHANNELS = ("meso_root",)


class HarmonyModulator:
    """Calcola il canale ``meso_root`` (int MIDI, 0..127).

    Args:
        config: configurazione (legge `config.harmony`).
        poi_registry: registry POI esplicito. Se None, viene caricato
            da `config.harmony.poi_registry_path` (None se assente).
    """

    def __init__(
        self,
        config: Config = DEFAULT_CONFIG,
        *,
        poi_registry: POIRegistry | None = None,
    ) -> None:
        self.config = config
        if poi_registry is None and config.harmony.poi_registry_path:
            path = Path(config.harmony.poi_registry_path)
            if path.exists():
                poi_registry = load_poi_registry(path)
        self.poi_registry = poi_registry

    @property
    def output_channels(self) -> tuple[str, ...]:
        return _CHANNELS

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        cfg = self.config.harmony
        n = track.n_samples
        if n == 0 or not cfg.interval_sequence:
            frame.add("meso_root", np.zeros(n, dtype=float))
            return frame

        # 1. Sorgente: distanza cumulata in km.
        cum_m = track.samples.get(cfg.distance_channel)
        if cum_m is None:
            # Fallback: solo tonica per tutta la tappa.
            root = np.full(n, float(np.clip(cfg.base_midi, 0, 127)))
            frame.add("meso_root", root)
            return frame

        cum_km = np.asarray(cum_m, dtype=float) / 1000.0

        # 2. Indice di sezione = floor(km / km_per_change) mod len(sequence).
        seq = np.asarray(cfg.interval_sequence, dtype=int)
        if cfg.km_per_change <= 0:
            section_idx = np.zeros(n, dtype=int)
        else:
            section_idx = (np.floor(cum_km / cfg.km_per_change).astype(int)
                           % len(seq))

        # 3. Lookup -> MIDI note.
        root = (cfg.base_midi + seq[section_idx]).astype(int)

        # 4. POI override: dentro un POI -> tonica.
        if cfg.poi_force_tonic and self.poi_registry is not None and len(self.poi_registry) > 0:
            mask = _poi_mask(track, self.poi_registry)
            if mask.any():
                root = np.where(mask, cfg.base_midi, root)

        # 5. Anti-flicker (riusa `_apply_dwell` dal macro).
        rate = self.config.timing.internal_rate_hz
        dwell_n = max(1, int(cfg.min_dwell_s * rate))
        root = _apply_dwell(root, dwell_n)

        # 6. Clip al range MIDI valido.
        root = np.clip(root, 0, 127)

        frame.add("meso_root", root.astype(float))
        return frame


__all__ = ["HarmonyModulator"]

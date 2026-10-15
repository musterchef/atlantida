"""Frame delle modulazioni continue.

Contenitore dei canali ``/mod/*`` lungo l'asse temporale della tappa.
I modulatori vi aggiungono colonne in modo cumulativo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import csv

import numpy as np


@dataclass
class ModulationFrame:
    """Insieme dei canali continui di modulazione lungo il tempo.

    Tutti i canali condividono lo stesso asse temporale ``t``.
    """

    t: np.ndarray
    channels: dict[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, values in self.channels.items():
            self._check_shape(name, values)

    def _check_shape(self, name: str, values: np.ndarray) -> None:
        if len(values) != len(self.t):
            raise ValueError(
                f"Canale '{name}' ha lunghezza {len(values)}, attesa {len(self.t)}",
            )

    def add(self, name: str, values: np.ndarray) -> None:
        """Aggiunge un canale al frame."""
        if name in self.channels:
            raise KeyError(f"Canale '{name}' già presente")
        self._check_shape(name, values)
        self.channels[name] = np.asarray(values)

    def update(self, mapping: Mapping[str, np.ndarray]) -> None:
        for name, values in mapping.items():
            self.add(name, values)

    @property
    def n_samples(self) -> int:
        return int(len(self.t))

    @property
    def channel_names(self) -> tuple[str, ...]:
        return tuple(self.channels.keys())

    def to_csv(self, path: str | Path) -> None:
        """Scrive il frame in CSV con colonne ``t`` + canali."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        names = ["t", *self.channel_names]
        columns = [self.t, *(self.channels[n] for n in self.channel_names)]
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(names)
            for row in zip(*columns):
                writer.writerow(row)

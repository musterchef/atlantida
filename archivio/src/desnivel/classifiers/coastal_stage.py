"""Classifier `coastal_stage`: marca `start`/`end` quando la tappa, nel suo
insieme, e' una tappa di mare (in riva, non panoramica).

Triggera quando la **mediana** della distanza dalla costa lungo la
tappa e' sotto soglia ``EventConfig.coastal_stage_max_median_m``
(default 1000 m). La mediana e' robusta agli outlier: ignora i
pochi punti che si allontanano (es. l'arrivo 1.5 km nell'entroterra
di Mattinata) e privilegia il *tempo* speso in costa.

Aggiunge la variante "coastal" — la stessa di ``CoastalClassifier``:
le varianti si fondono senza duplicati e il payload riceve i campi
aggiuntivi ``coast_median_m`` / ``coast_below_fraction_1000``.

Vedi CONTRATTO-MODULAZIONI.md 3.1.1.
"""
from __future__ import annotations

from typing import Any, Mapping

from ..config import DEFAULT_CONFIG, Config
from ..events import Event
from ..geo.coast_stats import coast_stats_for
from ..geo.coastline import CoastlineProvider, get_default_coastline
from ..track import Track


class CoastalStageClassifier:
    """Marca `start`/`end` come `coastal` se la tappa intera e' costiera."""

    applies_to_kinds: tuple[str, ...] | None = ("start", "end")

    def __init__(
        self,
        config: Config = DEFAULT_CONFIG,
        coastline: CoastlineProvider | None = None,
    ) -> None:
        self.config = config
        self._coastline = coastline

    def _get_coastline(self) -> CoastlineProvider:
        if self._coastline is None:
            self._coastline = get_default_coastline(
                bbox=self.config.geo.coastline_bbox,
            )
        return self._coastline

    def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
        stats = coast_stats_for(track, self._get_coastline())
        if stats is None:
            return {}
        if stats.median_m >= self.config.events.coastal_stage_max_median_m:
            return {}
        return {
            "variants": ["coastal"],
            "coast_median_m": stats.median_m,
            "coast_below_fraction_1000": stats.below_fraction_1000,
        }

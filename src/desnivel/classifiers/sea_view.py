"""Classifier `sea_view`: marca `start`/`end` quando la tappa e' panoramica
sul mare (in alto, vista mare, non in spiaggia).

Caso d'uso paradigmatico: Cinque Terre. Pedalata di crinale a 300-550 m
di quota, 1-3 km in linea d'aria dalla costa: il mare e' sempre li'
sotto ma non sei "in riva". Diverso musicalmente da `coastal`: piu'
arioso, verticale, paesaggistico.

Criteri (tutti necessari):
- mediana distanza costa < ``coastal_view_max_median_m`` (default 5 km);
- mediana quota >= ``coastal_view_min_ele_median_m`` (default 150 m);
- quota max >= ``coastal_view_min_ele_max_m`` (default 250 m).

Le ultime due distinguono il caso "pianura costiera" (Sabaudia: bassa
quota, vicino al mare, gia' coperto da `coastal`) dal caso "panoramica"
(Cinque Terre, parte di Genova-Levanto).

`coastal` e `sea_view` possono coesistere sullo stesso `end` quando una
tappa cambia carattere (Genova-Levanto: prima alta-via, poi giu' al
porto). La pipeline fonde le varianti come unione.

Vedi CONTRATTO-MODULAZIONI.md 3.1.1.
"""
from __future__ import annotations

from typing import Any, Mapping

from ..config import DEFAULT_CONFIG, Config
from ..events import Event
from ..geo.coast_stats import coast_stats_for
from ..geo.coastline import CoastlineProvider, get_default_coastline
from ..track import Track


class SeaViewClassifier:
    """Marca `start`/`end` come `sea_view` se la tappa e' panoramica sul mare."""

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
        cfg = self.config.events
        if stats.median_m >= cfg.coastal_view_max_median_m:
            return {}
        if stats.ele_median_m < cfg.coastal_view_min_ele_median_m:
            return {}
        if stats.ele_max_m < cfg.coastal_view_min_ele_max_m:
            return {}
        return {
            "variants": ["sea_view"],
            "coast_median_m": stats.median_m,
            "ele_median_m": stats.ele_median_m,
            "ele_max_m": stats.ele_max_m,
        }

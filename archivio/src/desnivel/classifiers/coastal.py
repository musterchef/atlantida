"""Classifier `coastal`: marca `start`/`end` come framing in riva al mare.

Aggiunge la variante "coastal" al payload di un `start` o `end` quando
la posizione di apertura/chiusura e' entro
``EventConfig.coastal_arrival_threshold_m`` dalla costa. E' la
versione **puntuale**: guarda solo il singolo campione di start/end,
non l'andamento della tappa intera.

Per il carattere "tappa di mare" (tipo Peschici-Mattinata che finisce
1.5 km nell'entroterra ma costeggia per il 60% del tempo) vedi
`CoastalStageClassifier`. Le due varianti sono **la stessa**
("coastal"): chi guarda il payload non distingue da quale classifier
sia stata aggiunta, semplicemente sa che la tappa ha quel carattere.

Vedi CONTRATTO-MODULAZIONI.md 3.1.1.
"""
from __future__ import annotations

from typing import Any, Mapping

from ..config import DEFAULT_CONFIG, Config
from ..events import Event
from ..geo.coastline import CoastlineProvider, get_default_coastline
from ..track import Track


class CoastalClassifier:
    """Marca `start`/`end` come `coastal` se il punto e' vicino alla costa."""

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
        loc = event.location
        if loc is None:
            return {}
        coast = self._get_coastline()
        distance = float(coast.distance_m(loc.lat, loc.lon))
        if distance >= self.config.events.coastal_arrival_threshold_m:
            return {}
        return {
            "variants": ["coastal"],
            "coast_distance_m": distance,
        }

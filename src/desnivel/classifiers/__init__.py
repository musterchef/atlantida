"""Classificatori pluggabili per arricchire il payload degli eventi.

Vedi `base.EventClassifier` e CONTRATTO-MODULAZIONI.md §3.1.1.
"""
from .arrival_climb import ArrivalClimbClassifier
from .base import EventClassifier
from .coastal import CoastalClassifier
from .coastal_stage import CoastalStageClassifier
from .sea_view import SeaViewClassifier

__all__ = [
    "EventClassifier",
    "ArrivalClimbClassifier",
    "CoastalClassifier",
    "CoastalStageClassifier",
    "SeaViewClassifier",
]

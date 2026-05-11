"""Classificatori pluggabili per arricchire il payload degli eventi.

Vedi `base.EventClassifier` e CONTRATTO-MODULAZIONI.md §3.1.1.
"""
from .arrival_climb import ArrivalClimbClassifier
from .base import EventClassifier

__all__ = ["EventClassifier", "ArrivalClimbClassifier"]

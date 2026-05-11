"""Rilevatori di eventi (derivati dai dati o esterni)."""
from .arrival_climb import ArrivalClimbDetector
from .base import EventDetector
from .summit import SummitDetector

__all__ = ["EventDetector", "SummitDetector", "ArrivalClimbDetector"]

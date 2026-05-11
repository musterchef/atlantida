"""Rilevatori di eventi (derivati dai dati o esterni)."""
from .base import EventDetector
from .bookends import EndDetector, StartDetector
from .summit import SummitDetector

__all__ = ["EventDetector", "StartDetector", "EndDetector", "SummitDetector"]

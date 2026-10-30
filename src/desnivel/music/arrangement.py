"""Assegnazioni manuali delle voci nelle sezioni."""
from dataclasses import dataclass, field
import math
from typing import Mapping


@dataclass(frozen=True)
class Assignment:
    role: str
    parameters: Mapping = field(default_factory=dict)
    presence: float = 1.

    def __post_init__(self):
        if (type(self.presence) not in (int, float) or not math.isfinite(self.presence)
                or not 0 <= self.presence <= 1):
            raise ValueError('presence deve essere un numero tra 0 e 1')

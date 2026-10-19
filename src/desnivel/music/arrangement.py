"""Assegnazioni manuali delle voci nelle sezioni."""
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Assignment:
    role: str
    parameters: Mapping = field(default_factory=dict)

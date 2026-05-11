"""Helper geometrici (costa, future feature spaziali)."""
from .coastline import (
    Coastline,
    CoastlineProvider,
    default_coastline_path,
    get_default_coastline,
)

__all__ = [
    "Coastline",
    "CoastlineProvider",
    "default_coastline_path",
    "get_default_coastline",
]

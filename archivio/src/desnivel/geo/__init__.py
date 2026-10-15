"""Helper geometrici (costa, POI, future feature spaziali)."""
from .coastline import (
    Coastline,
    CoastlineProvider,
    default_coastline_path,
    get_default_coastline,
)
from .poi import (
    POI,
    POIRegistry,
    default_poi_path,
    get_default_registry,
    load_poi_registry,
)

__all__ = [
    "Coastline",
    "CoastlineProvider",
    "default_coastline_path",
    "get_default_coastline",
    "POI",
    "POIRegistry",
    "default_poi_path",
    "get_default_registry",
    "load_poi_registry",
]

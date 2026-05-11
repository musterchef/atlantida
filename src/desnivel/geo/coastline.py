"""Distanza dalla costa.

Wrapper sottile attorno a shapely + pyshp: carica il shapefile Natural
Earth `ne_10m_coastline.shp`, clippa al bounding box di interesse,
fa l'unione e prepara la geometria per query ripetute.

Il modulo espone:

- `CoastlineProvider`: Protocol che fornisce `distance_m(lat, lon)` e
  `distances_m(lats, lons)` — interfaccia minima per detector/classifier.
  Permette di iniettare fake nei test senza shapely.
- `Coastline`: implementazione concreta basata su shapely 2.
- `get_default_coastline(config)`: singleton cache, carica una volta sola.

Dipendenze: ``shapely>=2.0`` e ``pyshp>=2.3`` (opzionale ``[geo]`` in
``pyproject.toml``). L'import e' lazy: il modulo si importa anche senza
le librerie installate, ma istanziare `Coastline` solleva ``ImportError``.

Conversione gradi -> metri: l'unione clippata della costa e' in WGS84,
quindi `nearest_points` ritorna un punto in lat/lon. La distanza vera
in metri si calcola con haversine sui due punti, evitando gli errori
dell'approssimazione lineare gradi->km.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np


_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distanza ortodromica in metri fra due punti WGS84."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2.0) ** 2
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


@runtime_checkable
class CoastlineProvider(Protocol):
    """Interfaccia minima per detector/classifier che usano la costa.

    I detector lavorano in metri, quindi questa e' l'unica API che serve.
    Implementazioni reali (`Coastline`) usano shapely; i test usano fake
    con distanze pre-calcolate.
    """

    def distance_m(self, lat: float, lon: float) -> float: ...

    def distances_m(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray: ...


def default_coastline_path() -> Path:
    """Path predefinito allo shapefile Natural Earth nel repo."""
    # `geo/coastline.py` -> repo_root/data/coastline/...
    return (
        Path(__file__).resolve().parents[3]
        / "data" / "coastline" / "ne_10m_coastline.shp"
    )


class Coastline:
    """Costa caricata da shapefile, con distanze in metri.

    Args:
        shp_path: percorso allo shapefile (`.shp`).
        bbox: bounding box (lon_min, lat_min, lon_max, lat_max) per clip.
            Riduce drasticamente il numero di segmenti.

    Raises:
        ImportError: se `shapely` o `pyshp` non sono installati.
        FileNotFoundError: se lo shapefile manca.
    """

    def __init__(
        self,
        shp_path: Path | str | None = None,
        bbox: tuple[float, float, float, float] = (6.0, 36.0, 19.0, 48.0),
    ) -> None:
        try:
            import shapefile as _shapefile  # pyshp
            from shapely import prepare
            from shapely.geometry import LineString, box
            from shapely.ops import unary_union
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Coastline richiede le dipendenze opzionali [geo]: "
                "pip install -e .[geo]"
            ) from exc

        path = Path(shp_path) if shp_path is not None else default_coastline_path()
        if not path.exists():
            raise FileNotFoundError(f"Coastline shapefile non trovato: {path}")

        clip_box = box(*bbox)
        sf = _shapefile.Reader(str(path))
        lines: list = []
        for sr in sf.shapeRecords():
            coords = sr.shape.points
            if not coords:
                continue
            line = LineString(coords)
            if line.intersects(clip_box):
                clipped = line.intersection(clip_box)
                if not clipped.is_empty:
                    lines.append(clipped)

        self._geom = unary_union(lines)
        prepare(self._geom)
        self._n_segments = len(lines)

    @property
    def n_segments(self) -> int:
        return self._n_segments

    def distance_m(self, lat: float, lon: float) -> float:
        """Distanza in metri dal punto (lat, lon) alla costa piu' vicina."""
        from shapely.geometry import Point
        from shapely.ops import nearest_points

        pt = Point(float(lon), float(lat))
        _, nearest = nearest_points(pt, self._geom)
        return haversine_m(lat, lon, float(nearest.y), float(nearest.x))

    def distances_m(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """Distanze in metri per array di punti. Vettoriale solo nel ciclo
        di `nearest_points`; haversine batch numpy sui risultati."""
        from shapely.geometry import Point
        from shapely.ops import nearest_points

        lats = np.asarray(lats, dtype=float)
        lons = np.asarray(lons, dtype=float)
        if lats.shape != lons.shape:
            raise ValueError("lats e lons devono avere la stessa shape")

        nearest_lat = np.empty_like(lats)
        nearest_lon = np.empty_like(lats)
        flat_lats = lats.ravel()
        flat_lons = lons.ravel()
        flat_nlat = nearest_lat.ravel()
        flat_nlon = nearest_lon.ravel()
        for i in range(flat_lats.size):
            pt = Point(float(flat_lons[i]), float(flat_lats[i]))
            _, nearest = nearest_points(pt, self._geom)
            flat_nlat[i] = float(nearest.y)
            flat_nlon[i] = float(nearest.x)

        # Haversine vettoriale.
        phi1 = np.radians(lats)
        phi2 = np.radians(nearest_lat)
        dphi = phi2 - phi1
        dlmb = np.radians(nearest_lon - lons)
        a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2.0) ** 2
        return 2.0 * _EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


@lru_cache(maxsize=4)
def _cached_coastline(shp_path: str, bbox: tuple[float, float, float, float]) -> Coastline:
    return Coastline(shp_path=shp_path, bbox=bbox)


def get_default_coastline(
    bbox: tuple[float, float, float, float] = (6.0, 36.0, 19.0, 48.0),
    shp_path: Path | str | None = None,
) -> Coastline:
    """Ritorna un'istanza condivisa di `Coastline` (cache per shp+bbox).

    Le CLI passano `bbox` da `Config.geo.coastline_bbox`. Test e codice
    custom possono creare istanze dirette con `Coastline(...)` senza
    cache.
    """
    path = Path(shp_path) if shp_path is not None else default_coastline_path()
    return _cached_coastline(str(path), bbox)

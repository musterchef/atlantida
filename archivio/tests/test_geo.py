"""Test per `geo.coastline.haversine_m` e per il path di default.

Lo shapefile non viene caricato qui (lo fa un test smoke separato se
necessario). Test usano solo funzioni pure.
"""
from __future__ import annotations

import pytest

from desnivel.geo.coastline import default_coastline_path, haversine_m


def test_haversine_zero_distance():
    assert haversine_m(45.0, 9.0, 45.0, 9.0) == pytest.approx(0.0)


def test_haversine_known_distance():
    # Roma -> Milano: ~477 km in linea d'aria
    d = haversine_m(41.9028, 12.4964, 45.4642, 9.1900)
    assert d == pytest.approx(477_000.0, rel=0.02)


def test_haversine_short_distance():
    # 1 km in latitudine ≈ 0.00899 gradi (1° ~ 111.2 km)
    d = haversine_m(44.0, 10.0, 44.0 + 0.00899, 10.0)
    assert d == pytest.approx(1000.0, rel=0.01)


def test_default_coastline_path_inside_repo():
    p = default_coastline_path()
    assert p.name == "ne_10m_coastline.shp"
    assert "data" in p.parts

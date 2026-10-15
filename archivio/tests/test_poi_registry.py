"""Test per `POIRegistry` e `load_poi_registry`."""
from __future__ import annotations

import json

import pytest

from desnivel.geo.poi import POI, POIRegistry, load_poi_registry


def _registry() -> POIRegistry:
    return POIRegistry([
        POI(name="San Gimignano", lat=43.4677, lon=11.0431, radius_m=1200.0,
            kind="town", tags=("medieval",)),
        POI(name="Roma", lat=41.9028, lon=12.4964, radius_m=8000.0, kind="city"),
        POI(name="Vaticano", lat=41.9029, lon=12.4534, radius_m=400.0,
            kind="landmark"),
    ])


def test_empty_registry():
    r = POIRegistry([])
    assert len(r) == 0
    assert r.nearest(0.0, 0.0) is None
    assert r.inside_indices(0.0, 0.0) == []


def test_nearest_returns_closest():
    r = _registry()
    poi, d = r.nearest(43.467, 11.043)
    assert poi.name == "San Gimignano"
    assert d < 200.0


def test_inside_indices_handles_overlapping_pois():
    """Il Vaticano è dentro Roma: query al Vaticano colpisce entrambi."""
    r = _registry()
    idxs = r.inside_indices(41.9029, 12.4534)
    names = {r.pois[i].name for i in idxs}
    assert names == {"Roma", "Vaticano"}


def test_inside_indices_empty_when_far():
    r = _registry()
    assert r.inside_indices(60.0, 10.0) == []


def test_load_from_json(tmp_path):
    path = tmp_path / "poi.json"
    path.write_text(json.dumps([
        {"name": "X", "lat": 45.0, "lon": 9.0, "radius_m": 500.0,
         "kind": "town", "tags": ["alpine"]},
        {"name": "Y", "lat": 46.0, "lon": 10.0, "radius_m": 300.0},
    ]), encoding="utf-8")
    r = load_poi_registry(path)
    assert len(r) == 2
    assert r.pois[0].kind == "town"
    assert r.pois[0].tags == ("alpine",)
    assert r.pois[1].kind == "poi"  # default
    assert r.pois[1].tags == ()


def test_load_missing_file_returns_empty(tmp_path):
    r = load_poi_registry(tmp_path / "nope.json")
    assert len(r) == 0

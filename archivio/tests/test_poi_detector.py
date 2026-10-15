"""Test per `POIDetector` con registry in-memory."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import POIDetector
from desnivel.events import EventCategory
from desnivel.geo.poi import POI, POIRegistry
from desnivel.track import Track


RATE_HZ = 10.0


def _track_along_lon(lons: np.ndarray, lat: float = 43.0) -> Track:
    """Track con `lon` variabile e `lat` costante (semplice da pilotare)."""
    n = lons.size
    t = np.arange(n, dtype=float) / RATE_HZ
    return Track(
        stage_id="test",
        t=t,
        samples={
            "lat": np.full(n, lat),
            "lon": lons,
            "ele": np.zeros(n),
        },
        metadata={},
    )


# Un POI a (lat=43.0, lon=11.0), raggio ~1.2 km. A questa latitudine
# 1 grado di longitudine ≈ 81.3 km, quindi 0.01° ≈ 813 m.
_POI_A = POI(name="A", lat=43.0, lon=11.0, radius_m=1200.0, kind="town")
_POI_B = POI(name="B", lat=43.0, lon=12.0, radius_m=500.0, kind="landmark",
             tags=("medieval",))


def test_no_registry_no_events():
    det = POIDetector(DEFAULT_CONFIG, registry=POIRegistry([]))
    track = _track_along_lon(np.linspace(10.0, 13.0, 600))
    assert list(det.detect(track)) == []


def test_single_entry_emits_one_event():
    """Traccia che attraversa POI A da fuori a fuori: un solo evento."""
    det = POIDetector(DEFAULT_CONFIG, registry=POIRegistry([_POI_A]))
    track = _track_along_lon(np.linspace(10.9, 11.1, 6000))
    events = list(det.detect(track))
    assert len(events) == 1
    assert events[0].kind == "poi"
    assert events[0].category == EventCategory.MAJOR
    assert events[0].payload["name"] == "A"
    assert events[0].payload["kind"] == "town"


def test_multiple_pois_emitted_in_order():
    det = POIDetector(DEFAULT_CONFIG, registry=POIRegistry([_POI_A, _POI_B]))
    track = _track_along_lon(np.linspace(10.9, 12.1, 12000))
    events = list(det.detect(track))
    names = [e.payload["name"] for e in events]
    assert names == ["A", "B"]
    assert events[1].payload["tags"] == ["medieval"]


def test_reentry_within_cooldown_suppressed():
    """Esci e rientra dentro il cooldown: niente secondo evento."""
    config = DEFAULT_CONFIG
    det = POIDetector(config, registry=POIRegistry([_POI_A]))
    # Traiettoria: dentro, fuori (per 60 s), dentro. Cooldown default 3600s.
    n = 6000  # 600 s = 10 min
    lons = np.concatenate([
        np.full(n // 3, 11.0),    # dentro
        np.full(n // 3, 11.05),   # fuori (~4 km)
        np.full(n // 3, 11.0),    # dentro
    ])
    track = _track_along_lon(lons)
    events = list(det.detect(track))
    assert len(events) == 1


def test_reentry_after_cooldown_emits_again():
    """Cooldown corto: la seconda entrata emette."""
    from desnivel.config import EventConfig, Config

    short_cd = Config(events=EventConfig(poi_reentry_cooldown_s=10.0))
    det = POIDetector(short_cd, registry=POIRegistry([_POI_A]))
    # Tre minuti: dentro 60s, fuori 60s, dentro 60s.
    n_chunk = int(60 * RATE_HZ)
    lons = np.concatenate([
        np.full(n_chunk, 11.0),
        np.full(n_chunk, 11.05),
        np.full(n_chunk, 11.0),
    ])
    track = _track_along_lon(lons)
    events = list(det.detect(track))
    assert len(events) == 2


def test_overlapping_pois_both_emit():
    """POI nidificati (B dentro A): entrando si attivano entrambi."""
    big = POI(name="Big", lat=43.0, lon=11.0, radius_m=5000.0, kind="city")
    small = POI(name="Small", lat=43.0, lon=11.0, radius_m=300.0,
                kind="landmark")
    det = POIDetector(DEFAULT_CONFIG, registry=POIRegistry([big, small]))
    track = _track_along_lon(np.linspace(10.9, 11.0, 6000))
    events = list(det.detect(track))
    names = {e.payload["name"] for e in events}
    assert names == {"Big", "Small"}


def test_track_starting_inside_emits_at_first_sample():
    det = POIDetector(DEFAULT_CONFIG, registry=POIRegistry([_POI_A]))
    track = _track_along_lon(np.full(600, 11.0))  # tutto dentro
    events = list(det.detect(track))
    assert len(events) == 1
    assert events[0].t == 0.0

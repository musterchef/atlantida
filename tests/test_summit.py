"""Test per ``SummitDetector``."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import SummitDetector
from desnivel.events import EventCategory
from desnivel.track import Track


RATE_HZ = 10.0


def _make_track(ele: np.ndarray, lat: np.ndarray | None = None, lon: np.ndarray | None = None) -> Track:
    n = len(ele)
    t = np.arange(n, dtype=float) / RATE_HZ
    samples: dict[str, np.ndarray] = {"ele": ele}
    if lat is not None:
        samples["lat"] = lat
    if lon is not None:
        samples["lon"] = lon
    return Track(stage_id="test", t=t, samples=samples, metadata={})


def _bump(n: int, center: int, height: float, width: int) -> np.ndarray:
    """Profilo gaussiano per simulare una salita-discesa con vetta."""
    x = np.arange(n, dtype=float)
    return height * np.exp(-0.5 * ((x - center) / width) ** 2)


def test_summit_detected_on_clear_peak():
    """Vetta di 200m molto pronunciata: viene emessa."""
    # 60 min a 10 Hz, vetta al centro alta 200m sopra base.
    n = 60 * 60 * int(RATE_HZ)
    ele = 100.0 + _bump(n, center=n // 2, height=200.0, width=int(5 * 60 * RATE_HZ))
    track = _make_track(ele)
    events = list(SummitDetector(DEFAULT_CONFIG).detect(track))
    assert len(events) == 1
    e = events[0]
    assert e.kind == "summit"
    assert e.category is EventCategory.MAJOR
    # Vetta a metà tappa, tolleranza ampia per lo smoothing.
    midpoint_s = (n - 1) / RATE_HZ / 2
    assert abs(e.t - midpoint_s) < 30
    assert e.payload["ele_m"] == pytest.approx(300.0, abs=2.0)
    assert e.payload["prominence_m"] > 150.0
    assert e.source_id == "gpx_auto"


def test_summit_not_detected_if_low_prominence():
    """Vetta di 20m: sotto soglia (50m), niente evento."""
    n = 30 * 60 * int(RATE_HZ)
    ele = 100.0 + _bump(n, center=n // 2, height=20.0, width=int(3 * 60 * RATE_HZ))
    track = _make_track(ele)
    events = list(SummitDetector(DEFAULT_CONFIG).detect(track))
    assert events == []


def test_summit_not_detected_on_monotonic_climb():
    """Salita continua (vetta al bordo, prominenza zero su un lato): niente."""
    n = 30 * 60 * int(RATE_HZ)
    ele = np.linspace(0.0, 500.0, n)  # massimo sul bordo destro
    track = _make_track(ele)
    events = list(SummitDetector(DEFAULT_CONFIG).detect(track))
    assert events == []


def test_summit_returns_empty_without_elevation():
    """Track senza canale ``ele``: niente evento, niente errore."""
    n = 100
    track = Track(
        stage_id="t",
        t=np.arange(n) / RATE_HZ,
        samples={},
        metadata={},
    )
    assert list(SummitDetector(DEFAULT_CONFIG).detect(track)) == []


def test_summit_includes_location_when_available():
    """Se ci sono lat/lon, l'evento include la GeoPoint del picco."""
    n = 30 * 60 * int(RATE_HZ)
    ele = 100.0 + _bump(n, center=n // 2, height=200.0, width=int(5 * 60 * RATE_HZ))
    lat = np.linspace(45.0, 46.0, n)
    lon = np.linspace(7.0, 8.0, n)
    track = _make_track(ele, lat=lat, lon=lon)
    e = list(SummitDetector(DEFAULT_CONFIG).detect(track))[0]
    assert e.location is not None
    assert 45.0 <= e.location.lat <= 46.0
    assert 7.0 <= e.location.lon <= 8.0
    assert e.location.ele is not None


def test_summit_picks_highest_when_multiple_peaks():
    """Due picchi: viene scelto solo il più alto (max globale)."""
    n = 60 * 60 * int(RATE_HZ)
    ele = (
        100.0
        + _bump(n, center=n // 4, height=100.0, width=int(2 * 60 * RATE_HZ))
        + _bump(n, center=3 * n // 4, height=200.0, width=int(2 * 60 * RATE_HZ))
    )
    track = _make_track(ele)
    events = list(SummitDetector(DEFAULT_CONFIG).detect(track))
    assert len(events) == 1
    # Il picco maggiore è a 3/4 della tappa.
    assert events[0].t > (n / RATE_HZ) * 0.6

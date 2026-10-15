"""Test per `CoastalStageClassifier` e `SeaViewClassifier`."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.classifiers import CoastalStageClassifier, SeaViewClassifier
from desnivel.config import DEFAULT_CONFIG
from desnivel.events import Event, EventCategory
from desnivel.geo import coast_stats as _coast_stats_mod
from desnivel.track import GeoPoint, Track


RATE_HZ = 10.0


@pytest.fixture(autouse=True)
def _clear_coast_stats_cache():
    _coast_stats_mod._CACHE.clear()
    _coast_stats_mod._CACHE_ORDER.clear()
    yield
    _coast_stats_mod._CACHE.clear()
    _coast_stats_mod._CACHE_ORDER.clear()


class _ProfileCoastline:
    """Fake che ritorna distanze = lat * scale (per pilotare facilmente)."""

    def __init__(self, scale: float = 1000.0) -> None:
        self._k = scale

    def distance_m(self, lat: float, lon: float) -> float:
        return float(lat) * self._k

    def distances_m(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        return np.asarray(lats, dtype=float) * self._k


def _make_track(distances_m: np.ndarray, ele: np.ndarray | None = None) -> Track:
    n = distances_m.size
    t = np.arange(n, dtype=float) / RATE_HZ
    lats = distances_m / 1000.0
    lons = np.full(n, 10.0)
    samples = {"lat": lats, "lon": lons}
    if ele is not None:
        samples["ele"] = ele
    return Track(stage_id="test", t=t, samples=samples, metadata={})


def _end_event(track: Track) -> Event:
    last = track.n_samples - 1
    return Event(
        kind="end",
        category=EventCategory.MAJOR,
        t=float(track.t[last]),
        location=GeoPoint(
            lat=float(track.samples["lat"][last]),
            lon=float(track.samples["lon"][last]),
            ele=0.0,
        ),
        payload={"variants": []},
        source_id="gpx_auto",
    )


# ──────────────────── CoastalStageClassifier ────────────────────


def test_coastal_stage_marks_when_median_below_threshold():
    """Tappa con mediana 340 m (Peschici-Mattinata sintetica)."""
    n = 600 * int(RATE_HZ)  # 10 min
    # 60% sotto 500m, 40% sopra
    d = np.concatenate([
        np.full(int(n * 0.6), 340.0),
        np.full(n - int(n * 0.6), 2000.0),
    ])
    track = _make_track(d)
    out = CoastalStageClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out["variants"] == ["coastal"]
    assert out["coast_median_m"] < 1000.0
    assert 0.5 < out["coast_below_fraction_1000"] < 0.7


def test_coastal_stage_skips_when_median_above_threshold():
    """Tappa con start/end vicini al mare ma interno: niente coastal_stage."""
    n = 600 * int(RATE_HZ)
    # 80% lontano dalla costa, 20% vicino (Roma-Sabaudia)
    d = np.concatenate([
        np.full(int(n * 0.8), 15000.0),
        np.full(n - int(n * 0.8), 500.0),
    ])
    track = _make_track(d)
    out = CoastalStageClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out == {}


def test_coastal_stage_applies_to_start_and_end():
    assert CoastalStageClassifier.applies_to_kinds == ("start", "end")


# ──────────────────── SeaViewClassifier ─────────────────────────


def test_sea_view_marks_panoramic_stage():
    """Cinque Terre sintetiche: mediana ~1500m, quote ~300m."""
    n = 600 * int(RATE_HZ)
    d = np.full(n, 1500.0)   # 1.5 km dalla costa
    ele = np.linspace(100.0, 500.0, n)  # quota 100-500m, mediana ~300
    track = _make_track(d, ele=ele)
    out = SeaViewClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out["variants"] == ["sea_view"]
    assert out["ele_median_m"] == pytest.approx(300.0, abs=10.0)
    assert out["ele_max_m"] >= 250.0


def test_sea_view_skips_low_elevation_coastal_stage():
    """Sabaudia-style: vicino al mare, bassa quota: NIENTE sea_view."""
    n = 600 * int(RATE_HZ)
    d = np.full(n, 400.0)
    ele = np.full(n, 5.0)   # in spiaggia
    track = _make_track(d, ele=ele)
    out = SeaViewClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out == {}


def test_sea_view_skips_when_far_from_coast():
    """Quote alte ma lontano dalla costa (Appennino interno): no."""
    n = 600 * int(RATE_HZ)
    d = np.full(n, 30000.0)   # 30 km dalla costa
    ele = np.full(n, 500.0)
    track = _make_track(d, ele=ele)
    out = SeaViewClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out == {}


def test_sea_view_skips_without_elevation():
    n = 600 * int(RATE_HZ)
    d = np.full(n, 1500.0)
    track = _make_track(d, ele=None)
    out = SeaViewClassifier(
        DEFAULT_CONFIG, coastline=_ProfileCoastline(),
    ).classify(_end_event(track), track)
    assert out == {}


def test_sea_view_applies_to_start_and_end():
    assert SeaViewClassifier.applies_to_kinds == ("start", "end")

"""Test del BodyModulator: body_euclid_k e body_euclid_rot."""
from __future__ import annotations

import numpy as np

from desnivel.config import BodyConfig, Config, DEFAULT_CONFIG
from desnivel.modulation import ModulationFrame
from desnivel.modulators import BodyModulator
from desnivel.track import Track


RATE = 10.0


def _t(n: int) -> np.ndarray:
    return np.arange(n, dtype=float) / RATE


def _frame_with(t: np.ndarray, **channels: np.ndarray) -> ModulationFrame:
    f = ModulationFrame(t=t)
    for name, arr in channels.items():
        f.add(name, arr)
    return f


def _empty_track(n: int) -> Track:
    return Track(stage_id="t", t=_t(n), samples={})


def _run(n: int, energy: float, phase: float,
         config: Config = DEFAULT_CONFIG) -> ModulationFrame:
    track = _empty_track(n)
    frame = _frame_with(track.t,
                        journey_energy=np.full(n, energy),
                        journey_phase=np.full(n, phase))
    BodyModulator(config).process(track, frame)
    return frame


def test_emits_both_channels() -> None:
    f = _run(200, energy=0.5, phase=0.5)
    assert "body_euclid_k" in f.channels
    assert "body_euclid_rot" in f.channels


def test_channels_are_integer_valued() -> None:
    f = _run(200, energy=0.7, phase=0.3)
    for name in ("body_euclid_k", "body_euclid_rot"):
        v = f.channels[name]
        assert np.allclose(v, np.round(v))


def test_k_at_energy_zero_is_min_k() -> None:
    cfg = DEFAULT_CONFIG
    f = _run(200, energy=0.0, phase=0.5)
    assert int(f.channels["body_euclid_k"][-1]) == cfg.body.min_k


def test_k_at_energy_one_is_max_k() -> None:
    cfg = DEFAULT_CONFIG
    f = _run(200, energy=1.0, phase=0.5)
    assert int(f.channels["body_euclid_k"][-1]) == cfg.body.max_k


def test_rot_in_valid_range() -> None:
    cfg = DEFAULT_CONFIG
    f = _run(200, energy=0.5, phase=1.0)
    rot = f.channels["body_euclid_rot"]
    assert rot.min() >= 0
    assert rot.max() <= cfg.body.steps - 1


def test_rot_at_phase_zero_is_zero() -> None:
    f = _run(200, energy=0.5, phase=0.0)
    assert int(f.channels["body_euclid_rot"][-1]) == 0


def test_fallback_when_no_energy_or_phase() -> None:
    """Senza journey_* nel frame: k usa energy=0.5, rot usa phase=0.5."""
    track = _empty_track(200)
    frame = ModulationFrame(t=track.t)
    BodyModulator(DEFAULT_CONFIG).process(track, frame)
    cfg = DEFAULT_CONFIG.body
    expected_k = round(cfg.min_k + 0.5 * (cfg.max_k - cfg.min_k))
    assert int(frame.channels["body_euclid_k"][-1]) == expected_k


def test_empty_track() -> None:
    track = Track(stage_id="empty", t=np.array([]), samples={})
    frame = ModulationFrame(t=track.t)
    BodyModulator(DEFAULT_CONFIG).process(track, frame)
    assert frame.channels["body_euclid_k"].size == 0
    assert frame.channels["body_euclid_rot"].size == 0


def test_custom_steps_and_range() -> None:
    cfg = Config(body=BodyConfig(steps=8, min_k=1, max_k=5, dwell_s=0.0))
    f = _run(200, energy=1.0, phase=1.0, config=cfg)
    assert int(f.channels["body_euclid_k"][-1]) == 5
    assert int(f.channels["body_euclid_rot"][-1]) == 7  # steps - 1


def test_determinism() -> None:
    f1 = _run(300, energy=0.6, phase=0.4)
    f2 = _run(300, energy=0.6, phase=0.4)
    assert np.array_equal(f1.channels["body_euclid_k"],
                          f2.channels["body_euclid_k"])
    assert np.array_equal(f1.channels["body_euclid_rot"],
                          f2.channels["body_euclid_rot"])

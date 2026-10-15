"""Test del MacroModulator: 5 canali, dwell-time, fallback, policy."""
from __future__ import annotations

import numpy as np

from desnivel.config import DEFAULT_CONFIG, Config, MacroConfig
from desnivel.modulation import ModulationFrame
from desnivel.modulators import JourneyModulator, MacroModulator
from desnivel.modulators.macro import (
    _apply_dwell,
    _bucketize_elevation,
    _bucketize_variance,
    _lowpass,
    _rolling_median,
    _rolling_std,
)
from desnivel.modulators.macro_policies import (
    MacroPolicy,
    POLICIES,
    get_policy,
)
from desnivel.track import Track


RATE = 10.0  # internal_rate_hz


# ──────────────────── Track factories ──────────────────────────────


def _t(n: int) -> np.ndarray:
    return np.arange(n, dtype=float) / RATE


def _track_flat(duration_s: float, ele: float = 100.0) -> Track:
    n = int(duration_s * RATE) + 1
    return Track(
        stage_id="flat",
        t=_t(n),
        samples={
            "ele": np.full(n, ele),
            "lat": np.zeros(n),
            "lon": np.zeros(n),
        },
    )


def _track_two_sections(low: float, high: float, half_s: float) -> Track:
    """Tappa in 2 sezioni: prima `half_s` a `low`, poi `half_s` a `high`."""
    n_half = int(half_s * RATE)
    ele = np.concatenate([np.full(n_half, low), np.full(n_half, high)])
    n = ele.size
    return Track(
        stage_id="two",
        t=_t(n),
        samples={
            "ele": ele,
            "lat": np.zeros(n),
            "lon": np.zeros(n),
        },
    )


def _frame_with_openness(track: Track, openness: float) -> ModulationFrame:
    n = track.n_samples
    f = ModulationFrame(t=track.t)
    f.add("journey_openness", np.full(n, openness))
    return f


# ──────────────────── Helpers numerici ─────────────────────────────


def test_rolling_median_preserves_size_and_constant() -> None:
    x = np.ones(50) * 7.0
    out = _rolling_median(x, window_n=11)
    assert out.shape == x.shape
    assert np.allclose(out, 7.0)


def test_rolling_std_constant_signal_zero() -> None:
    x = np.full(50, 3.5)
    assert np.allclose(_rolling_std(x, window_n=11), 0.0)


def test_lowpass_converges_to_input() -> None:
    x = np.full(200, 1.0)
    y = _lowpass(x, dt=0.1, tau_s=1.0)
    assert y[-1] > 0.95


def test_bucketize_elevation_two_sections() -> None:
    elev = np.concatenate([np.full(100, 50.0), np.full(100, 1000.0)])
    bucket, (lo, hi) = _bucketize_elevation(elev, (33.0, 67.0))
    assert lo < hi
    # Sezione bassa e alta in bucket distinti (qualunque siano).
    assert bucket[0] != bucket[-1]


def test_bucketize_variance_constant_signal_zero_bucket() -> None:
    var = np.zeros(100)
    bucket, thr = _bucketize_variance(var, 60.0)
    assert thr == 0.0
    # Tutti uguali alla soglia 0 -> tutti `>=`, quindi mossi.
    assert (bucket == 1).all()


def test_apply_dwell_no_flicker() -> None:
    # Flicker singolo: si ignora.
    values = np.array([1, 1, 1, 2, 1, 1, 1, 1, 1, 1])
    out = _apply_dwell(values, dwell_n=3)
    assert (out == 1).all()


def test_apply_dwell_real_transition() -> None:
    # 3 valori consecutivi a 2 -> commuta a 2.
    values = np.array([1, 1, 1, 2, 2, 2, 2, 2])
    out = _apply_dwell(values, dwell_n=3)
    assert out[0] == 1
    assert out[-1] == 2


# ──────────────────── MacroModulator: output base ──────────────────


def _run(track: Track, openness: float = 0.5,
         config: Config = DEFAULT_CONFIG) -> ModulationFrame:
    frame = _frame_with_openness(track, openness)
    MacroModulator(config).process(track, frame)
    return frame


def test_emits_all_five_channels() -> None:
    frame = _run(_track_flat(120.0))
    for name in ("macro_scale", "macro_palette", "macro_register",
                 "macro_space", "macro_brightness"):
        assert name in frame.channels


def test_channels_have_track_length() -> None:
    track = _track_flat(60.0)
    frame = _run(track)
    for name in frame.channel_names:
        assert frame.channels[name].size == track.n_samples


def test_int_channels_are_integer_valued() -> None:
    frame = _run(_track_flat(120.0))
    for name in ("macro_scale", "macro_palette"):
        v = frame.channels[name]
        assert np.allclose(v, np.round(v))


def test_float_channels_in_range() -> None:
    frame = _run(_track_flat(120.0))
    for name in ("macro_register", "macro_space", "macro_brightness"):
        v = frame.channels[name]
        assert v.min() >= 0.0 - 1e-9
        assert v.max() <= 1.0 + 1e-9


def test_register_changes_between_low_and_high_sections() -> None:
    track = _track_two_sections(low=50.0, high=1000.0, half_s=120.0)
    frame = _run(track)
    reg = frame.channels["macro_register"]
    # Bassa zona -> registro basso; zona alta -> registro alto.
    half = reg.size // 2
    assert reg[:half // 2].mean() < 0.3
    assert reg[-half // 4:].mean() > 0.6


def test_openness_drives_scale_via_thresholds() -> None:
    track = _track_flat(120.0)
    pol = get_policy("default")
    # openness bassa -> bucket 0 -> scale = phrygian (2)
    frame_lo = _run(track, openness=0.10)
    assert int(frame_lo.channels["macro_scale"][-1]) == pol.lookup_scale(0)
    # openness alta -> bucket 2 -> lydian (4)
    frame_hi = _run(track, openness=0.75)
    assert int(frame_hi.channels["macro_scale"][-1]) == pol.lookup_scale(2)


def test_fallback_when_no_elevation() -> None:
    n = int(60 * RATE)
    track = Track(stage_id="no_ele", t=_t(n), samples={})
    frame = ModulationFrame(t=track.t)
    MacroModulator(DEFAULT_CONFIG).process(track, frame)
    # Tutti costanti al fallback.
    assert np.allclose(frame.channels["macro_scale"],
                       DEFAULT_CONFIG.macro.fallback_scale)
    assert np.allclose(frame.channels["macro_palette"],
                       DEFAULT_CONFIG.macro.fallback_palette)


def test_fallback_for_very_short_track() -> None:
    track = Track(
        stage_id="tiny",
        t=np.array([0.0, 0.1]),
        samples={"ele": np.array([100.0, 110.0])},
    )
    frame = ModulationFrame(t=track.t)
    MacroModulator(DEFAULT_CONFIG).process(track, frame)
    assert frame.channels["macro_scale"].size == 2


def test_determinism_same_inputs_same_outputs() -> None:
    track = _track_two_sections(50.0, 1000.0, half_s=120.0)
    f1 = _run(track, openness=0.5)
    f2 = _run(track, openness=0.5)
    for name in f1.channel_names:
        assert np.array_equal(f1.channels[name], f2.channels[name])


# ──────────────────── Policy swappable ─────────────────────────────


def test_policy_minimal_never_emits_bells() -> None:
    cfg = Config(macro=MacroConfig(policy_name="minimal"))
    frame = _run(_track_flat(60.0), config=cfg)
    palette = frame.channels["macro_palette"]
    assert 2 not in palette.astype(int)


def test_policy_registry_has_default_entries() -> None:
    assert "default" in POLICIES
    assert "minimal" in POLICIES
    assert "dark" in POLICIES
    for name, pol in POLICIES.items():
        assert isinstance(pol, MacroPolicy)
        assert pol.name == name


def test_get_policy_raises_on_unknown_name() -> None:
    import pytest
    with pytest.raises(KeyError):
        get_policy("nonexistent")


# ──────────────────── Integrazione con JourneyModulator ────────────


def test_integration_after_journey() -> None:
    """MacroModulator legge journey_openness aggiunto da JourneyModulator."""
    track = _track_two_sections(50.0, 1000.0, half_s=120.0)
    frame = ModulationFrame(t=track.t)
    JourneyModulator(DEFAULT_CONFIG).process(track, frame)
    MacroModulator(DEFAULT_CONFIG).process(track, frame)
    # Aggiunge tutti i 5 canali macro senza errori.
    assert "macro_palette" in frame.channels
    assert "macro_brightness" in frame.channels

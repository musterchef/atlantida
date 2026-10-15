"""Test del JourneyModulator."""
from __future__ import annotations

import numpy as np

from desnivel.config import DEFAULT_CONFIG, Config, JourneyConfig
from desnivel.modulation import ModulationFrame
from desnivel.modulators import JourneyModulator
from desnivel.track import Track, make_empty_track

_RATE = DEFAULT_CONFIG.timing.internal_rate_hz


def _empty_frame(track: Track) -> ModulationFrame:
    return ModulationFrame(t=track.t)


def test_phase_is_monotonic_zero_to_one() -> None:
    track = make_empty_track("t", duration_s=120.0, rate_hz=_RATE)
    mod = JourneyModulator()
    frame = mod.process(track, _empty_frame(track))

    phase = frame.channels["journey_phase"]
    assert phase[0] == 0.0
    assert phase[-1] == 1.0
    assert np.all(np.diff(phase) >= -1e-12)


def test_outputs_have_expected_channels() -> None:
    track = make_empty_track("t", duration_s=60.0, rate_hz=_RATE)
    mod = JourneyModulator()
    frame = mod.process(track, _empty_frame(track))
    assert set(frame.channel_names) == {
        "journey_phase", "journey_energy", "journey_openness",
    }


def test_energy_is_zero_when_no_effort_channel() -> None:
    track = make_empty_track("t", duration_s=300.0, rate_hz=_RATE)
    mod = JourneyModulator()
    frame = mod.process(track, _empty_frame(track))
    assert np.allclose(frame.channels["journey_energy"], 0.0)


def test_energy_charges_and_decays_on_step_effort() -> None:
    duration = 1800.0
    n = int(duration * _RATE) + 1
    t = np.arange(n, dtype=float) / _RATE
    # Sforzo a gradino: 0 nei primi 300s, 1 fino a 1200s, 0 dopo.
    effort = np.zeros(n, dtype=float)
    effort[(t >= 300.0) & (t < 1200.0)] = 1.0

    track = Track(stage_id="t", t=t, samples={"effort": effort})
    mod = JourneyModulator()
    frame = mod.process(track, _empty_frame(track))
    energy = frame.channels["journey_energy"]

    # All'inizio energia ferma a zero.
    assert energy[0] == 0.0
    # Durante il plateau di sforzo l'energia sale.
    idx_plateau_end = int(1199.0 * _RATE)
    assert energy[idx_plateau_end] > 0.3
    # Dopo il rilascio decade ma non istantaneamente.
    idx_after = int(1700.0 * _RATE)
    assert energy[idx_after] > 0.0
    assert energy[idx_after] < energy[idx_plateau_end]


def test_openness_grows_with_phase_when_no_effort() -> None:
    track = make_empty_track("t", duration_s=600.0, rate_hz=_RATE)
    mod = JourneyModulator()
    frame = mod.process(track, _empty_frame(track))
    openness = frame.channels["journey_openness"]
    assert openness[0] < openness[-1]
    # Resta nel range nominale.
    assert openness.min() >= 0.0
    assert openness.max() <= 1.0


def test_openness_respects_base_at_start() -> None:
    cfg = Config(journey=JourneyConfig(openness_base=0.25))
    track = make_empty_track("t", duration_s=600.0, rate_hz=_RATE)
    frame = JourneyModulator(cfg).process(track, _empty_frame(track))
    assert frame.channels["journey_openness"][0] == 0.25

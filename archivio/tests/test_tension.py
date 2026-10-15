"""Test per ``TensionModulator``."""
from __future__ import annotations

import numpy as np

from desnivel.config import DEFAULT_CONFIG
from desnivel.modulation import ModulationFrame
from desnivel.modulators import TensionModulator
from desnivel.track import make_empty_track


def _track_with_effort(effort: np.ndarray, rate_hz: float = 10.0):
    """Costruisce un Track con un canale ``effort`` dato."""
    n = len(effort)
    duration_s = (n - 1) / rate_hz
    track = make_empty_track(stage_id="t", duration_s=duration_s, rate_hz=rate_hz)
    # Track è frozen ma samples è un dict mutabile, lo popoliamo.
    track.samples["effort"] = effort.astype(float)
    return track


def _empty_frame(track):
    return ModulationFrame(t=track.t)


def test_tension_output_channel():
    mod = TensionModulator(DEFAULT_CONFIG)
    assert mod.output_channels == ("meso_tension",)


def test_tension_zero_without_effort():
    """Senza canale effort, tension resta a zero."""
    track = make_empty_track(stage_id="t", duration_s=10.0, rate_hz=10.0)
    frame = _empty_frame(track)
    mod = TensionModulator(DEFAULT_CONFIG)
    out = mod.process(track, frame)
    assert np.allclose(out.channels["meso_tension"], 0.0)


def test_tension_responds_faster_than_journey_energy():
    """Su uno step di sforzo, meso_tension sale prima di journey_energy.

    Verifica empirica della differenza di scala: tension_charge=30s vs
    energy_charge=300s. Dopo 30 secondi di sforzo costante, tension è
    già sopra metà del valore di regime; journey_energy molto meno.
    """
    from desnivel.modulators import JourneyModulator

    rate_hz = 10.0
    n = int(60 * rate_hz)  # 60 s
    effort = np.ones(n)  # step da 0 a 1
    track = _track_with_effort(effort, rate_hz)

    t_mod = TensionModulator(DEFAULT_CONFIG)
    j_mod = JourneyModulator(DEFAULT_CONFIG)

    tension = t_mod.process(track, _empty_frame(track)).channels["meso_tension"]
    energy = j_mod.process(track, _empty_frame(track)).channels["journey_energy"]

    # A 30 s di sforzo costante:
    idx_30s = int(30 * rate_hz)
    assert tension[idx_30s] > energy[idx_30s] * 2
    # E tension è significativamente sopra zero:
    assert tension[idx_30s] > 0.4


def test_tension_decays_when_effort_drops():
    """Quando lo sforzo scende a zero, la tensione decade."""
    rate_hz = 10.0
    n_high = int(120 * rate_hz)  # 2 min di sforzo
    n_low = int(120 * rate_hz)   # 2 min di riposo
    effort = np.concatenate([np.ones(n_high), np.zeros(n_low)])
    track = _track_with_effort(effort, rate_hz)

    mod = TensionModulator(DEFAULT_CONFIG)
    tension = mod.process(track, _empty_frame(track)).channels["meso_tension"]

    peak = tension[n_high - 1]
    end = tension[-1]
    assert end < peak  # è effettivamente decaduto
    assert end < peak * 0.5  # decaduto sostanzialmente


def test_tension_in_unit_range():
    """Con effort in [0,1], tension resta in [0,1]."""
    rng = np.random.default_rng(42)
    effort = rng.uniform(0.0, 1.0, size=1000)
    track = _track_with_effort(effort)
    mod = TensionModulator(DEFAULT_CONFIG)
    tension = mod.process(track, _empty_frame(track)).channels["meso_tension"]
    assert tension.min() >= 0.0
    assert tension.max() <= 1.0


def test_tension_clips_negative_effort():
    """Effort sotto zero (sporco) viene clippato a 0, non scende."""
    rate_hz = 10.0
    effort = np.full(100, -0.5)  # input invalido
    track = _track_with_effort(effort, rate_hz)
    mod = TensionModulator(DEFAULT_CONFIG)
    tension = mod.process(track, _empty_frame(track)).channels["meso_tension"]
    assert np.all(tension >= 0.0)

"""Test del HarmonyModulator: meso_root int, sequenza, dwell, POI."""
from __future__ import annotations

import numpy as np

from desnivel.config import Config, DEFAULT_CONFIG, HarmonyConfig
from desnivel.modulation import ModulationFrame
from desnivel.modulators import HarmonyModulator
from desnivel.track import Track


RATE = 10.0


def _t(n: int) -> np.ndarray:
    return np.arange(n, dtype=float) / RATE


def _track_with_dist(total_km: float, duration_s: float) -> Track:
    """Tappa lineare: distanza cumula uniformemente da 0 a total_km."""
    n = int(duration_s * RATE) + 1
    cum_m = np.linspace(0.0, total_km * 1000.0, n)
    return Track(
        stage_id="lin",
        t=_t(n),
        samples={
            "cum_dist_m": cum_m,
            "lat": np.zeros(n),
            "lon": np.zeros(n),
        },
    )


def _run(track: Track, config: Config = DEFAULT_CONFIG) -> ModulationFrame:
    frame = ModulationFrame(t=track.t)
    HarmonyModulator(config).process(track, frame)
    return frame


# ──────────────────── Output base ──────────────────────────────────


def test_emits_meso_root_channel() -> None:
    frame = _run(_track_with_dist(20.0, 600.0))
    assert "meso_root" in frame.channels


def test_root_is_integer_valued() -> None:
    frame = _run(_track_with_dist(40.0, 600.0))
    v = frame.channels["meso_root"]
    assert np.allclose(v, np.round(v))


def test_root_within_midi_range() -> None:
    frame = _run(_track_with_dist(100.0, 600.0))
    v = frame.channels["meso_root"]
    assert v.min() >= 0
    assert v.max() <= 127


def test_starts_on_tonic() -> None:
    cfg = DEFAULT_CONFIG
    frame = _run(_track_with_dist(20.0, 600.0), cfg)
    assert int(frame.channels["meso_root"][0]) == cfg.harmony.base_midi


def test_changes_after_km_per_change() -> None:
    """Dopo km_per_change km dovremmo essere su un'altra nota della seq."""
    cfg = DEFAULT_CONFIG
    # Tappa lunga abbastanza da coprire 3 sezioni: 3 * km_per_change km.
    total_km = cfg.harmony.km_per_change * 3
    frame = _run(_track_with_dist(total_km, 1800.0), cfg)
    root = frame.channels["meso_root"]
    # Inizio sezione 0 (tonica). Fine sezione 2 -> seq[2].
    assert int(root[0]) == cfg.harmony.base_midi
    expected_last = cfg.harmony.base_midi + cfg.harmony.interval_sequence[2]
    assert int(root[-1]) == expected_last


def test_sequence_cycles() -> None:
    """Dopo un giro completo della sequenza si torna alla tonica."""
    cfg = DEFAULT_CONFIG
    seq_len = len(cfg.harmony.interval_sequence)
    # Tappa che copre esattamente seq_len sezioni: l'ultima sezione ha
    # indice (seq_len - 1) % seq_len = seq_len - 1 -> seq[-1].
    # Poi un piccolo extra dentro per coprire un giro: indice 0.
    total_km = cfg.harmony.km_per_change * seq_len + cfg.harmony.km_per_change * 0.5
    frame = _run(_track_with_dist(total_km, 1800.0), cfg)
    root = frame.channels["meso_root"]
    # Indice = floor((seq_len + 0.5) * km_per_change / km_per_change) mod seq_len
    #       = (seq_len + 0) mod seq_len = 0 -> tonica.
    assert int(root[-1]) == cfg.harmony.base_midi


# ──────────────────── Fallback / edge cases ────────────────────────


def test_fallback_when_no_distance_channel() -> None:
    n = 100
    track = Track(stage_id="no_dist", t=_t(n), samples={})
    frame = _run(track)
    root = frame.channels["meso_root"]
    assert root.size == n
    assert (root == DEFAULT_CONFIG.harmony.base_midi).all()


def test_empty_track() -> None:
    track = Track(stage_id="empty", t=np.array([]), samples={})
    frame = ModulationFrame(t=track.t)
    HarmonyModulator(DEFAULT_CONFIG).process(track, frame)
    assert frame.channels["meso_root"].size == 0


def test_custom_sequence_via_config() -> None:
    """Sequenza personalizzata -> esattamente quelle note in output."""
    cfg = Config(harmony=HarmonyConfig(
        base_midi=60,
        interval_sequence=(0, 12),  # solo tonica e ottava
        km_per_change=1.0,
        min_dwell_s=0.0,
    ))
    frame = _run(_track_with_dist(2.5, 600.0), cfg)
    root = frame.channels["meso_root"].astype(int)
    assert set(np.unique(root)).issubset({60, 72})


def test_determinism() -> None:
    track = _track_with_dist(30.0, 900.0)
    f1 = _run(track)
    f2 = _run(track)
    assert np.array_equal(f1.channels["meso_root"], f2.channels["meso_root"])


def test_dwell_prevents_flicker() -> None:
    """Tappa ferma sul confine: anti-flicker mantiene la nota iniziale."""
    cfg = Config(harmony=HarmonyConfig(
        base_midi=48,
        interval_sequence=(0, 5),
        km_per_change=1.0,
        min_dwell_s=100.0,  # dwell molto lungo
    ))
    # Tappa che oscilla a cavallo del confine 1km, troppo breve per cambiare.
    n = int(20.0 * RATE)
    cum_m = np.full(n, 999.0)
    cum_m[n // 2:] = 1001.0  # crossing instantaneo
    track = Track(stage_id="osc", t=_t(n),
                  samples={"cum_dist_m": cum_m,
                           "lat": np.zeros(n), "lon": np.zeros(n)})
    frame = _run(track, cfg)
    root = frame.channels["meso_root"]
    # Tutta la tappa resta sulla tonica (dwell > durata totale).
    assert (root == 48).all()

"""
Unit tests per audio_mapper.

Esegui:
    cd src && python -m pytest test_audio_mapper.py -v
    # oppure, senza pytest:
    cd src && python test_audio_mapper.py
"""

from datetime import datetime

import audio_mapper as am


# ─── Mappature scalari ────────────────────────────────────────────────────

def test_altitude_to_pitch_bounds():
    assert am.altitude_to_pitch_continuous(0.0) == am.PITCH_MIN
    assert am.altitude_to_pitch_continuous(1.0) == am.PITCH_MAX
    # clamp
    assert am.altitude_to_pitch_continuous(-1.0) == am.PITCH_MIN
    assert am.altitude_to_pitch_continuous(2.0)  == am.PITCH_MAX


def test_altitude_to_pitch_monotonic():
    a = am.altitude_to_pitch_continuous(0.2)
    b = am.altitude_to_pitch_continuous(0.5)
    c = am.altitude_to_pitch_continuous(0.9)
    assert a < b < c


def test_speed_to_bpm_bounds():
    assert am.speed_to_bpm(0.0)  == am.BPM_MIN
    assert am.speed_to_bpm(am.SPEED_REF_KMH) == am.BPM_MAX
    assert am.speed_to_bpm(999.0) == am.BPM_MAX  # saturazione


def test_slope_to_drive():
    assert am.slope_to_drive(0.0)   == 0.0
    assert am.slope_to_drive(-0.05) == 0.0          # discese non saturano
    assert am.slope_to_drive(am.SLOPE_REF) == 1.0    # 10% = drive massimo
    assert am.slope_to_drive(0.5)   == 1.0           # clamp


def test_curvature_to_density_symmetry():
    # densità dipende dal modulo, non dal segno
    assert am.curvature_to_density(-0.3) == am.curvature_to_density(0.3)
    assert am.curvature_to_density(0.0)  == 0.0
    assert am.curvature_to_density(1.0)  == 1.0


def test_difficulty_to_volume_floor():
    # mai sotto 0.4 (presenza minima)
    assert am.difficulty_to_volume(0.0) == 0.4
    assert am.difficulty_to_volume(1.0) == 1.0
    v = am.difficulty_to_volume(0.5)
    assert 0.4 < v < 1.0


def test_flow_to_reverb_bounds():
    assert am.flow_to_reverb(0.0) == 0.05
    assert am.flow_to_reverb(1.0) == 0.85


def test_altitude_to_cutoff_open_with_height():
    assert am.altitude_to_cutoff(0.0) == am.CUTOFF_MIN
    assert am.altitude_to_cutoff(1.0) == am.CUTOFF_MAX


# ─── Time of Day ──────────────────────────────────────────────────────────

def test_hour_to_scale_bands():
    assert am.hour_to_scale(7.0)  == "major"
    assert am.hour_to_scale(13.0) == "pentatonic_major"
    assert am.hour_to_scale(19.0) == "dorian"
    assert am.hour_to_scale(2.0)  == "phrygian"


def test_hour_to_color_temp_warmest_at_sunset():
    # massimo (≈1) intorno alle 18:00, minimo (≈0) intorno alle 06:00
    assert am.hour_to_color_temp(18.0) > am.hour_to_color_temp(6.0)
    assert 0.0 <= am.hour_to_color_temp(0.0)  <= 1.0
    assert 0.0 <= am.hour_to_color_temp(12.0) <= 1.0


# ─── Terrain → voice ──────────────────────────────────────────────────────

def test_terrain_to_voice_extremes():
    assert am.terrain_to_voice(0.0) == "drone_water"
    assert am.terrain_to_voice(1.0) == "brass_mountain"
    # clamp
    assert am.terrain_to_voice(-0.5) == "drone_water"
    assert am.terrain_to_voice(2.0)  == "brass_mountain"


def test_terrain_to_voice_midband():
    assert am.terrain_to_voice(0.30) == "pad_plain"
    assert am.terrain_to_voice(0.65) == "pluck_hill"


# ─── Quantizzazione ───────────────────────────────────────────────────────

def test_quantize_pitch_snaps_to_scale():
    # In C major (root=60), 60.4 → 60 (C), 61.6 → 62 (D), 63.4 → 64 (E)
    assert am.quantize_pitch_to_scale(60.4, "major", root=60) == 60
    assert am.quantize_pitch_to_scale(61.6, "major", root=60) == 62
    assert am.quantize_pitch_to_scale(63.4, "major", root=60) == 64


def test_quantize_pitch_unknown_scale_raises():
    try:
        am.quantize_pitch_to_scale(60, "blues_inesistente")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_quantize_pitch_in_midi_range():
    for cont in (-30.0, 0.0, 60.0, 130.0, 200.0):
        p = am.quantize_pitch_to_scale(cont, "minor")
        assert 0 <= p <= 127


# ─── make_sonic_params ────────────────────────────────────────────────────

def _sample_row(**overrides):
    base = dict(
        ele_norm=0.5,
        slope=0.04,
        curvature=0.1,
        speed_kmh=18.0,
        difficulty=0.3,
        flow_index=0.7,
        terrain_type=0.66,
        td_time=42.0,
        td_time_norm=0.07,
    )
    base.update(overrides)
    return base


def test_make_sonic_params_smoke():
    sp = am.make_sonic_params(_sample_row())
    d = sp.to_dict()
    # tutte le chiavi dichiarate sono presenti
    expected = {
        "t", "t_norm", "pitch", "pitch_continuous", "scale", "root",
        "bpm", "density", "drive", "volume", "reverb", "cutoff",
        "voice", "color_temp", "source",
    }
    assert expected.issubset(d.keys())
    assert 0 <= d["pitch"] <= 127
    assert am.BPM_MIN <= d["bpm"] <= am.BPM_MAX
    assert 0.0 <= d["drive"] <= 1.0
    assert 0.0 <= d["reverb"] <= 1.0
    assert d["scale"] == "major"  # default senza start_dt


def test_make_sonic_params_with_time_picks_scale():
    morning  = datetime(2025, 6, 1, 7, 0)
    midday   = datetime(2025, 6, 1, 13, 0)
    sunset   = datetime(2025, 6, 1, 19, 0)
    night    = datetime(2025, 6, 1, 2, 0)

    assert am.make_sonic_params(_sample_row(), start_dt=morning).scale == "major"
    assert am.make_sonic_params(_sample_row(), start_dt=midday ).scale == "pentatonic_major"
    assert am.make_sonic_params(_sample_row(), start_dt=sunset ).scale == "dorian"
    assert am.make_sonic_params(_sample_row(), start_dt=night  ).scale == "phrygian"


def test_make_sonic_params_handles_missing_keys():
    # input minimale: il mapper non deve esplodere su chiavi assenti
    sp = am.make_sonic_params({})
    d = sp.to_dict()
    assert d["bpm"] == am.BPM_MIN
    assert d["drive"] == 0.0
    assert d["volume"] == 0.4  # floor


def test_make_sonic_params_include_source():
    sp = am.make_sonic_params(_sample_row(), include_source=True)
    assert "ele_norm" in sp.source
    assert "slope"    in sp.source
    assert sp.source["ele_norm"] == 0.5


def test_map_rows_advances_time():
    rows = [
        _sample_row(td_time_norm=0.0),
        _sample_row(td_time_norm=0.5),
        _sample_row(td_time_norm=1.0),
    ]
    start = datetime(2025, 6, 1, 9, 0)  # 09:00 → major
    result = am.map_rows(rows, start_dt=start)
    assert len(result) == 3
    # Inizio in mattina (major), fine dopo 8h reali → 17:00 (dorian)
    assert result[0]["scale"] == "major"
    assert result[-1]["scale"] == "dorian"


# ─── Test runner stand-alone (no pytest) ──────────────────────────────────

if __name__ == "__main__":
    import sys, traceback
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception:
            failed += 1
            print(f"  ✗ {t.__name__}")
            traceback.print_exc()
    total = len(tests)
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)

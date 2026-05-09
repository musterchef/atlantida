"""Unit tests for bpm_smoothing module."""

import bpm_smoothing as bs


def test_savgol_filter_reduces_noise():
    """Verifica che Savitzky-Goyal riduce il rumore."""
    # Dati sintetici: trend lineare con noise
    data = [50.0 + i + (5.0 if i % 2 == 0 else -5.0) for i in range(10)]
    smooth = bs.savgol_filter(data, window_length=5, polyorder=2)
    
    # La versione liscia ha varianza minore (meno oscillazione)
    var_orig = sum((x - sum(data) / len(data)) ** 2 for x in data) / len(data)
    var_smooth = sum((x - sum(smooth) / len(smooth)) ** 2 for x in smooth) / len(smooth)
    assert var_smooth < var_orig, "Smooth dovrebbe ridurre la varianza"


def test_savgol_preserves_monotonic_trend():
    """Verifica che Savitzky-Goyal preserva il trend."""
    # Dati monotonicamente crescenti
    data = [float(i) for i in range(1, 11)]
    smooth = bs.savgol_filter(data, window_length=5, polyorder=2)
    
    # La versione liscia dovrebbe essere ancora monotonica
    for i in range(len(smooth) - 1):
        assert smooth[i] <= smooth[i + 1], f"Break monotonia at {i}"


def test_smooth_speed_length():
    """Verifica che smooth_speed mantiene la lunghezza."""
    speed = [20.0, 21.5, 22.1, 21.8, 20.5, 19.0]
    smooth = bs.smooth_speed(speed, window_length=5)
    assert len(smooth) == len(speed)


def test_quantize_bpm_snaps_to_grid():
    """Verifica la quantizzazione a griglia musicale (90-140 BPM)."""
    assert bs.quantize_bpm(92.0) == 90    # più vicino a 90
    assert bs.quantize_bpm(106.0) == 110  # più vicino a 110
    assert bs.quantize_bpm(110.0) == 110  # esatto
    assert bs.quantize_bpm(136.0) == 140  # più vicino a 140


def test_quantize_bpm_grid_coverage():
    """Verifica che tutti i BPM mappano a un valore della griglia."""
    for bpm in range(40, 160, 5):
        q = bs.quantize_bpm(float(bpm))
        assert q in bs.BPM_GRID, f"BPM {bpm} non ha mapping valido"


def test_blend_bpm_with_flow_extremes():
    """Verifica i casi estremi del blend."""
    bpm = 100.0
    
    # flow=0 (nessuna continuità)
    blended_min = bs.blend_bpm_with_flow(bpm, 0.0)
    assert blended_min == bpm * 0.7, f"Expected {bpm * 0.7}, got {blended_min}"
    
    # flow=1 (massima continuità)
    blended_max = bs.blend_bpm_with_flow(bpm, 1.0)
    assert blended_max == bpm * 1.0, f"Expected {bpm}, got {blended_max}"
    
    # flow=0.5 (media)
    blended_mid = bs.blend_bpm_with_flow(bpm, 0.5)
    assert blended_mid == bpm * 0.85


def test_blend_bpm_clamping():
    """Verifica che flow_index fuori [0,1] viene clamped."""
    bpm = 100.0
    
    # flow < 0
    blended = bs.blend_bpm_with_flow(bpm, -0.5)
    assert blended == bpm * 0.7  # clamped a 0
    
    # flow > 1
    blended = bs.blend_bpm_with_flow(bpm, 1.5)
    assert blended == bpm * 1.0  # clamped a 1


def test_apply_bpm_smoothing_full_length():
    """Verifica che apply_bpm_smoothing_full mantiene lunghezza."""
    speed = [20.0, 21.0, 22.0, 21.5, 20.0]
    flow = [0.8, 0.9, 0.95, 0.85, 0.7]
    
    def dummy_speed_to_bpm(s):
        return 60 + s * 2  # mapping semplice
    
    result = bs.apply_bpm_smoothing_full(
        speed, flow, dummy_speed_to_bpm,
        smooth_window=3,
        quantize=True,
        blend_flow=True
    )
    
    assert len(result) == len(speed)
    assert all(b in bs.BPM_GRID for b in result), "Tutti i BPM dovrebbero essere quantizzati"


def test_apply_bpm_smoothing_full_flow_blend_effect():
    """Verifica che lo smoothing completo applica il blend correttamente."""
    speed = [25.0] * 5  # velocità costante
    flow_low = [0.0, 0.2, 0.4, 0.6, 0.8]  # flow crescente
    flow_high = [1.0] * 5  # flow alto
    
    def dummy_speed_to_bpm(s):
        return 100.0  # BPM base
    
    # Con flow basso, BPM dovrebbe calare
    result_low = bs.apply_bpm_smoothing_full(
        speed, flow_low, dummy_speed_to_bpm,
        smooth_window=3,
        quantize=True,
        blend_flow=True
    )
    
    # Con flow alto, BPM dovrebbe rimanere elevato
    result_high = bs.apply_bpm_smoothing_full(
        speed, flow_high, dummy_speed_to_bpm,
        smooth_window=3,
        quantize=True,
        blend_flow=True
    )
    
    # La media bassa dovrebbe essere inferiore alla media alta
    avg_low = sum(result_low) / len(result_low)
    avg_high = sum(result_high) / len(result_high)
    assert avg_low < avg_high, f"Low flow {avg_low} dovrebbe essere < high flow {avg_high}"


def test_apply_bpm_length_mismatch_raises():
    """Verifica che lunghezze diverse sollevano errore."""
    speed = [20.0, 21.0, 22.0]
    flow = [0.8, 0.9]  # lunghezza diversa!
    
    def dummy_speed_to_bpm(s):
        return 100.0
    
    try:
        bs.apply_bpm_smoothing_full(speed, flow, dummy_speed_to_bpm)
        raise AssertionError("Expected ValueError for length mismatch")
    except ValueError as e:
        assert "stessa lunghezza" in str(e)


# ─── Test runner stand-alone ──────────────────────────────────────────

if __name__ == "__main__":
    import sys, traceback
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {t.__name__}")
            traceback.print_exc()
    total = len(tests)
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)

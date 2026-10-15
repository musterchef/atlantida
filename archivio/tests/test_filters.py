"""Test per `desnivel._filters`."""
from __future__ import annotations

import numpy as np
import pytest

from desnivel._filters import (
    _savgol_coeffs,
    asymmetric_leaky_integrator,
    savgol_filter,
)


# ── Savitzky-Golay ──────────────────────────────────────────────────────


def test_savgol_coeffs_sum_to_one():
    """Per qualunque (window, polyorder) i coefficienti sommano a 1:
    riproducono esattamente un segnale costante."""
    for window in (3, 5, 7, 11, 21):
        for poly in (1, 2, 3):
            if poly + 1 > window:
                continue
            c = _savgol_coeffs(window, poly)
            assert c.shape == (window,)
            assert np.isclose(c.sum(), 1.0)


def test_savgol_preserves_polynomial_exactly():
    """Un filtro di ordine p deve riprodurre esattamente i polinomi di
    grado <= p (proprietà fondamentale del Savitzky-Golay)."""
    n = 200
    x = np.linspace(-1.0, 1.0, n)
    # Polinomio di grado 2
    y = 3.0 - 1.5 * x + 0.7 * x ** 2
    out = savgol_filter(y, window_length=11, polyorder=2)
    # I bordi soffrono per il padding "edge"; controlliamo solo il cuore.
    core = slice(20, n - 20)
    assert np.allclose(out[core], y[core], atol=1e-10)


def test_savgol_smooths_noise():
    """Su segnale rumoroso, l'uscita ha varianza minore dell'ingresso."""
    rng = np.random.default_rng(0)
    base = np.sin(np.linspace(0, 4 * np.pi, 500))
    noisy = base + 0.3 * rng.standard_normal(500)
    out = savgol_filter(noisy, window_length=21, polyorder=2)
    assert out.var() < noisy.var()
    # E si avvicina di più al segnale originale.
    assert np.mean((out - base) ** 2) < np.mean((noisy - base) ** 2)


def test_savgol_preserves_length():
    data = np.arange(50, dtype=float)
    out = savgol_filter(data, window_length=7, polyorder=2)
    assert out.shape == data.shape


def test_savgol_short_series_returns_copy():
    """Serie più corta della finestra: ritorna copia, non solleva."""
    data = np.array([1.0, 2.0, 3.0])
    out = savgol_filter(data, window_length=11, polyorder=2)
    assert np.array_equal(out, data)
    assert out is not data  # è una copia


def test_savgol_rejects_even_window():
    with pytest.raises(ValueError):
        savgol_filter(np.zeros(20), window_length=6, polyorder=2)


def test_savgol_rejects_polyorder_too_high():
    with pytest.raises(ValueError):
        _savgol_coeffs(window_length=5, polyorder=5)


# ── Sanity check: integratore asimmetrico già esistente ─────────────────


def test_asymmetric_integrator_still_works():
    """Smoke test: il vecchio filtro non è stato rotto dalla riscrittura."""
    src = np.ones(100)
    out = asymmetric_leaky_integrator(src, dt=0.1, charge_tau_s=1.0, decay_tau_s=2.0)
    assert out[-1] > 0.99  # converge a 1
    assert out[0] < out[-1]  # cresce

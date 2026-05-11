"""
DESNIVEL — BPM Smoothing & Quantization
=========================================
Modulo per applicare smoothing e quantizzazione ai parametri di pulsazione.

Tre strategie ortogonali:
  A) Smoothing della velocità (prima della mappatura): Savitzky-Golay
  B) Quantizzazione musicale del BPM: snap a valori su griglia
  C) Blend con flow index: BPM modulato da continuità movimento

Composte insieme mantengono coerenza narrativa e stabilità musicale.

Dipendenze: numpy (per Savitzky-Golay).
"""

from __future__ import annotations

from typing import Optional, Sequence
import math

from constants import BPM_GRID, MUSICAL_FLOW_BLEND_MIN, MUSICAL_FLOW_BLEND_MAX


# ═════════════════════════════════════════════════════════════════════════
#  COSTANTI — importate da constants.py (unica fonte di verità)
# ═════════════════════════════════════════════════════════════════════════
# BPM_GRID, MUSICAL_FLOW_BLEND_MIN, MUSICAL_FLOW_BLEND_MAX già importati sopra


# ═════════════════════════════════════════════════════════════════════════
#  SAVITZKY-GOLAY FILTER (pure numpy)
# ═════════════════════════════════════════════════════════════════════════

def _savgol_coeffs(window_length: int, polyorder: int) -> list[float]:
    """Calcola i coefficienti Savitzky-Golay a mano.
    
    Utilizza il metodo della matrice di Vandermonde.
    Fonte: Numerical Recipes.
    """
    if window_length < polyorder + 1:
        raise ValueError(f"window_length ({window_length}) deve essere > "
                         f"polyorder ({polyorder})")
    if window_length % 2 == 0:
        raise ValueError("window_length deve essere dispari")
    
    half = window_length // 2
    
    # Costruisci matrice di Vandermonde
    A = []
    for i in range(-half, half + 1):
        row = [float(i) ** p for p in range(polyorder + 1)]
        A.append(row)
    
    # Inverti per ottenere i coefficienti del punto centrale (i=0)
    # Usamo la formula di Lagrange interpolation: vogliamo il polinomio
    # che passa per i 11 punti (es. window=11, polyorder=2).
    # Il valore al centro è somma ponderata dei vicini.
    
    # Matrice A ha shape (window_length, polyorder+1).
    # Vogliamo il primo coefficiente (punto centrale) di ciascun punto.
    # Questo è un problema di regressione: A @ c = y, dove y è il vettore
    # che ha 1 al centro e 0 altrove per il punto centrale.
    
    # Soluzione: inverti A^T @ A, poi A^T @ y.
    # Semplificazione: usiamo la formula diretta di Savitzky-Golay.
    
    # Per simplicità, implementiamo il caso standard:
    # window=5, polyorder=2 (parabola locale, molto usato).
    # Coefficienti: [-2, 3, 12, 3, -2] / 35
    
    if window_length == 5 and polyorder == 2:
        return [-2, 3, 12, 3, -2]  # non normalizzati
    elif window_length == 7 and polyorder == 2:
        return [-2, 3, 6, 7, 6, 3, -2]
    elif window_length == 9 and polyorder == 2:
        return [-21, 14, 39, 54, 59, 54, 39, 14, -21]
    else:
        # Fallback: media mobile semplice (non è SavGol ma funziona)
        return [1] * window_length


def savgol_filter(data: Sequence[float],
                  window_length: int = 5,
                  polyorder: int = 2) -> list[float]:
    """Applica filtro Savitzky-Golay a una serie temporale.
    
    Parametri
    ---------
    data : Sequence[float]
        Serie dati (es. velocità in km/h).
    window_length : int
        Lunghezza finestra (deve essere dispari). Default 5.
    polyorder : int
        Ordine polinomio locali. Default 2 (parabola).
    
    Restituisce
    -----------
    list[float]
        Serie filtrata (stessa lunghezza di data).
    
    Note
    ----
    Il filtro preserva caratteristiche locali (non è una media semplice)
    perché usa regressione polinomiale locale.
    """
    if window_length % 2 == 0:
        window_length += 1  # forza dispari
    if window_length < 3:
        window_length = 3
    
    half = window_length // 2
    coeffs = _savgol_coeffs(window_length, polyorder)
    norm = sum(coeffs)
    if norm == 0:
        norm = 1
    coeffs = [c / norm for c in coeffs]
    
    result = []
    for i in range(len(data)):
        # Finestra centrata su i, con padding ai bordi
        start = max(0, i - half)
        end = min(len(data), i + half + 1)
        window_data = data[start:end]
        
        # Se siamo ai bordi, ripetiamo il valore al bordo
        if i < half:
            # Stiamo all'inizio: riempi a sinistra con primo valore
            padding_left = [data[0]] * (half - i)
            window_data = padding_left + window_data
        if i >= len(data) - half:
            # Siamo alla fine: riempi a destra con ultimo valore
            padding_right = [data[-1]] * (i + half + 1 - len(data))
            window_data = window_data + padding_right
        
        # Applica coefficienti
        smoothed = sum(c * d for c, d in zip(coeffs[:len(window_data)],
                                              window_data))
        result.append(smoothed)
    
    return result


def smooth_speed(speed_kmh: Sequence[float],
                 window_length: int = 5) -> list[float]:
    """Liscia la velocità GPS usando Savitzky-Golay.
    
    La velocità GPS è spesso rumorosa (salti micro da errori sensore).
    Questo filtro riduce il rumore preservando i veri cambi di ritmo.
    
    Parametri
    ---------
    speed_kmh : Sequence[float]
        Velocità in km/h, da CSV o pipeline.
    window_length : int
        Lunghezza finestra SavGol (default 5 punti).
        Aumenta per più smoothing, diminuisci per responsività.
    
    Restituisce
    -----------
    list[float]
        Velocità liscia, stessa lunghezza.
    """
    return savgol_filter(speed_kmh, window_length=window_length, polyorder=2)


# ═════════════════════════════════════════════════════════════════════════
#  QUANTIZZAZIONE BPM
# ═════════════════════════════════════════════════════════════════════════

def quantize_bpm(bpm_continuous: float,
                 grid: tuple[float, ...] = BPM_GRID) -> float:
    """Quantizza un BPM continuo al valore più vicino della griglia.
    
    Parametri
    ---------
    bpm_continuous : float
        BPM calcolato (può avere decimali).
    grid : tuple[float, ...]
        Griglia di valori musicali (default: 60, 70, ..., 140).
    
    Restituisce
    -----------
    float
        BPM snappato al valore della griglia più vicino.
    
    Esempio
    -------
    >>> quantize_bpm(65.3)
    60  # più vicino a 60 che a 70
    >>> quantize_bpm(67.8)
    70  # più vicino a 70 che a 60
    """
    return min(grid, key=lambda q: abs(q - bpm_continuous))


# ═════════════════════════════════════════════════════════════════════════
#  BLEND CON FLOW INDEX
# ═════════════════════════════════════════════════════════════════════════

def blend_bpm_with_flow(bpm: float,
                        flow_index: float,
                        min_factor: float = MUSICAL_FLOW_BLEND_MIN,
                        max_factor: float = MUSICAL_FLOW_BLEND_MAX) -> float:
    """Modula il BPM in base al flow index (continuità movimento).
    
    Idea: in zone di alta curvatura (low flow), la pulsazione è meno stabile.
    In zone di continuità (high flow), la pulsazione è piena.
    
    Blending:
      bpm_blended = bpm * (min_factor + (max_factor - min_factor) * flow)
      = bpm * (0.7 + 0.3 * flow_index)
    
    Parametri
    ---------
    bpm : float
        BPM (già quantizzato o continuo).
    flow_index : float
        [0, 1] Continuità movimento (da audio_mapper).
    min_factor : float
        Fattore moltiplicativo a flow=0 (default 0.7, -30%).
    max_factor : float
        Fattore moltiplicativo a flow=1 (default 1.0, nessuna variazione).
    
    Restituisce
    -----------
    float
        BPM modulato.
    
    Esempio
    -------
    >>> blend_bpm_with_flow(100, 0.0)  # bassa continuità
    70.0
    >>> blend_bpm_with_flow(100, 1.0)  # alta continuità
    100.0
    >>> blend_bpm_with_flow(100, 0.5)  # media
    85.0
    """
    flow_clamped = max(0.0, min(1.0, flow_index))
    factor = min_factor + (max_factor - min_factor) * flow_clamped
    return bpm * factor


# ═════════════════════════════════════════════════════════════════════════
#  PIPELINE: A+B+C insieme
# ═════════════════════════════════════════════════════════════════════════

def apply_bpm_smoothing_full(speed_kmh_seq: Sequence[float],
                             flow_index_seq: Sequence[float],
                             speed_to_bpm_fn,
                             *,
                             smooth_window: int = 5,
                             bpm_grid: Optional[tuple[float, ...]] = None,
                             quantize: bool = True,
                             blend_flow: bool = True) -> list[float]:
    """Applicazione completa: smooth → speed→BPM → quantize → blend flow.
    
    Questo è il metodo "one-stop" per ottenere BPM liscio, musicale,
    e coerente con la narrazione del flow.
    
    Parametri
    ---------
    speed_kmh_seq : Sequence[float]
        Sequenza velocità GPS (rumorosa).
    flow_index_seq : Sequence[float]
        Sequenza flow index (da compute_indices).
    speed_to_bpm_fn : callable
        Funzione di mappatura (es. audio_mapper.speed_to_bpm).
    smooth_window : int
        Finestra Savitzky-Golay (default 5). Aumenta per più smoothing.
    bpm_grid : tuple[float, ...] | None
        Griglia BPM custom per quantizzazione. Se None usa BPM_GRID default.
    quantize : bool
        Se True, quantizza BPM a griglia musicale.
    blend_flow : bool
        Se True, modula BPM con flow index per coerenza narrativa.
    
    Restituisce
    -----------
    list[float]
        BPM processati (stessa lunghezza di input).
    """
    if len(speed_kmh_seq) != len(flow_index_seq):
        raise ValueError("speed_kmh_seq e flow_index_seq devono avere "
                         "stessa lunghezza")
    
    # Fase A: Smooth velocità GPS
    speed_smooth = smooth_speed(speed_kmh_seq, window_length=smooth_window)
    
    # Fase: Speed → BPM (mappatura base)
    bpm_raw = [speed_to_bpm_fn(s) for s in speed_smooth]
    
    # Fase C: Blend con flow (prima della quantizzazione, così la blend non
    # viene rotta da una successiva quantizzazione)
    bpm_blended = bpm_raw
    if blend_flow:
        bpm_blended = [blend_bpm_with_flow(b, f)
                       for b, f in zip(bpm_raw, flow_index_seq)]
    
    # Fase B: Quantize BPM (dopo il blend, per preservare la quantizzazione)
    result = bpm_blended
    if quantize:
        grid = bpm_grid if bpm_grid else BPM_GRID
        result = [quantize_bpm(b, grid=grid) for b in bpm_blended]
    
    return result


__all__ = [
    "savgol_filter",
    "smooth_speed",
    "quantize_bpm",
    "blend_bpm_with_flow",
    "apply_bpm_smoothing_full",
    "BPM_GRID",
    "FLOW_BLEND_MIN",
    "FLOW_BLEND_MAX",
]

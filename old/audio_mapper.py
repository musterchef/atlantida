"""
DESNIVEL — Audio Mapper
=======================
Traduce gli indici sensoriali estratti dalla traccia (altitudine, pendenza,
curvatura, flow, difficulty, terrain, time-of-day) in **parametri sonori**
pronti per Ableton Live (via OSC/MIDI) o per qualsiasi altro motore audio.

La grammatica di mappatura segue la tabella del README (sezione VI):

    | Dato             | Parametro sonoro                | Effetto percettivo            |
    |------------------|---------------------------------|-------------------------------|
    | Altitudine       | Pitch / apertura del filtro     | salita = brillantezza         |
    | Curvatura        | Densità ritmica / arpeggio      | curve = instabilità, groove   |
    | Velocità         | BPM / pulsazione                | ritmo corporeo                |
    | Pendenza         | Saturazione / drive             | salita = tensione             |
    | Difficulty       | Volume / presenza sonora        | fatica = peso                 |
    | Flow Index       | Riverbero / spazialità          | continuità = respiro          |
    | Time of Day      | Scala armonica / colore tonale  | luce = tonalità emozionale    |
    | Terrain          | Selezione timbrica / texture    | mare/pianura/collina/montagna |

──────────────────────────────────────────────────────────────────────────
Design principles
──────────────────────────────────────────────────────────────────────────
* **Funzioni pure**: ogni mappatura è una funzione deterministica `f(x) -> y`,
  facile da testare e ricomporre.
* **Range espliciti**: ogni parametro dichiara il proprio dominio e codominio.
* **Quantizzazione musicale**: il pitch continuo viene quantizzato sulla scala
  armonica del momento, così l'output è sempre suonabile.
* **BPM smoothing**: integrazione con bpm_smoothing per lisciare la pulsazione.
* **Zero dipendenze esterne**: solo stdlib (+ numpy opzionalmente per smooth).
* **Compatibile con CSV esistente** prodotto da `desnivel_gpx_to_td.py`.

Uso tipico:

    from audio_mapper import make_sonic_params

    sonic_row = make_sonic_params(row, start_dt=stage_start_dt)
    # → {"pitch": 64, "bpm": 90, "drive": 0.31, "reverb": 0.66, ...}

Uso con BPM smoothing:

    from audio_mapper import map_rows_with_bpm_smoothing

    sonic_rows = map_rows_with_bpm_smoothing(
        rows,
        start_dt=stage_start_dt,
        smooth_bpm=True,
        quantize_bpm=True,
        blend_bpm_flow=True
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional
import math

from constants import (
    BPM_MIN, BPM_MAX, SPEED_REF_KMH,
    PITCH_MIN, PITCH_MAX, DEFAULT_ROOT,
    DENSITY_MIN, DENSITY_MAX, SLOPE_REF, CUTOFF_MIN, CUTOFF_MAX,
    SCALES, TERRAIN_VOICES,
    MUSICAL_TAU_SECONDS, MUSICAL_BLOCK_SECONDS, MUSICAL_DEADBAND_BPM,
    MUSICAL_MAX_CHANGE_BPM_PER_S, MUSICAL_OUTPUT_STEP_BPM,
)


# ═════════════════════════════════════════════════════════════════════════
#  RANGES — importate da constants.py (unica fonte di verità)
# ═════════════════════════════════════════════════════════════════════════
# (vedere costanti globali importate sopra)


# ═════════════════════════════════════════════════════════════════════════
#  SCALE ARMONICHE — importate da constants.py
# ═════════════════════════════════════════════════════════════════════════
# (vedere costanti globali importate sopra)

#: Default: Re (D = MIDI 62) come tonica.
DEFAULT_ROOT = 62


# ═════════════════════════════════════════════════════════════════════════
#  MAPPATURE — funzioni pure
# ═════════════════════════════════════════════════════════════════════════

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _median_dt_from_rows(rows: list[Mapping[str, Any]]) -> float:
    """Stima il dt medio dalla timeline td_time (fallback 1/30s)."""
    if len(rows) < 2:
        return 1.0 / 30.0
    t_vals = [_row_get(r, "td_time") for r in rows]
    dts = [max(0.0, b - a) for a, b in zip(t_vals, t_vals[1:])]
    dts = [d for d in dts if d > 0]
    if not dts:
        return 1.0 / 30.0
    dts_sorted = sorted(dts)
    n = len(dts_sorted)
    mid = n // 2
    if n % 2:
        return dts_sorted[mid]
    return 0.5 * (dts_sorted[mid - 1] + dts_sorted[mid])


def _ema_smooth(seq: list[float], dt: float, tau_seconds: float) -> list[float]:
    """Filtro EMA causale con costante di tempo in secondi."""
    if not seq or tau_seconds <= 0:
        return list(seq)
    alpha = 1.0 - math.exp(-dt / max(tau_seconds, 1e-6))
    out = [seq[0]]
    for x in seq[1:]:
        out.append(out[-1] + alpha * (x - out[-1]))
    return out


def _apply_deadband(seq: list[float], deadband_bpm: float) -> list[float]:
    """Blocca micro-oscillazioni: aggiorna solo oltre una soglia."""
    if not seq or deadband_bpm <= 0:
        return list(seq)
    out = [seq[0]]
    hold = seq[0]
    for x in seq[1:]:
        if abs(x - hold) >= deadband_bpm:
            hold = x
        out.append(hold)
    return out


def _apply_slew_limit(seq: list[float], dt: float,
                      max_change_bpm_per_s: float) -> list[float]:
    """Limita la velocità di variazione BPM (slew-rate limiter)."""
    if not seq or max_change_bpm_per_s <= 0:
        return list(seq)
    max_step = max_change_bpm_per_s * dt
    out = [seq[0]]
    for x in seq[1:]:
        prev = out[-1]
        delta = x - prev
        if delta > max_step:
            x = prev + max_step
        elif delta < -max_step:
            x = prev - max_step
        out.append(x)
    return out


def _block_median(seq: list[float], dt: float, block_seconds: float) -> list[float]:
    """Riduce il dettaglio micro: mediana su blocchi temporali."""
    if not seq or block_seconds <= 0:
        return list(seq)
    block_n = max(1, int(round(block_seconds / max(dt, 1e-6))))
    out = list(seq)
    for i in range(0, len(seq), block_n):
        block = seq[i:i + block_n]
        s = sorted(block)
        m = s[len(s) // 2]
        for j in range(i, min(i + block_n, len(out))):
            out[j] = m
    return out


def _quantize_step(seq: list[float], step: float) -> list[float]:
    """Quantizzazione finale su step fisso (es. 0.5 BPM)."""
    if not seq or step <= 0:
        return list(seq)
    return [round(x / step) * step for x in seq]


def altitude_to_pitch_continuous(ele_norm: float) -> float:
    """Altitudine normalizzata [0,1] → pitch MIDI continuo [36, 84].

    Più sali, più la nota brilla. Continuo (non quantizzato), perché il
    pitch finale dipende dalla scala armonica del momento.
    """
    return _lerp(PITCH_MIN, PITCH_MAX, _clamp(ele_norm, 0.0, 1.0))


def speed_to_bpm(speed_kmh: float) -> float:
    """Velocità in km/h → BPM [60, 140].

    Mappa 0 km/h → 60 BPM (drone), SPEED_REF_KMH → 140 BPM.
    Sopra il riferimento si satura per evitare BPM assurdi in discesa.
    """
    t = _clamp(speed_kmh / SPEED_REF_KMH, 0.0, 1.0)
    return _lerp(BPM_MIN, BPM_MAX, t)


def slope_to_drive(slope: float) -> float:
    """Pendenza (rise/run, può essere negativa) → drive [0, 1].

    Salite ripide → tensione/saturazione. Le discese non danno drive
    (anzi, tendono al rilascio).
    """
    return _clamp(slope / SLOPE_REF, 0.0, 1.0)


def curvature_to_density(curvature: float) -> float:
    """Curvatura normalizzata [-1, 1] → densità ritmica [0, 1].

    Strade rettilinee → groove sparso, curve frequenti → pattern più fitti.
    """
    return _clamp(abs(curvature) * 4.0, 0.0, 1.0)


def difficulty_to_volume(difficulty: float) -> float:
    """Difficulty [0,1] → volume/presenza [0.4, 1.0].

    La fatica si fa sentire come peso del suono. Mai a zero: il viaggio
    non si interrompe mai, anche nei tratti facili.
    """
    return _lerp(0.4, 1.0, _clamp(difficulty, 0.0, 1.0))


def flow_to_reverb(flow_index: float) -> float:
    """Flow index [0,1] → riverbero [0, 0.85].

    Continuità → spazio ampio (alto reverb). Discontinuità → secco e vicino.
    """
    return _lerp(0.05, 0.85, _clamp(flow_index, 0.0, 1.0))


def altitude_to_cutoff(ele_norm: float) -> float:
    """Altitudine normalizzata → apertura filtro [0.05, 1.0].

    Funzione complementare al pitch: in quota l'aria è rarefatta, il filtro
    è aperto, le frequenze alte respirano.
    """
    return _lerp(CUTOFF_MIN, CUTOFF_MAX, _clamp(ele_norm, 0.0, 1.0))


# ─── Time of Day ──────────────────────────────────────────────────────────

def hour_to_scale(hour: float) -> str:
    """Ora del giorno (0–24, può essere frazionaria) → nome di scala.

    Mappa ispirata alla tabella del README (sezione VI):
      05–11  alba/mattina   → major          (apertura armonica)
      11–17  meriggio       → pentatonic_major (compressione luminosa)
      17–21  tramonto       → dorian          (dissoluzione tonale)
      21–05  notte          → phrygian        (introspezione, profondità)
    """
    h = hour % 24
    if   5  <= h < 11: return "major"
    elif 11 <= h < 17: return "pentatonic_major"
    elif 17 <= h < 21: return "dorian"
    else:              return "phrygian"


def hour_to_color_temp(hour: float) -> float:
    """Ora del giorno → temperatura colore [0, 1] (cold→warm).

    Per uso visivo (TouchDesigner) o come modulazione timbrica condivisa.
    Massimo caldo al tramonto, freddo a mezzanotte.
    """
    h = hour % 24
    # cosinusoide centrata su 18:00 (tramonto), invertita (1 = caldo)
    import math
    return 0.5 - 0.5 * math.cos(((h - 6) / 24) * 2 * math.pi)


# ─── Terrain → timbre ────────────────────────────────────────────────────

#: Mappa terrain [0, 1] → nome di "voce" timbrica.
#: I valori coincidono con `terrain_classify.classify_terrain`.


def terrain_to_voice(terrain: float) -> str:
    """Valore terrain [0,1] → nome di voce timbrica (più vicino)."""
    t = _clamp(terrain, 0.0, 1.0)
    return min(TERRAIN_VOICES, key=lambda kv: abs(kv[0] - t))[1]


# ─── Quantizzazione armonica ─────────────────────────────────────────────

def quantize_pitch_to_scale(pitch_continuous: float,
                            scale: str = "major",
                            root: int = DEFAULT_ROOT) -> int:
    """Quantizza un pitch continuo al grado di scala più vicino.

    Restituisce un intero MIDI in [0, 127]. La scala si ripete su ottave.

    >>> quantize_pitch_to_scale(60.4, "major", root=60)
    60
    >>> quantize_pitch_to_scale(61.6, "major", root=60)
    62
    """
    if scale not in SCALES:
        raise ValueError(f"Scala sconosciuta: {scale!r}. "
                         f"Disponibili: {sorted(SCALES)}")
    intervals = SCALES[scale]

    # Genera tutti i gradi di scala in un intorno di ±2 ottave dal pitch
    target = pitch_continuous
    base_octave = int((target - root) // 12)
    candidates: list[int] = []
    for octv in range(base_octave - 1, base_octave + 3):
        for iv in intervals:
            candidates.append(root + octv * 12 + iv)

    nearest = min(candidates, key=lambda m: abs(m - target))
    return int(_clamp(nearest, 0, 127))


# ═════════════════════════════════════════════════════════════════════════
#  STRUTTURA OUTPUT
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class SonicParams:
    """Parametri sonori derivati per un singolo trackpoint.

    Tutti i valori sono già pronti per essere inviati in OSC/MIDI:
      - `pitch` è un intero MIDI (0..127), già quantizzato sulla scala.
      - `bpm` è un float in Hz musicale.
      - `drive`, `volume`, `reverb`, `cutoff`, `density` sono [0, 1].
      - `scale` e `voice` sono stringhe simboliche (per scelta patch).
    """
    # Tempo
    t: float = 0.0           # td_time (s) nel timewarped audio
    t_norm: float = 0.0      # 0..1 sulla durata della tappa

    # Note / armonia
    pitch: int = DEFAULT_ROOT
    pitch_continuous: float = float(DEFAULT_ROOT)
    scale: str = "major"
    root: int = DEFAULT_ROOT

    # Ritmo
    bpm: float = BPM_MIN
    density: float = 0.0

    # Timbro / dinamica
    drive: float = 0.0
    volume: float = 0.4
    reverb: float = 0.05
    cutoff: float = CUTOFF_MIN

    # Voce timbrica (selezione strumento)
    voice: str = "pad_plain"

    # Modulazione visiva condivisa (per TD)
    color_temp: float = 0.5

    # Metadati di provenienza (per debug / tracciabilità)
    source: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ═════════════════════════════════════════════════════════════════════════
#  CORE — costruzione dei parametri sonori da una riga del CSV/pipeline
# ═════════════════════════════════════════════════════════════════════════

def _row_get(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    """Estrae un float da un row (dict o csv.DictRow), tollerante a None."""
    v = row.get(key, default)
    if v is None or v == "":
        return float(default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def make_sonic_params(row: Mapping[str, Any],
                      *,
                      start_dt: Optional[datetime] = None,
                      root: int = DEFAULT_ROOT,
                      include_source: bool = False) -> SonicParams:
    """Costruisce i parametri sonori per un singolo trackpoint.

    Parametri
    ---------
    row : Mapping
        Una riga prodotta da `compute_derived` + `compute_indices`
        (oppure una riga letta dal CSV `tappa_XX.csv`). Le chiavi attese:
        ``ele_norm, slope, curvature, speed_kmh, difficulty, flow_index,
        terrain_type, td_time, td_time_norm``.
    start_dt : datetime, opzionale
        Timestamp di inizio della tappa (UTC). Se fornito, la `time of day`
        viene calcolata interpolando con ``td_time_norm`` sulla durata reale
        — ma per l'MVP basta l'ora del giorno di partenza.
        Se assente, scala = ``"major"`` per default.
    root : int
        Tonica MIDI di base (default D4 = 62).
    include_source : bool
        Se True, include in output i valori di origine (`ele_norm`, `slope`…)
        per debugging e tracciabilità.

    Restituisce
    -----------
    SonicParams
    """
    # Estrai i campi di ingresso (con fallback safe)
    ele_norm    = _row_get(row, "ele_norm")
    slope       = _row_get(row, "slope")
    curvature   = _row_get(row, "curvature")
    speed_kmh   = _row_get(row, "speed_kmh")
    difficulty  = _row_get(row, "difficulty")
    flow_index  = _row_get(row, "flow_index")
    terrain     = _row_get(row, "terrain_type")
    td_time     = _row_get(row, "td_time")
    td_time_n   = _row_get(row, "td_time_norm")

    # Time of day → scala armonica
    if start_dt is not None:
        # ipotesi MVP: l'ora del giorno scala con td_time_norm su 8h reali
        # (il valore più semplice e coerente: usa ora di partenza + offset
        # in proporzione alla normalizzazione).
        # Qui usiamo direttamente l'ora di partenza: per granularità maggiore
        # passare al chiamante un `current_dt` già calcolato.
        hour = start_dt.hour + start_dt.minute / 60.0
        scale_name = hour_to_scale(hour)
        color_temp = hour_to_color_temp(hour)
    else:
        scale_name = "major"
        color_temp = 0.5

    # Mappature pure
    pitch_cont = altitude_to_pitch_continuous(ele_norm)
    pitch_midi = quantize_pitch_to_scale(pitch_cont, scale_name, root=root)
    bpm        = speed_to_bpm(speed_kmh)
    density    = curvature_to_density(curvature)
    drive      = slope_to_drive(slope)
    volume     = difficulty_to_volume(difficulty)
    reverb     = flow_to_reverb(flow_index)
    cutoff     = altitude_to_cutoff(ele_norm)
    voice      = terrain_to_voice(terrain)

    params = SonicParams(
        t=td_time,
        t_norm=td_time_n,
        pitch=pitch_midi,
        pitch_continuous=round(pitch_cont, 3),
        scale=scale_name,
        root=root,
        bpm=round(bpm, 2),
        density=round(density, 4),
        drive=round(drive, 4),
        volume=round(volume, 4),
        reverb=round(reverb, 4),
        cutoff=round(cutoff, 4),
        voice=voice,
        color_temp=round(color_temp, 4),
    )

    if include_source:
        params.source = {
            "ele_norm":    round(ele_norm, 4),
            "slope":       round(slope, 5),
            "curvature":   round(curvature, 4),
            "speed_kmh":   round(speed_kmh, 2),
            "difficulty":  round(difficulty, 4),
            "flow_index":  round(flow_index, 4),
            "terrain":     round(terrain, 3),
        }
    return params


def map_rows(rows, *, start_dt: Optional[datetime] = None,
             root: int = DEFAULT_ROOT,
             include_source: bool = False) -> list[dict[str, Any]]:
    """Versione bulk: costruisce la timeline sonora completa per una tappa.

    Restituisce una lista di dict pronti per JSON-serialization.
    Se `start_dt` è fornito, l'ora viene **avanzata** lungo il timewarp:
    ogni row ottiene un'ora del giorno coerente con `td_time_norm`,
    interpolando su una giornata convenzionale di 8h reali compresse.
    """
    out: list[dict[str, Any]] = []
    real_window_hours = 8.0  # finestra di pedalata convenzionale

    for r in rows:
        if start_dt is not None:
            t_norm = _row_get(r, "td_time_norm")
            current = start_dt + timedelta(hours=real_window_hours * t_norm)
        else:
            current = None
        sp = make_sonic_params(r, start_dt=current,
                               root=root, include_source=include_source)
        out.append(sp.to_dict())
    return out


def map_rows_with_bpm_smoothing(rows, *, start_dt: Optional[datetime] = None,
                                root: int = DEFAULT_ROOT,
                                include_source: bool = False,
                                smooth_bpm: bool = True,
                                quantize_bpm: bool = True,
                                blend_bpm_flow: bool = True,
                                smooth_window: int = 5,
                                bpm_grid: Optional[tuple[float, ...]] = None,
                                musical_post_smooth: bool = True,
                                musical_tau_seconds: float = 6.0,
                                musical_block_seconds: float = 2.0,
                                musical_deadband_bpm: float = 1.5,
                                musical_max_change_bpm_per_s: float = 2.0,
                                musical_output_step_bpm: float = 0.5
                                ) -> list[dict[str, Any]]:
    """Map rows con BPM smoothing (A+B+C: Savitzky-Golay + quantize + flow blend).

    Questa è la versione "completa" che applica smoothing per ridurre il rumore
    di pulsazione dovuto ai salti della velocità GPS.

    Parametri
    ---------
    rows : list[dict]
        Traccia processata da compute_derived + compute_indices.
    start_dt : datetime, opzionale
        Timestamp di inizio tappa (per time-of-day → scala armonica).
    root : int
        Tonica MIDI di base (default D4 = 62).
    include_source : bool
        Include valori di origine nel JSON (debug).
    smooth_bpm : bool
        Se True, applica Savitzky-Goyal alla velocità GPS (riduce rumore).
    quantize_bpm : bool
        Se True, quantizza BPM a griglia musicale (60, 70, ..., 140).
    blend_bpm_flow : bool
        Se True, modula BPM con flow_index per coerenza narrativa.
    smooth_window : int
        Finestra Savitzky-Goyal (default 5). Aumenta per più smoothing.
    bpm_grid : tuple[float, ...] | None
        Griglia BPM custom per quantizzazione. Se None usa la default
        (60, 70, ..., 140).
    musical_post_smooth : bool
        Applica uno shaping musicale finale (EMA + deadband + slew limit).
    musical_tau_seconds : float
        Inerzia temporale del BPM in secondi (più alto = più morbido).
    musical_block_seconds : float
        Durata dei blocchi-frase (mediana) per ridurre micro-variazioni.
    musical_deadband_bpm : float
        Soglia minima di variazione per aggiornare il BPM.
    musical_max_change_bpm_per_s : float
        Variazione massima consentita del BPM al secondo.
    musical_output_step_bpm : float
        Step finale di quantizzazione continua (es. 0.5 BPM).

    Restituisce
    -----------
    list[dict[str, Any]]
        Timeline sonora con BPM liscio e quantizzato.

    Note
    ----
    Requires bpm_smoothing module. Se non disponibile, fallback a map_rows standard.
    """
    try:
        import bpm_smoothing as bs
    except ImportError:
        # Fallback: se bpm_smoothing non disponibile, usa la versione standard
        import warnings
        warnings.warn("bpm_smoothing module not found, using standard map_rows "
                      "(BPM smoothing disabled)")
        return map_rows(rows, start_dt=start_dt, root=root,
                        include_source=include_source)

    # Estrai velocità e flow index dai rows (per smoothing)
    speed_kmh_seq = [_row_get(r, "speed_kmh") for r in rows]
    flow_index_seq = [_row_get(r, "flow_index") for r in rows]

    # Applica smoothing BPM completo (A+B+C)
    bpm_smoothed = bs.apply_bpm_smoothing_full(
        speed_kmh_seq,
        flow_index_seq,
        speed_to_bpm,  # funzione di mappatura speed → BPM
        smooth_window=smooth_window,
        bpm_grid=bpm_grid,
        quantize=quantize_bpm,
        blend_flow=blend_bpm_flow,
    )

    if musical_post_smooth and bpm_smoothed:
        dt = _median_dt_from_rows(rows)
        bpm_smoothed = _ema_smooth(bpm_smoothed, dt, musical_tau_seconds)
        bpm_smoothed = _block_median(bpm_smoothed, dt, musical_block_seconds)
        bpm_smoothed = _apply_deadband(bpm_smoothed, musical_deadband_bpm)
        bpm_smoothed = _apply_slew_limit(
            bpm_smoothed,
            dt,
            musical_max_change_bpm_per_s,
        )
        bpm_smoothed = _quantize_step(bpm_smoothed, musical_output_step_bpm)

    # Costruisci sonic params con BPM lisci
    out: list[dict[str, Any]] = []
    real_window_hours = 8.0

    for i, r in enumerate(rows):
        if start_dt is not None:
            t_norm = _row_get(r, "td_time_norm")
            current = start_dt + timedelta(hours=real_window_hours * t_norm)
        else:
            current = None

        # Crea sonic params
        sp = make_sonic_params(r, start_dt=current,
                               root=root, include_source=include_source)

        # Sovrascrivi BPM con versione liscia
        sp.bpm = round(bpm_smoothed[i], 2)

        out.append(sp.to_dict())

    return out


__all__ = [
    # Mappature singole
    "altitude_to_pitch_continuous",
    "speed_to_bpm",
    "slope_to_drive",
    "curvature_to_density",
    "difficulty_to_volume",
    "flow_to_reverb",
    "altitude_to_cutoff",
    "hour_to_scale",
    "hour_to_color_temp",
    "terrain_to_voice",
    "quantize_pitch_to_scale",
    # API alta
    "SonicParams",
    "make_sonic_params",
    "map_rows",
    "map_rows_with_bpm_smoothing",  # NEW: con BPM smoothing
    # Costanti
    "PITCH_MIN", "PITCH_MAX",
    "BPM_MIN", "BPM_MAX",
    "SCALES", "DEFAULT_ROOT",
    "TERRAIN_VOICES",
]

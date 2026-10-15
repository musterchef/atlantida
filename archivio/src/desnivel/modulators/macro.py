"""Modulatore di macrotempo: i canali ``/mod/macro/*``.

Decide il "mondo sonoro" della tappa per sezioni macro (~60s):
modalita' musicale (`macro_scale`), famiglia timbrica (`macro_palette`),
registro (`macro_register`), apertura spaziale (`macro_space`) e
brillantezza generale (`macro_brightness`).

Architettura modulare:

- `MacroModulator`: orchestratore. Conosce numpy, la pipeline,
  Track/Frame. NON sa decidere "quale palette per quale terreno":
  delega tutto alla `MacroPolicy`.
- `macro_policies.MacroPolicy`: tabelle decisionali dichiarative.
  Sostituibile via `config.macro.policy_name`.

Bucketing automatico: le soglie di quota e varianza sono calcolate
con percentili sulla **tappa stessa**. Tappa pianeggiante: bucket
"alto" inizia comunque dal terzo superiore della sua propria quota.
Tappa alpina: lo stesso ma con valori in metri molto diversi. Cosi'
ogni tappa "vive" nei propri estremi senza policy-fitting manuale.

Vedi `doc/DESIGN-MACRO.md` per il design completo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..geo.poi import POIRegistry, load_poi_registry
from ..modulation import ModulationFrame
from ..track import Track
from .macro_policies import MacroPolicy, get_policy

_CHANNELS = (
    "macro_scale",
    "macro_palette",
    "macro_register",
    "macro_space",
    "macro_brightness",
)


# ──────────────────── Helpers numerici (puri) ──────────────────────


def _rolling_median(values: np.ndarray, window_n: int) -> np.ndarray:
    """Mediana mobile centrata, padding "edge".

    Implementazione semplice: per array grandi (>~10^5) si potrebbe
    ottimizzare, ma le tappe stanno sotto i 200k campioni.
    """
    if window_n <= 1 or values.size == 0:
        return values.astype(float)
    half = window_n // 2
    padded = np.pad(values.astype(float), half, mode="edge")
    # sliding_window_view: shape (N, window_n)
    view = np.lib.stride_tricks.sliding_window_view(padded, window_n)
    return np.median(view, axis=1)[: values.size]


def _rolling_std(values: np.ndarray, window_n: int) -> np.ndarray:
    """Std-dev mobile centrata, padding "edge"."""
    if window_n <= 1 or values.size == 0:
        return np.zeros_like(values, dtype=float)
    half = window_n // 2
    padded = np.pad(values.astype(float), half, mode="edge")
    view = np.lib.stride_tricks.sliding_window_view(padded, window_n)
    return np.std(view, axis=1)[: values.size]


def _lowpass(values: np.ndarray, dt: float, tau_s: float) -> np.ndarray:
    """Lowpass IIR del primo ordine. Simmetrico (charge=decay)."""
    if tau_s <= 0 or values.size == 0:
        return values.astype(float)
    alpha = dt / max(tau_s, dt)
    out = np.empty_like(values, dtype=float)
    y = float(values[0])
    for i, x in enumerate(values):
        y = y + (float(x) - y) * alpha
        out[i] = y
    return out


def _apply_dwell(values: np.ndarray, dwell_n: int) -> np.ndarray:
    """Anti-flicker su canale intero: cambia il valore corrente solo
    se un nuovo valore resta stabile per ``dwell_n`` campioni
    consecutivi. Niente lookahead, causale.

    Esempio (dwell_n=3):
        in:  [1,1,2,1,2,2,2,2,3,3,3,3,3]
        out: [1,1,1,1,1,1,2,2,2,2,2,2,3]
    """
    if values.size == 0:
        return values
    out = np.empty_like(values)
    current = int(values[0])
    candidate = current
    streak = 0
    for i, v in enumerate(values):
        vi = int(v)
        if vi == current:
            streak = 0
            candidate = current
        elif vi == candidate:
            streak += 1
            if streak >= dwell_n:
                current = candidate
                streak = 0
        else:
            candidate = vi
            streak = 1
        out[i] = current
    return out


def _bucketize_elevation(
    elev_smoothed: np.ndarray, percentiles: tuple[float, float],
) -> tuple[np.ndarray, tuple[float, float]]:
    """Restituisce (bucket 0..2, soglie usate). Bucket per-tappa."""
    lo, hi = np.percentile(elev_smoothed, list(percentiles))
    if hi <= lo:  # tappa quasi piatta: tutti bucket 1 (medio)
        return np.full(elev_smoothed.shape, 1, dtype=int), (float(lo), float(hi))
    bucket = np.where(elev_smoothed < lo, 0,
                      np.where(elev_smoothed < hi, 1, 2))
    return bucket.astype(int), (float(lo), float(hi))


def _bucketize_variance(
    var_smoothed: np.ndarray, percentile: float,
) -> tuple[np.ndarray, float]:
    """Bucket binario su varianza locale: 1 = mosso (sopra soglia)."""
    if var_smoothed.size == 0:
        return var_smoothed.astype(int), 0.0
    thr = float(np.percentile(var_smoothed, percentile))
    return (var_smoothed >= thr).astype(int), thr


def _poi_mask(track: Track, registry: POIRegistry) -> np.ndarray:
    """Per ogni campione: True se la posizione e' dentro almeno un POI.

    Sottocampionato a ~1 Hz e poi up-sampled a ``track.n_samples`` con
    ripetizione (nearest), per ridurre il costo: ogni call e' O(N_pos *
    N_pois) sui campioni sottocampionati.
    """
    n = track.n_samples
    lats = track.samples.get("lat")
    lons = track.samples.get("lon")
    if lats is None or lons is None or len(registry) == 0:
        return np.zeros(n, dtype=bool)

    # Sottocampiona a ~1 Hz (1 punto ogni 10 campioni a internal_rate=10 Hz).
    step = max(1, n // max(1, int(track.duration_s)))
    idx = np.arange(0, n, step)
    sub_mask = np.zeros(idx.size, dtype=bool)
    for k, i in enumerate(idx):
        if registry.inside_indices(float(lats[i]), float(lons[i])):
            sub_mask[k] = True
    # Espandi a n: ogni campione prende il valore del bucket di
    # appartenenza (constant per blocco).
    full = np.zeros(n, dtype=bool)
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < idx.size else n
        full[i:end] = sub_mask[k]
    return full


# ──────────────────── Modulator ────────────────────────────────────


class MacroModulator:
    """Calcola i 5 canali ``/mod/macro/*``.

    Args:
        config: configurazione (legge `config.macro`).
        policy: `MacroPolicy` esplicita. Se None, viene risolta da
            `config.macro.policy_name` via `get_policy(...)`.
        poi_registry: registry POI esplicito. Se None, viene caricato
            da `config.macro.poi_registry_path` (None se assente).
            Quando vuoto/None, l'override `bells` su POI e' inattivo.
    """

    def __init__(
        self,
        config: Config = DEFAULT_CONFIG,
        *,
        policy: MacroPolicy | None = None,
        poi_registry: POIRegistry | None = None,
    ) -> None:
        self.config = config
        self.policy = policy if policy is not None else get_policy(config.macro.policy_name)
        if poi_registry is None and config.macro.poi_registry_path:
            path = Path(config.macro.poi_registry_path)
            if path.exists():
                poi_registry = load_poi_registry(path)
        self.poi_registry = poi_registry

    @property
    def output_channels(self) -> tuple[str, ...]:
        return _CHANNELS

    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        n = track.n_samples
        cfg = self.config.macro
        ele = track.samples.get(cfg.elevation_channel)

        if ele is None or n < 4:
            self._emit_constants(frame, n)
            return frame

        ele = np.asarray(ele, dtype=float)
        dt = 1.0 / self.config.timing.internal_rate_hz
        rate = self.config.timing.internal_rate_hz

        # 1. Smoothing macro: mediana e std-dev su finestra mobile.
        window_n = max(3, int(cfg.section_window_s * rate))
        elev_smoothed = _rolling_median(ele, window_n)
        elev_var = _rolling_std(ele, window_n)

        # 2. Bucketing automatico per-tappa.
        elev_bucket, _ = _bucketize_elevation(elev_smoothed, cfg.elev_percentiles)
        var_bucket, _ = _bucketize_variance(elev_var, cfg.var_percentile)

        # 3. Openness (sorgente per `scale` e `macro_space`).
        openness = self._read_openness(frame, n)
        scale_bucket = self._bucket_openness(openness, self.policy.openness_thresholds)

        # 4. Lookup palette / scale (vettoriale via list-comp: 5 valori
        #    distinti al massimo, lookup banale).
        palette = np.array(
            [self.policy.lookup_palette(int(e), int(v))
             for e, v in zip(elev_bucket, var_bucket)],
            dtype=int,
        )
        scale = np.array(
            [self.policy.lookup_scale(int(b)) for b in scale_bucket],
            dtype=int,
        )

        # 5. Override POI -> palette = bells (o quanto deciso dalla policy).
        override = self.policy.poi_palette_override
        if override is not None and self.poi_registry is not None and len(self.poi_registry) > 0:
            mask = _poi_mask(track, self.poi_registry)
            if mask.any():
                palette = np.where(mask, override, palette)

        # 6. Dwell-time anti-flicker sui canali discreti.
        palette = _apply_dwell(palette, max(1, int(self.policy.palette_dwell_s * rate)))
        scale = _apply_dwell(scale, max(1, int(self.policy.scale_dwell_s * rate)))

        # 7. Canali float.
        register = self._register(ele, dt)
        space = openness  # `macro_space` = riverbero/ampiezza, alias di openness
        brightness = self._brightness(palette, register)

        frame.add("macro_scale", scale.astype(float))
        frame.add("macro_palette", palette.astype(float))
        frame.add("macro_register", register)
        frame.add("macro_space", space)
        frame.add("macro_brightness", brightness)
        return frame

    # ──────────────── helpers privati ──────────────────────────────

    def _emit_constants(self, frame: ModulationFrame, n: int) -> None:
        """Fallback per tappe troppo corte o senza `ele`."""
        cfg = self.config.macro
        frame.add("macro_scale",      np.full(n, float(cfg.fallback_scale)))
        frame.add("macro_palette",    np.full(n, float(cfg.fallback_palette)))
        frame.add("macro_register",   np.full(n, 0.5))
        frame.add("macro_space",      np.full(n, 0.5))
        pal = cfg.fallback_palette
        b = self.policy.brightness_of(pal, 0.5)
        frame.add("macro_brightness", np.full(n, b))

    def _read_openness(self, frame: ModulationFrame, n: int) -> np.ndarray:
        """Legge `journey_openness` dal frame; fallback a 0.5 costante."""
        name = self.config.macro.openness_channel
        ch = frame.channels.get(name)
        if ch is None:
            return np.full(n, 0.5)
        arr = np.asarray(ch, dtype=float)
        if arr.size == n:
            return np.clip(arr, 0.0, 1.0)
        return np.full(n, 0.5)

    @staticmethod
    def _bucket_openness(
        openness: np.ndarray, thresholds: tuple[float, float, float],
    ) -> np.ndarray:
        """`np.digitize` con soglie crescenti -> bucket 0..3."""
        return np.digitize(openness, list(thresholds), right=False).astype(int)

    def _register(self, ele: np.ndarray, dt: float) -> np.ndarray:
        """Registro normalizzato per-tappa, lowpass a `tau` lento.

        Min/max della tappa: cosi' il canale usa tutto il range 0..1
        anche su tappe pianeggianti (e' un parametro *musicale*, non
        un'altitudine assoluta). Se il client vuole l'altitudine
        cruda, va aggiunto un canale separato in futuro.
        """
        emin = float(ele.min())
        emax = float(ele.max())
        if emax > emin:
            raw = (ele - emin) / (emax - emin)
        else:
            raw = np.full_like(ele, 0.5)
        return np.clip(_lowpass(raw, dt, self.policy.register_smoothing_tau_s), 0.0, 1.0)

    def _brightness(self, palette: np.ndarray, register: np.ndarray) -> np.ndarray:
        """Combina la `brightness_of(palette, register)` campione per campione."""
        return np.array(
            [self.policy.brightness_of(int(p), float(r))
             for p, r in zip(palette, register)],
            dtype=float,
        )


__all__ = ["MacroModulator"]

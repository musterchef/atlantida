"""Policy del MacroModulator: tabelle decisionali dichiarative.

Una `MacroPolicy` raccoglie i parametri musicali che traducono input
geografici (quota, varianza locale, openness) in canali del contratto
``/mod/macro/*``. La logica del modulator NON sta qui: qui ci sono
solo dati. Aggiungere una policy = aggiungere una funzione factory che
ritorna una `MacroPolicy`.

Convenzioni numeriche (vedi `CONTRATTO-MODULAZIONI.md` §2.1):

- `scale`: 0 pentatonica, 1 dorian, 2 phrygian, 3 mixolydian, 4 lydian,
  5 whole-tone.
- `palette`: 0 pad, 1 strings, 2 bells, 3 granular, 4 brass.

Bucket di quota: ``0`` = bassa, ``1`` = media, ``2`` = alta.
Bucket di varianza locale: ``0`` = piatto, ``1`` = mosso.
Bucket di openness corrente: ``0..3`` (chiuso, dorian, lydian, sospeso).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

# Tipi alias per chiarezza.
ElevBucket = int
VarBucket = int
PaletteId = int
ScaleId = int


# ──────────────────── Dataclass ────────────────────────────────────


@dataclass(frozen=True)
class MacroPolicy:
    """Tabelle decisionali e parametri musicali. Tutto dati, niente logica.

    Attributes:
        name: nome identificativo (per debug/log).
        palette_table: mappa ``(elev_bucket, var_bucket) -> palette``.
            Deve coprire tutti i 6 quadranti possibili (elev 0..2 ×
            var 0..1). Manca = fallback a `default_palette`.
        scale_table: mappa ``openness_bucket -> scale``. Bucket 0..3.
            Le soglie di binning sono in `openness_thresholds`.
        openness_thresholds: 3 cut-points crescenti in 0..1 che
            dividono `openness` corrente in 4 bucket.
        default_palette: usata se il lookup nella tabella manca.
        default_scale: usata in fallback.
        poi_palette_override: se non None e c'e' un POI attivo,
            forza ``macro_palette`` a questo valore (es. 2=bells).
            None disattiva l'override.
        palette_brightness: mappa ``palette -> brightness_intrinseca``
            in 0..1. Usata per calcolare ``macro_brightness``.
        brightness_register_weight: peso del registro nel calcolo
            finale di `macro_brightness` (resto: palette).
        register_smoothing_tau_s: smoothing del canale `register` (s).
        scale_dwell_s: tempo minimo di stabilita' prima di cambiare
            `macro_scale` (anti-flicker).
        palette_dwell_s: idem per `macro_palette`.
        section_window_s: finestra mobile per calcolare quota mediana
            e varianza locale (s). Determina la grana delle sezioni.
    """

    name: str = "default"

    palette_table: Mapping[tuple[ElevBucket, VarBucket], PaletteId] = field(
        default_factory=lambda: MappingProxyType({
            (0, 0): 0,  # basso + piatto   -> pad
            (0, 1): 1,  # basso + mosso    -> strings
            (1, 0): 1,  # medio + piatto   -> strings
            (1, 1): 3,  # medio + mosso    -> granular
            (2, 0): 4,  # alto + piatto    -> brass
            (2, 1): 4,  # alto + mosso     -> brass
        }),
    )

    scale_table: Mapping[int, ScaleId] = field(
        default_factory=lambda: MappingProxyType({
            0: 2,  # openness bassa     -> phrygian (chiuso, minore)
            1: 1,  # openness media     -> dorian
            2: 4,  # openness alta      -> lydian (aperto, brillante)
            3: 5,  # openness molto alta-> whole-tone (sospeso)
        }),
    )

    openness_thresholds: tuple[float, float, float] = (0.30, 0.60, 0.85)

    default_palette: PaletteId = 0
    default_scale: ScaleId = 1

    poi_palette_override: PaletteId | None = 2  # bells

    palette_brightness: Mapping[PaletteId, float] = field(
        default_factory=lambda: MappingProxyType({
            0: 0.25,  # pad: scuro
            1: 0.50,  # strings: medio
            2: 0.80,  # bells: brillante
            3: 0.60,  # granular: medio-brillante
            4: 0.75,  # brass: brillante
        }),
    )

    brightness_register_weight: float = 0.4
    register_smoothing_tau_s: float = 30.0

    scale_dwell_s: float = 20.0
    palette_dwell_s: float = 30.0
    section_window_s: float = 60.0

    def lookup_palette(
        self, elev_bucket: ElevBucket, var_bucket: VarBucket,
    ) -> PaletteId:
        return self.palette_table.get(
            (elev_bucket, var_bucket), self.default_palette,
        )

    def lookup_scale(self, openness_bucket: int) -> ScaleId:
        return self.scale_table.get(openness_bucket, self.default_scale)

    def brightness_of(self, palette: PaletteId, register: float) -> float:
        pal_b = self.palette_brightness.get(palette, 0.5)
        w = self.brightness_register_weight
        return float(w * register + (1.0 - w) * pal_b)


# ──────────────────── Policy registry ──────────────────────────────


def _default_policy() -> MacroPolicy:
    """Policy bilanciata per il corpus italiano (le tue tappe).

    Tabella discussa in `doc/DESIGN-MACRO.md` §4.
    """
    return MacroPolicy(name="default")


def _minimal_policy() -> MacroPolicy:
    """Policy ridotta: solo pad / strings / brass. Utile per A/B test
    sound design quando non si vuole troppo turn-over timbrico."""
    return MacroPolicy(
        name="minimal",
        palette_table=MappingProxyType({
            (0, 0): 0, (0, 1): 0,
            (1, 0): 1, (1, 1): 1,
            (2, 0): 4, (2, 1): 4,
        }),
        poi_palette_override=None,  # niente bells qui
    )


def _dark_policy() -> MacroPolicy:
    """Policy "scura": scala minore quasi ovunque, palette grevi.
    Esperimento per tappe drammatiche / serali."""
    return MacroPolicy(
        name="dark",
        scale_table=MappingProxyType({
            0: 2,  # phrygian
            1: 2,  # phrygian
            2: 1,  # dorian
            3: 1,  # dorian
        }),
        palette_table=MappingProxyType({
            (0, 0): 0, (0, 1): 0,
            (1, 0): 3, (1, 1): 3,
            (2, 0): 0, (2, 1): 4,
        }),
    )


#: Registry pubblico. Estendere aggiungendo una funzione factory.
POLICIES: Mapping[str, "MacroPolicy"] = MappingProxyType({
    "default": _default_policy(),
    "minimal": _minimal_policy(),
    "dark":    _dark_policy(),
})


def get_policy(name: str) -> MacroPolicy:
    """Ritorna la policy nominata. Errore esplicito se manca."""
    if name not in POLICIES:
        raise KeyError(
            f"Policy macro '{name}' non trovata. "
            f"Disponibili: {sorted(POLICIES)}",
        )
    return POLICIES[name]


__all__ = ["MacroPolicy", "POLICIES", "get_policy"]

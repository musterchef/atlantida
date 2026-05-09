"""
DESNIVEL — Costanti centralizzate
==================================
Unica fonte di verità per tutti i parametri del sistema audio.

Importare da qui per evitare duplicazione e mantenere coerenza globale.
Cambiamenti qui si propagano automaticamente a tutto il codice.
"""

# ═════════════════════════════════════════════════════════════════════════
#  BPM RANGES
# ═════════════════════════════════════════════════════════════════════════

#: BPM minimo assoluto della composizione
BPM_MIN = 120.0

#: BPM massimo assoluto della composizione
BPM_MAX = 160.0

#: Step di quantizzazione predefinito per griglia musicale (in BPM)
BPM_GRID_STEP_DEFAULT = 4

#: Velocità di riferimento per mappatura speed → BPM (km/h)
#: A questa velocità il BPM raggiunge circa 2/3 del range max
SPEED_REF_KMH = 30.0


# ═════════════════════════════════════════════════════════════════════════
#  BPM GRID GENERATOR
# ═════════════════════════════════════════════════════════════════════════

def get_bpm_grid(step: float = BPM_GRID_STEP_DEFAULT) -> tuple[float, ...]:
    """Genera griglia BPM dal range definito sopra.
    
    Parametri
    ---------
    step : float
        Intervallo tra punti griglia (default 10 BPM).
    
    Restituisce
    -----------
    tuple[float, ...]
        Griglia BPM da BPM_MIN a BPM_MAX con intervallo step.
    
    Esempi
    ------
    >>> get_bpm_grid(10)
    (90.0, 100.0, 110.0, 120.0, 130.0, 140.0)
    >>> get_bpm_grid(2)
    (90.0, 92.0, 94.0, ..., 140.0)
    """
    if step <= 0:
        step = BPM_GRID_STEP_DEFAULT
    return tuple(float(v) for v in [int(x) for x in range(int(BPM_MIN), int(BPM_MAX) + 1, int(step))])


#: Griglia default (step=10 BPM, musicalemente significativo)
BPM_GRID = get_bpm_grid(BPM_GRID_STEP_DEFAULT)


# ═════════════════════════════════════════════════════════════════════════
#  PITCH RANGES
# ═════════════════════════════════════════════════════════════════════════

#: Pitch MIDI minimo: C2 (una ottava sotto il range standard)
PITCH_MIN = 36

#: Pitch MIDI massimo: C6 (4 ottave di escursione altimetrica)
PITCH_MAX = 84

#: Tonica MIDI di base: D4 (Re, centro caldo e suonabile)
DEFAULT_ROOT = 62


# ═════════════════════════════════════════════════════════════════════════
#  AUDIO MAPPATURE — range e scale
# ═════════════════════════════════════════════════════════════════════════

#: Densità ritmica [0, 1]
DENSITY_MIN, DENSITY_MAX = 0.0, 1.0

#: Saturazione/drive [0, 1]
SLOPE_REF = 0.10  # 10% pendenza = già molto duro

#: Filter cutoff normalizzato [0, 1]
CUTOFF_MIN, CUTOFF_MAX = 0.05, 1.0

#: Scale armoniche come intervalli (semitoni) sopra la tonica
SCALES = {
    "major":            (0, 2, 4, 5, 7, 9, 11),
    "minor":            (0, 2, 3, 5, 7, 8, 10),
    "dorian":           (0, 2, 3, 5, 7, 9, 10),
    "lydian":           (0, 2, 4, 6, 7, 9, 11),
    "phrygian":         (0, 1, 3, 5, 7, 8, 10),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
}

#: Mappa terrain [0, 1] → voce timbrica
TERRAIN_VOICES = (
    (0.00, "drone_water"),    # mare/costa
    (0.33, "pad_plain"),      # pianura
    (0.66, "pluck_hill"),     # collina
    (1.00, "brass_mountain"), # montagna
)


# ═════════════════════════════════════════════════════════════════════════
#  MUSICAL SMOOTHING PARAMETERS
# ═════════════════════════════════════════════════════════════════════════

#: Fattore di modulazione minimo dal flow index (bassa continuità)
MUSICAL_FLOW_BLEND_MIN = 0.85

#: Fattore di modulazione massimo dal flow index (alta continuità)
MUSICAL_FLOW_BLEND_MAX = 1.0

#: Inerzia temporale del BPM in secondi (quanto morbidezza post-mapping)
MUSICAL_TAU_SECONDS = 8.0

#: Durata dei blocchi-frase per ridurre micro-variazioni (secondi)
MUSICAL_BLOCK_SECONDS = 4.0

#: Soglia minima di variazione per aggiornare il BPM (BPM assoluti)
MUSICAL_DEADBAND_BPM = 2.0

#: Variazione massima consentita del BPM al secondo (slew-rate limit)
MUSICAL_MAX_CHANGE_BPM_PER_S = 1.5

#: Step finale di quantizzazione continua nel mapping BPM (0.5 = mezzo BPM)
MUSICAL_OUTPUT_STEP_BPM = 1.0

#: Finestra Savitzky-Golay per smoothing velocità (numero di punti, deve essere dispari)
SAVGOL_WINDOW_DEFAULT = 15

#: Ordine polinomio per Savitzky-Goyal (2 = parabola, la norma)
SAVGOL_POLYORDER = 2


__all__ = [
    # BPM
    "BPM_MIN", "BPM_MAX", "BPM_GRID", "BPM_GRID_STEP_DEFAULT",
    "SPEED_REF_KMH", "get_bpm_grid",
    # Pitch
    "PITCH_MIN", "PITCH_MAX", "DEFAULT_ROOT",
    # Audio
    "DENSITY_MIN", "DENSITY_MAX", "SLOPE_REF", "CUTOFF_MIN", "CUTOFF_MAX",
    "SCALES", "TERRAIN_VOICES",
    # Musical shaping
    "MUSICAL_FLOW_BLEND_MIN", "MUSICAL_FLOW_BLEND_MAX",
    "MUSICAL_TAU_SECONDS", "MUSICAL_BLOCK_SECONDS",
    "MUSICAL_DEADBAND_BPM", "MUSICAL_MAX_CHANGE_BPM_PER_S",
    "MUSICAL_OUTPUT_STEP_BPM",
    "SAVGOL_WINDOW_DEFAULT", "SAVGOL_POLYORDER",
]

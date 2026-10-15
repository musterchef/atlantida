"""
DESNIVEL — TouchDesigner Data Loader
=====================================
Questo script va incollato in un **Text DAT** chiamato `desnivel_loader`.
Poi un **CHOP Execute** o **Timer CHOP callback** lo chiama ogni frame.

SETUP in TouchDesigner:
1. File In DAT  → "file_csv"   → punta a output/tappa_01.csv
2. Table DAT    → "data_table" → collega dal File In DAT
3. Text DAT     → "desnivel_loader" → incolla questo script
4. CHOP Execute → richiama onValueChange o un Timer callback

Oppure: usa il metodo semplice (DAT to CHOP) descritto in fondo.
"""

import math

# ──────────────────────────────────────────────
# CONFIGURAZIONE
# ──────────────────────────────────────────────
CSV_PATH = "C:/Users/marco/Documents/Desnivel/output/tappa_01.csv"
TOTAL_STAGES = 12


def get_current_frame():
    """
    Ritorna il frame corrente dell'animazione TD, 
    wrappato al numero di righe del CSV.
    """
    table = op('data_table')
    if table is None or table.numRows <= 1:
        return 0
    max_frames = table.numRows - 1  # prima riga = header
    # absTime.frame parte da 0 in TD
    return int(absTime.frame) % max_frames


def get_row(frame_idx):
    """
    Legge una riga dal Table DAT e restituisce un dizionario.
    frame_idx è 0-based (riga 0 = primo dato, non header).
    """
    table = op('data_table')
    if table is None or table.numRows <= 1:
        return {}
    
    row = frame_idx + 1  # +1 per saltare header
    if row >= table.numRows:
        row = table.numRows - 1
    
    headers = [table[0, col].val for col in range(table.numCols)]
    values = {}
    for col_idx, h in enumerate(headers):
        raw = table[row, col_idx].val
        try:
            values[h] = float(raw)
        except (ValueError, TypeError):
            values[h] = 0.0
    return values


def push_to_chop(values, target_name='constant_data'):
    """
    Scrive i valori in un Constant CHOP per usarli ovunque nel network.
    Il Constant CHOP deve avere i canali già nominati.
    """
    target = op(target_name)
    if target is None:
        return
    
    channel_map = {
        'lat_norm':    'tx',   # posizione X nella scena
        'lon_norm':    'tz',   # posizione Z nella scena  
        'ele_norm':    'ty',   # altezza Y
        'speed_kmh':   'speed',
        'slope':       'slope',
        'curvature':   'curve',
        'bearing_deg': 'bearing',
        'difficulty':  'diff',
        'flow_index':  'flow',
        'effort':      'effort',
    }
    
    for csv_col, chop_chan in channel_map.items():
        if csv_col in values:
            try:
                target.par[chop_chan + '0'] = values[csv_col]  # costant CHOP syntax
            except:
                pass


def push_to_custom_pars(values, target_name='geo_viaggio'):
    """
    Scrive i valori nei Custom Parameters di un COMP.
    Utile per pilotare shader / materiali.
    """
    target = op(target_name)
    if target is None:
        return
    
    par_map = {
        'lat_norm':   'Latnorm',
        'lon_norm':   'Lonnorm',
        'ele_norm':   'Elenorm',
        'speed_kmh':  'Speed',
        'slope':      'Slope',
        'curvature':  'Curvature',
        'difficulty': 'Difficulty',
        'flow_index': 'Flow',
        'effort':     'Effort',
    }
    
    for csv_col, par_name in par_map.items():
        if csv_col in values:
            try:
                setattr(target.par, par_name, values[csv_col])
            except:
                pass


# ──────────────────────────────────────────────
# METODO 1: Frame Execute DAT callback
# ──────────────────────────────────────────────
# Crea un "Frame Execute DAT", punta a questo Text DAT,
# e attiva "Execute on Frame" con questo codice:

def onFrameStart(frame):
    """Chiamato ogni frame da TouchDesigner."""
    f = get_current_frame()
    row = get_row(f)
    if row:
        push_to_chop(row, 'constant_data')
        # push_to_custom_pars(row, 'geo_viaggio')  # se usi custom pars


# ──────────────────────────────────────────────
# METODO 2 (PIÙ SEMPLICE): DAT to CHOP diretto
# ──────────────────────────────────────────────
"""
Non serve nessuno script! Basta collegare operatori.

IMPORTANTE: prima Select, poi Speed+Lookup.
Alcuni canali sono istantanei (per-frame), altri cumulativi.
Raggruppali con Select CHOP prima di scorrere.

NETWORK:

  File In DAT (tappa_01.csv)
      ↓
  DAT to CHOP
    · First Row is: Names
    · First Column is: Values
    · Output: Channel per Column
      ↓
      ├─ Select CHOP "sel_position"
      │    Channels: lat_norm lon_norm ele_norm
      │      ↓
      │    Speed CHOP (rate=1, min=0, max=1) → Lookup CHOP
      │      ↓
      │    → Transform COMP (tx ty tz)
      │
      ├─ Select CHOP "sel_instant"
      │    Channels: speed_kmh slope curvature bearing_deg difficulty flow_index
      │      ↓
      │    Speed CHOP → Lookup CHOP
      │      ↓
      │    → Visuals diretti (colore, particelle, rotazione, shader)
      │
      ├─ Select CHOP "sel_progress"
      │    Channels: td_time_norm
      │      ↓
      │    Speed CHOP → Lookup CHOP
      │      ↓
      │    → Barra progresso, timeline UI
      │
      └─ Select CHOP "sel_cumulative"
           Channels: cum_dist_m effort td_time
             ↓
           Speed CHOP → Lookup CHOP
             ↓
           (opzionale) Math CHOP con Derivative = ON
             → ottieni il delta per-frame (variazione istantanea)
             → utile per "accelerazione", "sforzo improvviso", ecc.

PERCHÉ Select PRIMA di Speed+Lookup:
  - Puoi applicare Math/Filter/Lag diversi per gruppo
  - I cumulativi (cum_dist_m, effort) servono sia come valore
    assoluto (per barra progresso) sia come derivata (per intensità)
  - I per-frame (speed, slope) vanno bene così come sono
  - La posizione (lat/lon/ele) va direttamente a geometria

TIPI DI CANALE:
  PER-FRAME (istantanei):
    speed_kmh    → velocità in quel momento
    slope        → pendenza (-1 discesa, +1 salita)
    curvature    → curva (-1 sinistra, +1 destra)
    bearing_deg  → direzione (0-360°)
    difficulty   → difficoltà calcolata (0→1)
    flow_index   → ritmicità del movimento (0→1)

  CUMULATIVI (crescenti nel tempo):
    cum_dist_m   → distanza totale percorsa (cresce sempre)
    effort       → fatica accumulata (cresce)
    td_time      → tempo mappato (cresce)

  POSIZIONE (normalizzati 0→1):
    lat_norm     → latitudine normalizzata
    lon_norm     → longitudine normalizzata
    ele_norm     → altitudine normalizzata

  PROGRESSO:
    td_time_norm → 0 a 1, progresso globale della tappa
"""


# ──────────────────────────────────────────────
# HELPER: Cambia tappa
# ──────────────────────────────────────────────
def load_stage(stage_num):
    """
    Carica una tappa diversa (1-12).
    Chiama: run("desnivel_loader").load_stage(5)
    """
    file_dat = op('file_csv')
    if file_dat is None:
        return
    path = f"C:/Users/marco/Documents/Desnivel/output/tappa_{stage_num:02d}.csv"
    file_dat.par.file = path
    print(f"[DESNIVEL] Caricata tappa {stage_num}: {path}")


def get_all_stage_info():
    """Carica il summary JSON per avere metadati di tutte le tappe."""
    import json
    json_path = "C:/Users/marco/Documents/Desnivel/output/desnivel_summary.json"
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except:
        return {}

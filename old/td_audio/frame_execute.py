"""
DESNIVEL — Frame Execute DAT
=============================
Ogni frame legge il CSV, aggiorna i GLSL TOP e manda OSC ad Ableton.

SETUP (tutti nello stesso livello di /project1/):
  file_csv      — Table DAT      → output/tappa_01.csv
  osc_control   — OSC Out DAT   → 127.0.0.1:11000  (AbletonOSC: BPM, transport)
  osc_music     — OSC Out DAT   → 127.0.0.1:9001   (Max4Live: note, scale, density)
  glsl_trail    — GLSL TOP      → trail_pixel.glsl
  glsl_terrain  — GLSL TOP      → terrain_pixel.glsl (opzionale)

OSC routing:
  osc_control → AbletonOSC Remote Script → /live/song/set/tempo, mixer
  osc_music   → Max4Live device (udpreceive 9001) → genera note da scale+pitch

Parametri Execute DAT da abilitare:
  onStart, onFrameStart — ON
  tutto il resto        — OFF
"""

import json
import os

# ── Stato globale (TD persiste variabili di modulo tra frame) ──
_sonic_data = None   # list[dict] caricato da JSON
_csv_path   = None   # path CSV corrente (per reload)


def _load_sonic(csv_path: str) -> list:
    """Carica il JSON sonic corrispondente al CSV. Una volta sola."""
    sonic_path = csv_path.replace('.csv', '_sonic.json')
    if not os.path.exists(sonic_path):
        print(f'[DESNIVEL] sonic JSON non trovato: {sonic_path}')
        return []
    with open(sonic_path, encoding='utf-8') as f:
        data = json.load(f)
    print(f'[DESNIVEL] Caricato {len(data)} frame sonic da: {sonic_path}')
    return data


def _col(table, row, name: str) -> float:
    """Legge il valore di una colonna dal Table DAT per nome."""
    for c in range(table.numCols):
        if table[0, c].val == name:
            try:
                return float(table[row, c].val)
            except (ValueError, TypeError):
                return 0.0
    return 0.0


def _send_osc_control(osc, params: dict):
    """AbletonOSC (porta 11000): BPM, transport, mixer."""
    osc.sendOSC('/live/song/set/tempo', [float(params['bpm'])])
    osc.sendOSC('/desnivel/volume',     [params['volume']])
    osc.sendOSC('/desnivel/drive',      [params['drive']])
    osc.sendOSC('/desnivel/reverb',     [params['reverb']])
    osc.sendOSC('/desnivel/cutoff',     [params['cutoff']])
    osc.sendOSC('/desnivel/color_temp', [params['color_temp']])
    osc.sendOSC('/desnivel/progress',   [params['t_norm']])


def _send_osc_music(osc, params: dict):
    """Max4Live device (porta 9001): pitch, scale, density → genera note."""
    osc.sendOSC('/desnivel/pitch',   [params['pitch']])
    osc.sendOSC('/desnivel/scale',   [params['scale']])
    osc.sendOSC('/desnivel/voice',   [params['voice']])
    osc.sendOSC('/desnivel/density', [params['density']])
    osc.sendOSC('/desnivel/bpm',     [float(params['bpm'])])


def _send_osc(params: dict):
    """Entry point: invia ai due OSC Out DAT. Tollerante se uno manca."""
    ctrl = op('osc_control')
    mus  = op('osc_music')
    if ctrl is not None:
        _send_osc_control(ctrl, params)
    if mus is not None:
        _send_osc_music(mus, params)


def onStart():
    """Chiamata all'avvio di TD. Resetta lo stato per forzare il reload del JSON."""
    global _sonic_data, _csv_path
    _sonic_data = None
    _csv_path   = None
    print('[DESNIVEL] onStart — stato resettato')


def onFrameStart(frame):
    global _sonic_data, _csv_path

    table = op('file_csv')
    if table is None or table.numRows <= 1:
        return

    # ── Carica sonic JSON al primo frame (o se il CSV cambia) ──
    try:
        current_path = table.par.file.val
    except AttributeError:
        current_path = ''

    if _sonic_data is None or current_path != _csv_path:
        _csv_path   = current_path
        _sonic_data = _load_sonic(current_path)

    max_frames = table.numRows - 1
    f   = int(absTime.frame) % max_frames
    row = f + 1  # +1 per saltare header

    # ── Leggi valori geografici dal CSV ──
    lat_n   = _col(table, row, 'lat_norm')
    lon_n   = _col(table, row, 'lon_norm')
    ele_n   = _col(table, row, 'ele_norm')
    speed   = _col(table, row, 'speed_kmh')
    slope   = _col(table, row, 'slope')
    curv    = _col(table, row, 'curvature')
    diff    = _col(table, row, 'difficulty')
    flow    = _col(table, row, 'flow_index')
    effort  = _col(table, row, 'effort')
    prog    = _col(table, row, 'td_time_norm')
    speed_n = min(speed / 120.0, 1.0)

    # ── Aggiorna GLSL TOP: Trail ──
    glsl = op('glsl_trail')
    if glsl is not None:
        glsl.par.value1 = lat_n
        glsl.par.value2 = lon_n
        glsl.par.value3 = ele_n
        glsl.par.value4 = speed_n
        glsl.par.value5 = slope
        glsl.par.value6 = curv
        glsl.par.value7 = diff
        glsl.par.value8 = prog

    # ── Aggiorna GLSL TOP: Terrain ──
    glsl2 = op('glsl_terrain')
    if glsl2 is not None:
        glsl2.par.value1 = lat_n
        glsl2.par.value2 = lon_n
        glsl2.par.value3 = ele_n
        glsl2.par.value4 = speed_n
        glsl2.par.value5 = slope
        glsl2.par.value6 = curv
        glsl2.par.value7 = effort
        glsl2.par.value8 = prog

    # ── Leggi parametri audio dal sonic JSON ──
    if _sonic_data and f < len(_sonic_data):
        sonic = _sonic_data[f]
        _send_osc(sonic)

    # ── Debug ogni 300 frame (~10 sec a 30fps) ──
    if f % 300 == 0:
        print(f'[DESNIVEL] frame={f}/{max_frames} prog={prog:.3f} '
              f'lat={lat_n:.4f} lon={lon_n:.4f} ele={ele_n:.3f} '
              f'speed={speed:.1f}km/h slope={slope:.3f}')
        if _sonic_data and f < len(_sonic_data):
            s = _sonic_data[f]
            print(f'[DESNIVEL] bpm={s["bpm"]} pitch={s["pitch"]} '
                  f'scale={s["scale"]} voice={s["voice"]} drive={s["drive"]:.3f}')


def onFrameEnd(frame):
    pass

def onPlayStateChange(state):
    pass

def onDeviceChange():
    pass

def onProjectPreSave():
    pass

def onProjectPostSave():
    pass

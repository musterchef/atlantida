"""
DESNIVEL — Frame Execute DAT
=============================
Incolla questo codice in un Execute DAT (tipo "Execute" o "Frame Execute").
Ogni frame legge la riga corrispondente dal CSV e aggiorna
i parametri di un GLSL TOP.

SETUP NECESSARIO:
1. "file_csv"     — File In DAT → punta a tappa_01.csv
2. "glsl_trail"   — GLSL TOP con trail_pixel.glsl caricato
3. "glsl_terrain" — GLSL TOP con terrain_pixel.glsl caricato (opzionale)
4. "feedback1"    — Feedback TOP collegato a glsl_trail (per la scia)

Il Frame Execute DAT deve avere:
  - "Execute on Frame Start" = ON
  - "Execute on Frame End"   = OFF
"""

def onFrameStart(frame):
    table = op('file_csv')
    if table is None or table.numRows <= 1:
        return
    
    max_frames = table.numRows - 1
    # Frame corrente, ciclico
    f = int(absTime.frame) % max_frames
    row = f + 1  # +1 per saltare header
    
    # ── Leggi valori dal CSV ──
    def col(name):
        """Legge il valore di una colonna per nome."""
        try:
            col_idx = table.row(0).index(name) if hasattr(table.row(0), 'index') else None
            # Metodo alternativo: cerca nella prima riga
            for c in range(table.numCols):
                if table[0, c].val == name:
                    return float(table[row, c].val)
            return 0.0
        except:
            return 0.0
    
    lat_n   = col('lat_norm')
    lon_n   = col('lon_norm')
    ele_n   = col('ele_norm')
    speed   = col('speed_kmh')
    slope   = col('slope')
    curv    = col('curvature')
    diff    = col('difficulty')
    flow    = col('flow_index')
    effort  = col('effort')
    prog    = col('td_time_norm')
    bearing = col('bearing_deg')
    
    # Normalizza speed (assume max ~120 km/h)
    speed_n = min(speed / 120.0, 1.0)
    
    # ── Aggiorna GLSL TOP: Trail ──
    glsl = op('glsl_trail')
    if glsl is not None:
        glsl.par.value1 = lat_n      # uLat       (uniform float)
        glsl.par.value2 = lon_n      # uLon
        glsl.par.value3 = ele_n      # uEle
        glsl.par.value4 = speed_n    # uSpeed
        glsl.par.value5 = slope      # uSlope
        glsl.par.value6 = curv       # uCurvature
        glsl.par.value7 = diff       # uDifficulty
        glsl.par.value8 = prog       # uProgress
    
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
    
    # ── Debug (opzionale): stampa ogni 300 frame (~10 sec) ──
    if f % 300 == 0:
        print(f"[DESNIVEL] frame={f}/{max_frames} prog={prog:.3f} "
              f"lat={lat_n:.4f} lon={lon_n:.4f} ele={ele_n:.3f} "
              f"speed={speed:.1f}km/h slope={slope:.3f}")


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

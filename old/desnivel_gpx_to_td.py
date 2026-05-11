"""
DESNIVEL — GPX → TouchDesigner data pipeline
=============================================
Parsa tutti i 12 GPX delle tappe Torino → Castel del Monte.
Estrae parametri utili per TouchDesigner e Ableton.
Riscala il tempo di ogni tappa: la piu lunga = 10 min (600 s),
le altre in proporzione.

Output per ogni tappa:
  - CSV  (tappa_XX.csv)       → pronto per Table DAT
  - JSON (desnivel_summary.json) → sommario globale

Dipendenze: solo stdlib (xml.etree, math, json, csv, os, glob).
Nessun pip install necessario.
"""

import xml.etree.ElementTree as ET
import math, json, csv, os, glob, sys
from datetime import datetime
from pathlib import Path
from terrain_classify import classify_terrain
from audio_mapper import map_rows as map_sonic_rows
from audio_mapper import map_rows_with_bpm_smoothing
from constants import (
    SAVGOL_WINDOW_DEFAULT,
    MUSICAL_TAU_SECONDS, MUSICAL_BLOCK_SECONDS,
    MUSICAL_DEADBAND_BPM, MUSICAL_MAX_CHANGE_BPM_PER_S,
    MUSICAL_OUTPUT_STEP_BPM, get_bpm_grid, BPM_GRID_STEP_DEFAULT,
)

# ─────────────────── CONFIG ────────────────
PROJECT_DIR    = Path(__file__).resolve().parent.parent  # C:\Users\marco\Documents\Desnivel
GPX_DIR        = str(PROJECT_DIR / "gpx")               # dove stanno i GPX
OUT_DIR        = str(PROJECT_DIR / "output")             # cartella output
MAX_DURATION_S = 600.0    # 10 min in secondi
RESAMPLE_FPS   = 30       # frequenza di campionamento per TD (0 = no resample, raw)
TERRAIN_METHOD = "coastline"  # "elevation" | "coastline" | "srtm"
# ─ Sonic output ─
EXPORT_SONIC            = True       # genera tappa_XX_sonic.json
SONIC_INCLUDE_SOURCE    = False      # include valori origine per debug
SONIC_SMOOTH_BPM        = True       # Savitzky-Goyal smoothing su velocità
SONIC_QUANTIZE_BPM      = True       # Quantizza BPM a griglia musicale
SONIC_BLEND_BPM_FLOW    = True       # Modula BPM con flow_index
SONIC_BPM_SMOOTH_WINDOW = SAVGOL_WINDOW_DEFAULT  # Finestra Savitzky-Goyal
SONIC_BPM_GRID_STEP     = 2          # Step di quantizzazione BPM (per griglia densa)
# ─ Musical shaping (importati da constants.py) ─
SONIC_MUSICAL_POST      = True       # Shaping musicale finale (anti-nervosismo)
SONIC_MUSICAL_TAU_S     = MUSICAL_TAU_SECONDS
SONIC_MUSICAL_BLOCK_S   = MUSICAL_BLOCK_SECONDS
SONIC_MUSICAL_DEADBAND  = MUSICAL_DEADBAND_BPM
SONIC_MUSICAL_MAX_DPS   = MUSICAL_MAX_CHANGE_BPM_PER_S
SONIC_MUSICAL_STEP_BPM  = MUSICAL_OUTPUT_STEP_BPM
# ────────────────────────────────────────────────

NS = {"gpx": "http://www.topografix.com/GPX/1/1"}

def parse_time(s: str) -> datetime:
    """Parsa ISO 8601 come da GPX Strava."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

def haversine(lat1, lon1, lat2, lon2):
    """Distanza in metri tra due coordinate."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing(lat1, lon1, lat2, lon2):
    """Angolo di direzione in gradi (0-360)."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def curvature_from_bearings(b_prev, b_cur):
    """Variazione angolare normalizzata [-1, 1]. 0 = dritto."""
    diff = b_cur - b_prev
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return diff / 180.0  # normalizzato

# ─────────────── PARSING ───────────────
def parse_gpx(filepath):
    """Ritorna lista di dict con campi raw per ogni trackpoint."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    points = []
    for trkpt in root.findall(".//gpx:trkpt", NS):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_el = trkpt.find("gpx:ele", NS)
        time_el = trkpt.find("gpx:time", NS)
        ele = float(ele_el.text) if ele_el is not None else 0.0
        t = parse_time(time_el.text) if time_el is not None else None
        points.append({"lat": lat, "lon": lon, "ele": ele, "time": t})
    return points

def get_stage_name(filepath):
    """Estrae il nome della tappa dal filename (es. tappa01_Torino_Genova)."""
    return Path(filepath).stem

def get_stage_number(filepath):
    """Estrae il numero della tappa dal filename (es. tappa01_... → 1)."""
    stem = Path(filepath).stem
    import re
    m = re.match(r'tappa(\d+)', stem)
    return int(m.group(1)) if m else 0

# ─────────────── DERIVED DATA ───────────────
def compute_derived(points):
    """
    Calcola per ogni punto:
      - dist_m        distanza dal punto precedente (m)
      - cum_dist_m    distanza cumulativa (m)
      - dt_s          delta tempo (s)
      - elapsed_s     tempo trascorso dall'inizio (s)
      - speed_ms      velocita' (m/s)
      - speed_kmh     velocita' (km/h)
      - slope         pendenza (rise/run), 0 se run==0
      - slope_pct     pendenza in %
      - bearing_deg   direzione (gradi)
      - curvature     variazione angolare normalizzata [-1, 1]
      - ele_delta     variazione altimetrica dal punto precedente
      - ele_norm      elevazione normalizzata [0, 1] nella tappa
      - lat_norm      latitudine normalizzata [0, 1] nella tappa
      - lon_norm      longitudine normalizzata [0, 1] nella tappa
    """
    if not points:
        return []

    # range per normalizzazione
    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    eles = [p["ele"] for p in points]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    ele_min, ele_max = min(eles), max(eles)
    lat_range = lat_max - lat_min if lat_max != lat_min else 1e-9
    lon_range = lon_max - lon_min if lon_max != lon_min else 1e-9
    ele_range = ele_max - ele_min if ele_max != ele_min else 1e-9

    results = []
    cum_dist = 0.0
    cum_ele_gain = 0.0
    cum_ele_loss = 0.0
    prev_bearing = None
    t0 = points[0]["time"]

    for i, p in enumerate(points):
        row = {
            "lat":      p["lat"],
            "lon":      p["lon"],
            "ele":      p["ele"],
            "lat_norm": (p["lat"] - lat_min) / lat_range,
            "lon_norm": (p["lon"] - lon_min) / lon_range,
            "ele_norm": (p["ele"] - ele_min) / ele_range,
        }

        if i == 0:
            row["dist_m"]       = 0.0
            row["cum_dist_m"]   = 0.0
            row["dt_s"]         = 0.0
            row["elapsed_s"]    = 0.0
            row["speed_ms"]     = 0.0
            row["speed_kmh"]    = 0.0
            row["slope"]        = 0.0
            row["slope_pct"]    = 0.0
            row["bearing_deg"]  = 0.0
            row["curvature"]    = 0.0
            row["ele_delta"]    = 0.0
            row["cum_ele_gain"] = 0.0
            row["cum_ele_loss"] = 0.0
        else:
            prev = points[i - 1]
            d = haversine(prev["lat"], prev["lon"], p["lat"], p["lon"])
            dt = (p["time"] - prev["time"]).total_seconds() if (p["time"] and prev["time"]) else 0.0
            elapsed = (p["time"] - t0).total_seconds() if (p["time"] and t0) else 0.0
            cum_dist += d
            speed = d / dt if dt > 0 else 0.0
            ele_d = p["ele"] - prev["ele"]
            sl = ele_d / d if d > 0 else 0.0
            b = bearing(prev["lat"], prev["lon"], p["lat"], p["lon"])
            curv = curvature_from_bearings(prev_bearing, b) if prev_bearing is not None else 0.0
            prev_bearing = b

            row["dist_m"]       = d
            row["cum_dist_m"]   = cum_dist
            row["dt_s"]         = dt
            row["elapsed_s"]    = elapsed
            row["speed_ms"]     = speed
            row["speed_kmh"]    = speed * 3.6
            row["slope"]        = sl
            row["slope_pct"]    = sl * 100.0
            row["bearing_deg"]  = b
            row["curvature"]    = curv
            row["ele_delta"]    = ele_d

            # accumula dislivello positivo e negativo separatamente
            if ele_d > 0:
                cum_ele_gain += ele_d
            else:
                cum_ele_loss += abs(ele_d)
            row["cum_ele_gain"] = cum_ele_gain
            row["cum_ele_loss"] = cum_ele_loss

        results.append(row)

    # normalizza cum_ele_gain e cum_ele_loss (0→1)
    if results:
        max_gain = results[-1].get("cum_ele_gain", 0)
        max_loss = results[-1].get("cum_ele_loss", 0)
        for r in results:
            r["cum_ele_gain_norm"] = r["cum_ele_gain"] / max_gain if max_gain > 0 else 0.0
            r["cum_ele_loss_norm"] = r["cum_ele_loss"] / max_loss if max_loss > 0 else 0.0

    return results

# ─────────────── DIFFICULTY / FLOW INDICES ───────────────
def compute_indices(rows, window=30):
    """
    Aggiunge indici derivati:
      - difficulty   media mobile pendenza assoluta (rolling)
      - flow_index   1 - varianza curvatura (rolling) → continuità
      - effort       speed * abs(slope)
    """
    n = len(rows)
    for i in range(n):
        # rolling window
        start = max(0, i - window // 2)
        end = min(n, i + window // 2 + 1)
        seg = rows[start:end]

        slopes = [abs(r["slope"]) for r in seg]
        curvs  = [abs(r["curvature"]) for r in seg]

        avg_slope = sum(slopes) / len(slopes) if slopes else 0.0
        avg_curv  = sum(curvs)  / len(curvs)  if curvs else 0.0
        var_curv  = sum((c - avg_curv) ** 2 for c in curvs) / len(curvs) if curvs else 0.0

        rows[i]["difficulty"] = min(avg_slope * 10.0, 1.0)  # normalizzato 0-1
        rows[i]["flow_index"] = max(0.0, 1.0 - var_curv * 50.0)  # normalizzato 0-1
        rows[i]["effort"]     = rows[i]["speed_ms"] * abs(rows[i]["slope"])

    # normalizza effort 0-1
    max_effort = max((r["effort"] for r in rows), default=1e-9)
    if max_effort > 0:
        for r in rows:
            r["effort"] = r["effort"] / max_effort

    return rows

# ─────────────── TIME WARP ───────────────
def time_warp(rows, target_duration_s):
    """
    Rimappa elapsed_s → td_time (0 .. target_duration_s).
    Aggiunge td_time e td_time_norm (0..1).
    """
    if not rows:
        return rows
    total = rows[-1]["elapsed_s"]
    if total <= 0:
        total = 1e-9
    scale = target_duration_s / total
    for r in rows:
        r["td_time"]      = r["elapsed_s"] * scale
        r["td_time_norm"] = r["td_time"] / target_duration_s
    return rows

# ─────────────── RESAMPLE ───────────────
def lerp(a, b, t):
    return a + (b - a) * t

def resample_rows(rows, fps, duration_s):
    """
    Ricampiona i dati a frequenza fissa.
    Ritorna nuova lista di dict con frame_index e td_time.
    """
    if fps <= 0 or not rows:
        return rows

    total_frames = int(duration_s * fps)
    if total_frames < 2:
        return rows

    # build lookup by td_time
    resampled = []
    fields_to_lerp = [
        "lat_norm", "lon_norm", "ele_norm",
        "speed_kmh", "slope",
        "bearing_deg", "curvature", "ele_delta",
        "cum_ele_gain_norm", "cum_ele_loss_norm",
        "difficulty", "flow_index", "effort",
        "cum_dist_m", "td_time", "td_time_norm",
        "terrain_type"
    ]

    j = 0  # indice di ricerca nel raw
    for frame in range(total_frames + 1):
        t = (frame / total_frames) * duration_s

        # avanza j finché td_time[j+1] < t
        while j < len(rows) - 2 and rows[j + 1]["td_time"] < t:
            j += 1

        a = rows[j]
        b = rows[min(j + 1, len(rows) - 1)]
        span = b["td_time"] - a["td_time"]
        frac = (t - a["td_time"]) / span if span > 0 else 0.0
        frac = max(0.0, min(1.0, frac))

        new_row = {"frame": frame, "td_time": t}
        for f in fields_to_lerp:
            if f in a and f in b:
                new_row[f] = lerp(a[f], b[f], frac)
        # bearing wrap-around
        if "bearing_deg" in a and "bearing_deg" in b:
            diff = b["bearing_deg"] - a["bearing_deg"]
            if diff > 180: diff -= 360
            elif diff < -180: diff += 360
            new_row["bearing_deg"] = (a["bearing_deg"] + diff * frac) % 360

        resampled.append(new_row)

    return resampled

# ─────────────── CSV EXPORT ───────────────
CSV_FIELDS = [
    "frame", "td_time", "td_time_norm",
    "lat_norm", "lon_norm", "ele_norm",
    "cum_dist_m",
    "speed_kmh",
    "slope",
    "bearing_deg", "curvature",
    "ele_delta",
    "cum_ele_gain_norm", "cum_ele_loss_norm",
    "difficulty", "flow_index", "effort",
    "terrain_type"
]

def export_csv(rows, filepath):
    available = [f for f in CSV_FIELDS if f in rows[0]]
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=available, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            # round floats
            out = {}
            for k in available:
                v = r.get(k, "")
                if isinstance(v, float):
                    out[k] = round(v, 6)
                else:
                    out[k] = v
            writer.writerow(out)

# ─────────────── MAIN ───────────────
def main():
    gpx_pattern = os.path.join(GPX_DIR, "tappa*.gpx")
    gpx_files = sorted(glob.glob(gpx_pattern), key=lambda f: get_stage_number(f))

    if not gpx_files:
        print(f"Nessun file GPX trovato in: {GPX_DIR}")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Trovati {len(gpx_files)} file GPX")
    print(f"Output in: {OUT_DIR}")
    print(f"Max duration: {MAX_DURATION_S}s ({MAX_DURATION_S/60:.0f} min)")
    print(f"Resample FPS: {RESAMPLE_FPS}")
    print()

    # ── PASS 1: parse all, find max duration ──
    stages = []
    for fp in gpx_files:
        num = get_stage_number(fp)
        name = get_stage_name(fp)
        pts = parse_gpx(fp)
        rows = compute_derived(pts)
        rows = compute_indices(rows)

        # Terrain classification
        terrain_values = classify_terrain(rows, method=TERRAIN_METHOD)
        for j, tv in enumerate(terrain_values):
            rows[j]["terrain_type"] = tv

        real_duration = rows[-1]["elapsed_s"] if rows else 0.0
        total_dist = rows[-1]["cum_dist_m"] if rows else 0.0
        eles = [r["ele"] for r in rows]
        ele_gain = sum(max(0, rows[i]["ele_delta"]) for i in range(1, len(rows)))
        ele_loss = sum(min(0, rows[i]["ele_delta"]) for i in range(1, len(rows)))

        # Timestamp di inizio tappa (per mappatura time-of-day in audio_mapper)
        start_dt = pts[0]["time"] if pts and pts[0].get("time") else None

        stages.append({
            "num":           num,
            "name":          name,
            "filepath":      fp,
            "raw_rows":      rows,
            "start_dt":      start_dt,
            "real_duration":  real_duration,
            "total_dist_km": total_dist / 1000.0,
            "n_points":      len(rows),
            "ele_min":       min(eles) if eles else 0,
            "ele_max":       max(eles) if eles else 0,
            "ele_gain":      ele_gain,
            "ele_loss":      abs(ele_loss),
        })
        dur_h = real_duration / 3600
        print(f"  tappa {num:>2d} | {name:<55s} | {len(rows):>6d} pts | "
              f"{dur_h:.1f}h | {total_dist/1000:.1f}km | +{ele_gain:.0f}m -{abs(ele_loss):.0f}m")

    max_real = max(s["real_duration"] for s in stages)
    print(f"\nTappa piu lunga: {max_real:.0f}s ({max_real/3600:.1f}h)")
    print()

    # ── PASS 2: time warp + resample + export ──
    summary = []
    for s in stages:
        # durata proporzionale
        target_dur = (s["real_duration"] / max_real) * MAX_DURATION_S
        rows = time_warp(s["raw_rows"], target_dur)

        if RESAMPLE_FPS > 0:
            rows = resample_rows(rows, RESAMPLE_FPS, target_dur)

        csv_path = os.path.join(OUT_DIR, f"tappa_{s['num']:02d}.csv")
        export_csv(rows, csv_path)

        n_frames = len(rows)
        total_csv_dur = rows[-1].get("td_time", 0)

        # ─── Sonic JSON (audio_mapper) ───
        sonic_file = None
        if EXPORT_SONIC:
            # Usa la versione con BPM smoothing se abilitata
            if SONIC_SMOOTH_BPM or SONIC_QUANTIZE_BPM or SONIC_BLEND_BPM_FLOW:
                # Griglia BPM costruita dinamicamente dal step
                bpm_grid = get_bpm_grid(SONIC_BPM_GRID_STEP) if SONIC_QUANTIZE_BPM else None
                sonic_rows = map_rows_with_bpm_smoothing(
                    rows,
                    start_dt=s.get("start_dt"),
                    include_source=SONIC_INCLUDE_SOURCE,
                    smooth_bpm=SONIC_SMOOTH_BPM,
                    quantize_bpm=SONIC_QUANTIZE_BPM,
                    blend_bpm_flow=SONIC_BLEND_BPM_FLOW,
                    smooth_window=SONIC_BPM_SMOOTH_WINDOW,
                    bpm_grid=bpm_grid,
                    musical_post_smooth=SONIC_MUSICAL_POST,
                    musical_tau_seconds=SONIC_MUSICAL_TAU_S,
                    musical_block_seconds=SONIC_MUSICAL_BLOCK_S,
                    musical_deadband_bpm=SONIC_MUSICAL_DEADBAND,
                    musical_max_change_bpm_per_s=SONIC_MUSICAL_MAX_DPS,
                    musical_output_step_bpm=SONIC_MUSICAL_STEP_BPM,
                )
            else:
                sonic_rows = map_sonic_rows(
                    rows,
                    start_dt=s.get("start_dt"),
                    include_source=SONIC_INCLUDE_SOURCE,
                )
            sonic_path = os.path.join(OUT_DIR, f"tappa_{s['num']:02d}_sonic.json")
            with open(sonic_path, "w", encoding="utf-8") as fh:
                json.dump(sonic_rows, fh, ensure_ascii=False)
            sonic_file = f"tappa_{s['num']:02d}_sonic.json"

        print(f"  tappa {s['num']:>2d} → {target_dur:>6.1f}s ({target_dur/60:.1f}min) | "
              f"{n_frames:>6d} frames | {csv_path}"
              + (f" + {sonic_file}" if sonic_file else ""))

        summary.append({
            "tappa":              s["num"],
            "name":               s["name"],
            "real_duration_s":    round(s["real_duration"], 1),
            "real_duration_h":    round(s["real_duration"] / 3600, 2),
            "mapped_duration_s":  round(target_dur, 2),
            "mapped_duration_min": round(target_dur / 60, 2),
            "total_dist_km":     round(s["total_dist_km"], 2),
            "n_raw_points":      s["n_points"],
            "n_output_frames":   n_frames,
            "ele_min":           round(s["ele_min"], 1),
            "ele_max":           round(s["ele_max"], 1),
            "ele_gain_m":        round(s["ele_gain"], 1),
            "ele_loss_m":        round(s["ele_loss"], 1),
            "csv_file":          f"tappa_{s['num']:02d}.csv",
            "sonic_file":        sonic_file,
            "start_dt":          s["start_dt"].isoformat() if s.get("start_dt") else None,
            "fps":               RESAMPLE_FPS,
        })

    # ── JSON summary ──
    json_path = os.path.join(OUT_DIR, "desnivel_summary.json")
    meta = {
        "project":        "DESNIVEL",
        "description":    "GPX → TouchDesigner data pipeline",
        "max_duration_s": MAX_DURATION_S,
        "resample_fps":   RESAMPLE_FPS,
        "n_stages":       len(stages),
        "longest_stage":  max(stages, key=lambda s: s["real_duration"])["num"],
        "stages":         summary,
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    print(f"\nSommario JSON: {json_path}")
    print("\n─── RIEPILOGO MAPPATURA TEMPORALE ───")
    print(f"{'Tappa':<8} {'Reale':>8} {'Mappata':>10} {'Dist':>8} {'D+':>8}")
    for s in summary:
        print(f"  {s['tappa']:<6d} {s['real_duration_h']:>6.1f}h  {s['mapped_duration_min']:>7.1f}min  "
              f"{s['total_dist_km']:>6.1f}km  +{s['ele_gain_m']:>5.0f}m")

    print(f"\nDone! Tutti i CSV in: {OUT_DIR}")
    print("Importa in TouchDesigner: File In DAT → tappa_XX.csv")
    print("Oppure carica desnivel_summary.json con un Web DAT / Script DAT.")

if __name__ == "__main__":
    main()

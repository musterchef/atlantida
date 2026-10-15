"""
DESNIVEL — GoPro Video → Route Mapper
======================================
Scansiona una cartella di video GoPro Hero 10, estrae:
  - timestamp creazione
  - durata
  - GPS embedded (telemetria GPMF via ffprobe)

Poi associa ogni video alla tappa/km/frame corrispondente
usando i dati GPX già processati.

Output: output/gopro_map.json

Uso:
  python gopro_mapper.py                      # scansiona gopro/
  python gopro_mapper.py --video-dir D:\GoPro # cartella custom
  python gopro_mapper.py --list               # mostra solo info video, no match
"""

import subprocess
import json
import os
import sys
import math
import csv
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from gpmf_extract import extract_gps_summary

# ─────────────────── CONFIG ────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR   = PROJECT_DIR / "gopro"       # default: gopro/ nella root progetto
GPX_DIR     = PROJECT_DIR / "gpx"
OUT_DIR     = PROJECT_DIR / "output"
CSV_DIR     = PROJECT_DIR / "output"

# Tolleranza temporale per matching video → tappa (ore)
TIME_TOLERANCE_H = 24

# Estensioni video accettate
VIDEO_EXTS = {".mp4", ".MP4", ".lrv", ".LRV", ".360"}
# ────────────────────────────────────────────────


def run_ffprobe(video_path: str) -> dict:
    """Esegue ffprobe e ritorna i metadati come dict."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {video_path}: {result.stderr[:200]}")
    return json.loads(result.stdout)


def extract_video_info(video_path: str) -> dict:
    """
    Estrae da un video GoPro:
      - creation_time: datetime UTC
      - duration_s: durata in secondi
      - resolution: "WxH"
      - fps: frame rate
      - has_gps_stream: True se c'è un canale dati GoPro (GPMF)
    """
    meta = run_ffprobe(video_path)
    
    info = {
        "file": os.path.basename(video_path),
        "path": video_path,
        "duration_s": 0.0,
        "creation_time": None,
        "creation_time_str": "",
        "resolution": "",
        "fps": 0.0,
        "has_gps_stream": False,
        "codec": "",
    }

    # --- format level ---
    fmt = meta.get("format", {})
    info["duration_s"] = float(fmt.get("duration", 0))
    
    # creation_time può essere in format.tags o streams[0].tags
    tags = fmt.get("tags", {})
    ct_str = tags.get("creation_time", "")
    
    # --- streams ---
    for stream in meta.get("streams", []):
        codec_type = stream.get("codec_type", "")
        
        if codec_type == "video":
            w = stream.get("width", 0)
            h = stream.get("height", 0)
            info["resolution"] = f"{w}x{h}"
            info["codec"] = stream.get("codec_name", "")
            
            # fps: r_frame_rate è "30000/1001" etc
            rfr = stream.get("r_frame_rate", "0/1")
            try:
                num, den = rfr.split("/")
                info["fps"] = round(float(num) / float(den), 2)
            except (ValueError, ZeroDivisionError):
                pass
            
            # try creation_time from video stream tags
            if not ct_str:
                st_tags = stream.get("tags", {})
                ct_str = st_tags.get("creation_time", "")
        
        # GoPro GPMF data stream (codec_name = "gpmd" o codec_tag_string = "gpmd")
        codec_name = stream.get("codec_name", "")
        codec_tag = stream.get("codec_tag_string", "")
        if "gpmd" in codec_name.lower() or "gpmd" in codec_tag.lower():
            info["has_gps_stream"] = True
        # anche "data" stream con handler GoPro MET
        if codec_type == "data":
            st_tags = stream.get("tags", {})
            handler = st_tags.get("handler_name", "")
            if "GoPro MET" in handler or "gpmd" in handler.lower():
                info["has_gps_stream"] = True

    # Parse creation_time
    if ct_str:
        # Formati possibili: "2024-07-15T10:30:00.000000Z", "2024-07-15 10:30:00"
        for fmt_str in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z"):
            try:
                dt = datetime.strptime(ct_str, fmt_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                info["creation_time"] = dt
                info["creation_time_str"] = dt.isoformat()
                break
            except ValueError:
                continue

    return info





# ─────────────── GPX / CSV DATA ───────────────

def load_gpx_time_ranges() -> list:
    """
    Per ogni tappa, carica start/end time + trackpoints dal GPX.
    Ritorna lista di dict con stage_num, start_time, end_time, gpx_file, trackpoints.
    trackpoints = lista di {lat, lon, ele, time}.
    """
    import xml.etree.ElementTree as ET
    NS = {"gpx": "http://www.topografix.com/GPX/1/1"}
    
    stages = []
    gpx_files = sorted(Path(GPX_DIR).glob("*.gpx"))
    
    for gpx_file in gpx_files:
        match = re.search(r"tappa_?(\d+)", gpx_file.stem)
        if not match:
            continue
        stage_num = int(match.group(1))
        
        tree = ET.parse(str(gpx_file))
        root = tree.getroot()
        trackpoints = []
        for trkpt in root.findall(".//gpx:trkpt", NS):
            lat = float(trkpt.get("lat"))
            lon = float(trkpt.get("lon"))
            ele_el = trkpt.find("gpx:ele", NS)
            ele = float(ele_el.text) if ele_el is not None else 0.0
            time_el = trkpt.find("gpx:time", NS)
            t = None
            if time_el is not None:
                try:
                    t = datetime.strptime(time_el.text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            trackpoints.append({"lat": lat, "lon": lon, "ele": ele, "time": t})
        
        times = [tp["time"] for tp in trackpoints if tp["time"]]
        if times:
            stages.append({
                "stage_num": stage_num,
                "start_time": min(times),
                "end_time": max(times),
                "gpx_file": gpx_file.name,
                "trackpoints": trackpoints,
            })
    
    stages.sort(key=lambda s: s["stage_num"])
    return stages


def load_csv_data(stage_num: int) -> list:
    """Carica i dati CSV di una tappa."""
    csv_path = CSV_DIR / f"tappa_{stage_num:02d}.csv"
    if not csv_path.exists():
        csv_path = CSV_DIR / f"tappa{stage_num:02d}.csv"
    if not csv_path.exists():
        return []
    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────── MATCHING ───────────────

def match_video_to_stage_by_time(video_info: dict, stages: list) -> dict | None:
    """
    Associa un video a una tappa in base al timestamp di creazione.
    Fallback quando il GPS non è disponibile.
    """
    ct = video_info.get("creation_time")
    if ct is None:
        return None
    
    tolerance = timedelta(hours=TIME_TOLERANCE_H)
    best = None
    best_dist = None
    
    for stage in stages:
        s_start = stage["start_time"] - tolerance
        s_end = stage["end_time"] + tolerance
        
        if s_start <= ct <= s_end:
            stage_mid = stage["start_time"] + (stage["end_time"] - stage["start_time"]) / 2
            dist = abs((ct - stage_mid).total_seconds())
            if best is None or dist < best_dist:
                best = stage
                best_dist = dist
    
    return best


def match_video_to_stage_by_gps(gps_summary: dict, stages: list) -> tuple[dict | None, dict | None]:
    """
    Associa un video a una tappa usando le coordinate GPS estratte dal GPMF.
    Ritorna (stage, nearest_point_info) dove nearest_point_info ha:
      {distance_m, trackpoint_idx, lat, lon}
    """
    vlat = gps_summary["lat"]
    vlon = gps_summary["lon"]
    
    best_stage = None
    best_info = None
    best_dist = float("inf")
    
    for stage in stages:
        trackpoints = stage.get("trackpoints", [])
        for ti, tp in enumerate(trackpoints):
            d = haversine(vlat, vlon, tp["lat"], tp["lon"])
            if d < best_dist:
                best_dist = d
                best_stage = stage
                best_info = {
                    "distance_m": round(d, 1),
                    "trackpoint_idx": ti,
                    "lat": tp["lat"],
                    "lon": tp["lon"],
                }
    
    # Soglia: se il punto più vicino è a più di 5km, probabilmente non è sulla rotta
    if best_dist > 5000:
        return None, None
    
    return best_stage, best_info


def find_frame_for_gps(gps_summary: dict, stage: dict, csv_rows: list,
                       gpx_trackpoint_idx: int) -> dict:
    """
    Trova il frame CSV corrispondente alla posizione GPS del video.
    Usa l'indice del trackpoint GPX più vicino per calcolare il progresso.
    """
    result = {
        "method": "gps",
        "frame_start": 0,
        "frame_end": 0,
        "td_time_start": 0.0,
        "td_time_end": 0.0,
        "km_approx": 0.0,
        "progress_pct": 0.0,
        "gps_lat": gps_summary["lat"],
        "gps_lon": gps_summary["lon"],
        "gps_fix": gps_summary["best_fix"],
        "gps_points": gps_summary["total_points"],
    }
    
    if not csv_rows:
        return result
    
    trackpoints = stage.get("trackpoints", [])
    if not trackpoints:
        return result
    
    # Progresso = indice trackpoint / totale trackpoints
    progress = gpx_trackpoint_idx / max(1, len(trackpoints) - 1)
    progress = max(0.0, min(1.0, progress))
    
    total_frames = len(csv_rows)
    frame_start = int(progress * (total_frames - 1))
    
    # Stima frame_end: usa durata video / durata tappa GPX * totale frame
    gpx_duration = (stage["end_time"] - stage["start_time"]).total_seconds()
    # Non abbiamo la durata video qui, la aggiungiamo nel caller
    result["frame_start"] = frame_start
    result["frame_end"] = frame_start  # verrà aggiornato
    result["progress_pct"] = round(progress * 100, 1)
    
    if frame_start < len(csv_rows):
        result["td_time_start"] = float(csv_rows[frame_start].get("td_time", 0))
        result["km_approx"] = round(float(csv_rows[frame_start].get("cum_dist_m", 0)) / 1000, 1)
    
    return result


def find_frame_for_time(video_info: dict, stage: dict, csv_rows: list) -> dict:
    """
    Dato un video e la tappa associata, trova il frame CSV più vicino
    al timestamp di creazione del video.
    
    Ritorna dict con frame_start, frame_end, td_time_start, td_time_end,
    km_approx, progress_pct.
    """
    result = {
        "method": "time",
        "frame_start": 0,
        "frame_end": 0,
        "td_time_start": 0.0,
        "td_time_end": 0.0,
        "km_approx": 0.0,
        "progress_pct": 0.0,
    }
    
    if not csv_rows:
        return result
    
    ct = video_info["creation_time"]
    dur = video_info["duration_s"]
    
    # L'inizio della tappa nel GPX
    gpx_start = stage["start_time"]
    gpx_end = stage["end_time"]
    gpx_duration = (gpx_end - gpx_start).total_seconds()
    
    if gpx_duration <= 0:
        return result
    
    # Posizione del video nella timeline della tappa (0→1)
    video_start_offset = (ct - gpx_start).total_seconds()
    video_start_pct = max(0.0, min(1.0, video_start_offset / gpx_duration))
    video_end_pct = max(0.0, min(1.0, (video_start_offset + dur) / gpx_duration))
    
    total_frames = len(csv_rows)
    frame_start = int(video_start_pct * (total_frames - 1))
    frame_end = int(video_end_pct * (total_frames - 1))
    
    result["frame_start"] = frame_start
    result["frame_end"] = frame_end
    result["progress_pct"] = round(video_start_pct * 100, 1)
    
    # td_time dai CSV
    if frame_start < len(csv_rows):
        result["td_time_start"] = float(csv_rows[frame_start].get("td_time", 0))
    if frame_end < len(csv_rows):
        result["td_time_end"] = float(csv_rows[frame_end].get("td_time", 0))
    
    # km approssimativo
    if frame_start < len(csv_rows):
        result["km_approx"] = round(float(csv_rows[frame_start].get("cum_dist_m", 0)) / 1000, 1)
    
    return result


# ─────────────── MAIN ───────────────

def scan_videos(video_dir: Path) -> list:
    """Scansiona cartella e sottocartelle per video GoPro."""
    videos = []
    for root, dirs, files in os.walk(str(video_dir)):
        for f in sorted(files):
            ext = os.path.splitext(f)[1]
            if ext in VIDEO_EXTS:
                videos.append(os.path.join(root, f))
    return videos


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GoPro Video → Route Mapper")
    parser.add_argument("--video-dir", type=str, default=str(VIDEO_DIR),
                       help="Cartella con i video GoPro")
    parser.add_argument("--list", action="store_true",
                       help="Solo lista info video, senza matching")
    parser.add_argument("--output", type=str, default=str(OUT_DIR / "gopro_map.json"),
                       help="File output JSON")
    args = parser.parse_args()
    
    video_dir = Path(args.video_dir)
    if not video_dir.exists():
        print(f"ERRORE: cartella video non trovata: {video_dir}")
        print(f"Crea la cartella e mettici i video GoPro, oppure usa --video-dir")
        sys.exit(1)
    
    # Verifica ffprobe
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=10)
    except FileNotFoundError:
        print("ERRORE: ffprobe non trovato nel PATH.")
        print("Installa ffmpeg: winget install Gyan.FFmpeg")
        sys.exit(1)
    
    # 1. Scansiona video
    print(f"\n{'='*60}")
    print(f"  DESNIVEL — GoPro Video Mapper")
    print(f"{'='*60}")
    print(f"\nCartella video: {video_dir}")
    
    video_paths = scan_videos(video_dir)
    print(f"Video trovati: {len(video_paths)}")
    
    if not video_paths:
        print("Nessun video trovato. Estensioni cercate:", ", ".join(VIDEO_EXTS))
        sys.exit(0)
    
    # 2. Estrai info da ogni video
    print(f"\nEstrazione metadati...")
    videos_info = []
    for i, vp in enumerate(video_paths):
        try:
            info = extract_video_info(vp)
            videos_info.append(info)
            gps_marker = " [GPS]" if info["has_gps_stream"] else ""
            ct_str = info["creation_time_str"][:19] if info["creation_time_str"] else "???"
            dur_min = info["duration_s"] / 60
            print(f"  [{i+1:3d}/{len(video_paths)}] {info['file']}"
                  f"  {ct_str}  {dur_min:.1f}min  {info['resolution']}"
                  f"  {info['fps']}fps{gps_marker}")
        except Exception as e:
            print(f"  [{i+1:3d}/{len(video_paths)}] ERRORE {os.path.basename(vp)}: {e}")
    
    if args.list:
        # Solo lista, niente matching
        total_dur = sum(v["duration_s"] for v in videos_info)
        gps_count = sum(1 for v in videos_info if v["has_gps_stream"])
        print(f"\n--- Riepilogo ---")
        print(f"Video totali: {len(videos_info)}")
        print(f"Durata totale: {total_dur/3600:.1f}h")
        print(f"Con GPS: {gps_count}")
        return
    
    # 3. Carica dati GPX per matching temporale
    print(f"\nCaricamento tappe GPX...")
    stages = load_gpx_time_ranges()
    print(f"Tappe caricate: {len(stages)}")
    for s in stages:
        date_str = s["start_time"].strftime("%Y-%m-%d")
        dur_h = (s["end_time"] - s["start_time"]).total_seconds() / 3600
        print(f"  Tappa {s['stage_num']:2d}: {date_str}  ({dur_h:.1f}h)  {s['gpx_file']}")
    
    # 4. Estrai GPS da video con stream GPMF
    print(f"\nEstrazione GPS da stream GPMF...")
    gps_cache = {}  # path -> gps_summary
    gps_ok = 0
    for vi in videos_info:
        if vi["has_gps_stream"]:
            try:
                summary = extract_gps_summary(vi["path"])
                if summary and summary["total_points"] > 0:
                    gps_cache[vi["path"]] = summary
                    gps_ok += 1
                    fix_str = f"fix={summary['best_fix']}" if summary["best_fix"] >= 2 else "no-fix"
                    print(f"  {vi['file']}: {summary['total_points']} pts  "
                          f"lat={summary['lat']:.6f} lon={summary['lon']:.6f}  {fix_str}")
                else:
                    print(f"  {vi['file']}: nessun punto GPS")
            except Exception as e:
                print(f"  {vi['file']}: errore GPS: {e}")
    print(f"GPS estratto da {gps_ok}/{sum(1 for v in videos_info if v['has_gps_stream'])} video")

    # 5. Matching video → tappa (GPS preferred, timestamp fallback)
    print(f"\nMatching video → tappe...")
    results = []
    matched = 0
    unmatched_videos = []
    
    # Cache CSV per tappa
    csv_cache = {}
    
    for vi in videos_info:
        entry = {
            "file": vi["file"],
            "path": vi["path"],
            "creation_time": vi["creation_time_str"],
            "duration_s": vi["duration_s"],
            "resolution": vi["resolution"],
            "fps": vi["fps"],
            "has_gps": vi["has_gps_stream"],
            "stage": None,
            "mapping": None,
        }
        
        stage = None
        mapping = None
        match_method = None
        
        # Prova GPS matching
        gps_summary = gps_cache.get(vi["path"])
        if gps_summary:
            stage, nearest = match_video_to_stage_by_gps(gps_summary, stages)
            if stage:
                match_method = "gps"
                snum = stage["stage_num"]
                if snum not in csv_cache:
                    csv_cache[snum] = load_csv_data(snum)
                csv_rows = csv_cache[snum]
                mapping = find_frame_for_gps(
                    gps_summary, stage, csv_rows, nearest["trackpoint_idx"]
                )
                # Aggiorna frame_end con durata video
                gpx_dur = (stage["end_time"] - stage["start_time"]).total_seconds()
                if gpx_dur > 0 and csv_rows:
                    dur_frac = vi["duration_s"] / gpx_dur
                    frame_span = int(dur_frac * len(csv_rows))
                    mapping["frame_end"] = min(mapping["frame_start"] + frame_span,
                                               len(csv_rows) - 1)
                if mapping["frame_end"] < len(csv_rows):
                    mapping["td_time_end"] = float(
                        csv_rows[mapping["frame_end"]].get("td_time", 0))
                mapping["gps_match_distance_m"] = nearest["distance_m"]
        
        # Fallback: timestamp matching
        if not stage:
            stage = match_video_to_stage_by_time(vi, stages)
            if stage:
                match_method = "time"
                snum = stage["stage_num"]
                if snum not in csv_cache:
                    csv_cache[snum] = load_csv_data(snum)
                mapping = find_frame_for_time(vi, stage, csv_cache[snum])
        
        if stage:
            matched += 1
            entry["stage"] = stage["stage_num"]
            entry["mapping"] = mapping
            method_tag = f"[{match_method}]" if match_method else ""
            dist_info = ""
            if match_method == "gps" and mapping:
                dist_info = f"  ~{mapping.get('gps_match_distance_m', 0):.0f}m"
            print(f"  ✓ {vi['file']} → Tappa {stage['stage_num']:2d}"
                  f"  frame {mapping['frame_start']}-{mapping['frame_end']}"
                  f"  km {mapping['km_approx']}"
                  f"  ({mapping['progress_pct']}%) {method_tag}{dist_info}")
        else:
            unmatched_videos.append(vi["file"])
        
        results.append(entry)
    
    # 6. Riepilogo
    print(f"\n{'─'*60}")
    print(f"Matched: {matched}/{len(videos_info)}")
    if unmatched_videos:
        print(f"Non matchati ({len(unmatched_videos)}):")
        for f in unmatched_videos[:10]:
            print(f"  ✗ {f}")
        if len(unmatched_videos) > 10:
            print(f"  ... e altri {len(unmatched_videos)-10}")
    
    # Stats per tappa
    stage_counts = {}
    stage_durations = {}
    for r in results:
        if r["stage"]:
            s = r["stage"]
            stage_counts[s] = stage_counts.get(s, 0) + 1
            stage_durations[s] = stage_durations.get(s, 0) + r["duration_s"]
    
    if stage_counts:
        print(f"\nVideo per tappa:")
        for s in sorted(stage_counts):
            dur_min = stage_durations[s] / 60
            print(f"  Tappa {s:2d}: {stage_counts[s]:3d} video ({dur_min:.0f} min)")
    
    # 7. Salva JSON
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = args.output
    
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "video_dir": str(video_dir),
        "total_videos": len(videos_info),
        "matched_videos": matched,
        "unmatched_videos": len(unmatched_videos),
        "stages_with_video": len(stage_counts),
        "total_video_duration_s": sum(v["duration_s"] for v in videos_info),
        "videos": results,
    }
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nSalvato: {out_path}")


if __name__ == "__main__":
    main()

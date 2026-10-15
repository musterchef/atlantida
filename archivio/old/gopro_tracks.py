"""
DESNIVEL — GoPro Video GPS Track Extractor
============================================
Estrae la traccia GPS completa da ogni video GoPro e salva:
  - output/gopro_tracks.json  → tutte le tracce GPS in un file
  - output/gopro_gpx/         → un file .gpx per ogni video (opzionale)

Usa il parser GPMF di gpmf_extract.py.

Uso:
  python gopro_tracks.py                         # scansiona gopro/
  python gopro_tracks.py --video-dir D:\GoPro    # cartella custom
  python gopro_tracks.py --gpx                   # genera anche file .gpx
  python gopro_tracks.py --single video.mp4      # singolo video
"""

import json
import os
import sys
import math
from pathlib import Path
from datetime import datetime, timezone

from gpmf_extract import extract_gps

# ─────────────────── CONFIG ────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR   = PROJECT_DIR / "gopro"
OUT_DIR     = PROJECT_DIR / "output"
GPX_OUT_DIR = PROJECT_DIR / "gpx" / "gopro"
GOPRO_MAP   = OUT_DIR / "gopro_map.json"
VIDEO_EXTS  = {".mp4", ".MP4", ".360"}
# ────────────────────────────────────────────────


def load_stage_map() -> dict[str, int]:
    """Carica la mappa video→tappa da gopro_map.json."""
    if not GOPRO_MAP.exists():
        return {}
    with open(GOPRO_MAP, encoding="utf-8") as f:
        data = json.load(f)
    return {v["file"]: v["stage"] for v in data.get("videos", []) if v.get("stage")}


def scan_videos(video_dir: Path) -> list[str]:
    videos = []
    for root, _, files in os.walk(str(video_dir)):
        for f in sorted(files):
            if os.path.splitext(f)[1] in VIDEO_EXTS:
                videos.append(os.path.join(root, f))
    return videos


def haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def clean_track(points: list[dict]) -> list[dict]:
    """
    Pulisce la traccia GPS:
      - preferisce punti con fix >= 2
      - rimuove punti duplicati consecutivi (stessa lat/lon)
      - rimuove spike (salti > 500m tra campioni consecutivi)
      - aggiunge distanza cumulativa
    """
    if not points:
        return []

    # Separa punti con fix e senza
    fixed = [p for p in points if p["gps_fix"] >= 2]
    # Se ci sono punti con fix, usa solo quelli
    src = fixed if fixed else points

    cleaned = [dict(src[0])]
    cleaned[0]["cum_dist_m"] = 0.0
    cum_dist = 0.0

    for i in range(1, len(src)):
        prev = cleaned[-1]
        cur = src[i]

        # Skip duplicati esatti
        if cur["lat"] == prev["lat"] and cur["lon"] == prev["lon"]:
            continue

        # Skip spike (> 500m tra campioni consecutivi)
        d = haversine(prev["lat"], prev["lon"], cur["lat"], cur["lon"])
        if d > 500:
            continue

        cum_dist += d
        cur = dict(cur)
        cur["cum_dist_m"] = round(cum_dist, 1)
        cleaned.append(cur)

    return cleaned


def track_stats(points: list[dict]) -> dict:
    """Calcola statistiche della traccia."""
    if not points:
        return {"total_points": 0}

    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    alts = [p["alt"] for p in points]
    speeds = [p["speed_2d"] for p in points]
    fixed = [p for p in points if p["gps_fix"] >= 2]

    total_dist = points[-1].get("cum_dist_m", 0) if points else 0

    return {
        "total_points": len(points),
        "fixed_points": len(fixed),
        "best_fix": max(p["gps_fix"] for p in points),
        "total_distance_m": round(total_dist, 1),
        "lat_min": round(min(lats), 7),
        "lat_max": round(max(lats), 7),
        "lon_min": round(min(lons), 7),
        "lon_max": round(max(lons), 7),
        "alt_min": round(min(alts), 1),
        "alt_max": round(max(alts), 1),
        "speed_avg_ms": round(sum(speeds) / len(speeds), 2) if speeds else 0,
        "speed_max_ms": round(max(speeds), 2) if speeds else 0,
    }


def points_to_gpx(points: list[dict], video_name: str) -> str:
    """Genera contenuto GPX dalla lista punti."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="Desnivel GoPro Track Extractor"',
        '     xmlns="http://www.topografix.com/GPX/1/1">',
        f'  <trk><name>{video_name}</name><trkseg>',
    ]
    for pt in points:
        lines.append(
            f'    <trkpt lat="{pt["lat"]:.7f}" lon="{pt["lon"]:.7f}">'
            f'<ele>{pt["alt"]:.1f}</ele></trkpt>'
        )
    lines.append('  </trkseg></trk>')
    lines.append('</gpx>')
    return "\n".join(lines)


def extract_track(video_path: str) -> dict:
    """
    Estrae e pulisce la traccia GPS da un video.
    Ritorna dict pronto per JSON con punti, stats, metadata.
    """
    raw_points = extract_gps(video_path)
    cleaned = clean_track(raw_points)

    # Punti compatti per JSON (senza duplicare chiavi verbose)
    track = []
    for pt in cleaned:
        track.append({
            "lat": round(pt["lat"], 7),
            "lon": round(pt["lon"], 7),
            "alt": round(pt["alt"], 1),
            "spd": round(pt["speed_2d"], 2),
            "fix": pt["gps_fix"],
            "t": pt.get("time_offset_s", 0),
            "d": pt.get("cum_dist_m", 0),
        })

    return {
        "file": os.path.basename(video_path),
        "path": video_path,
        "raw_points": len(raw_points),
        "stats": track_stats(cleaned),
        "track": track,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GoPro GPS Track Extractor")
    parser.add_argument("--video-dir", type=str, default=str(VIDEO_DIR))
    parser.add_argument("--single", type=str, default=None,
                       help="Estrai da un singolo video")
    parser.add_argument("--gpx", action="store_true",
                       help="Genera anche file .gpx per ogni video")
    parser.add_argument("--output", type=str,
                       default=str(OUT_DIR / "gopro_tracks.json"))
    args = parser.parse_args()

    # Singolo video
    if args.single:
        if not os.path.exists(args.single):
            print(f"ERRORE: file non trovato: {args.single}")
            sys.exit(1)
        video_paths = [args.single]
    else:
        video_dir = Path(args.video_dir)
        if not video_dir.exists():
            print(f"ERRORE: cartella non trovata: {video_dir}")
            sys.exit(1)
        video_paths = scan_videos(video_dir)

    print(f"\n{'='*60}")
    print(f"  DESNIVEL — GoPro GPS Track Extractor")
    print(f"{'='*60}")
    # Mappa video → tappa
    stage_map = load_stage_map()
    print(f"\nVideo da processare: {len(video_paths)}")
    if stage_map:
        print(f"Mappa tappe caricata: {len(stage_map)} video")

    if not video_paths:
        print("Nessun video trovato.")
        sys.exit(0)

    # Estrai tracce
    all_tracks = []
    total_pts = 0
    for i, vp in enumerate(video_paths):
        name = os.path.basename(vp)
        try:
            result = extract_track(vp)
            all_tracks.append(result)
            n = result["stats"]["total_points"]
            total_pts += n
            dist = result["stats"]["total_distance_m"]
            fix = result["stats"]["best_fix"]
            fix_str = f"fix={fix}" if fix >= 2 else "no-fix"
            print(f"  [{i+1:3d}/{len(video_paths)}] {name}"
                  f"  {n} pts  {dist:.0f}m  {fix_str}")

            # GPX export — sotto gpx/gopro/tappaXX/
            if args.gpx and result["track"]:
                stem = Path(name).stem
                stage = stage_map.get(name)
                if stage:
                    tappa_str = f"tappa{stage:02d}"
                    gpx_dir = GPX_OUT_DIR / tappa_str
                    gpx_name = f"{tappa_str}_{stem}.gpx"
                else:
                    gpx_dir = GPX_OUT_DIR / "no_tappa"
                    gpx_name = f"{stem}.gpx"
                os.makedirs(gpx_dir, exist_ok=True)
                gpx_path = gpx_dir / gpx_name
                # Ricostruisci punti completi per GPX
                gpx_pts = [{"lat": p["lat"], "lon": p["lon"], "alt": p["alt"]}
                           for p in result["track"]]
                gpx_content = points_to_gpx(gpx_pts, name)
                with open(gpx_path, "w", encoding="utf-8") as f:
                    f.write(gpx_content)

        except Exception as e:
            print(f"  [{i+1:3d}/{len(video_paths)}] {name}  ERRORE: {e}")

    # Salva JSON
    os.makedirs(OUT_DIR, exist_ok=True)
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(all_tracks),
        "total_gps_points": total_pts,
        "tracks": all_tracks,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'─'*60}")
    print(f"Tracce estratte: {len(all_tracks)}")
    print(f"Punti GPS totali: {total_pts}")
    print(f"Salvato: {args.output}")
    if args.gpx:
        print(f"GPX files: {GPX_OUT_DIR}/")


if __name__ == "__main__":
    main()

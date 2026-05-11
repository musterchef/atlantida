"""
GPMF GPS Extractor per GoPro Hero 10+
======================================
Estrae coordinate GPS dallo stream GPMF (GoPro Metadata Format)
embedded nei video .MP4.

Usa ffmpeg per estrarre i pacchetti raw, poi parsa il formato KLV.

Referenza: https://github.com/gopro/gpmf-parser
"""

import subprocess
import struct
import tempfile
import os
from pathlib import Path


def _extract_gpmf_packets(video_path: str) -> list[bytes]:
    """
    Estrae i pacchetti GPMF dal video usando ffmpeg.
    Ritorna lista di bytes, un elemento per pacchetto (~1/sec).
    """
    # Trova l'indice dello stream gpmd
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-show_streams",
        "-select_streams", "d", "-print_format", "json",
        video_path
    ]
    import json
    result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return []

    meta = json.loads(result.stdout)
    gpmd_index = None
    for stream in meta.get("streams", []):
        if stream.get("codec_tag_string") == "gpmd":
            gpmd_index = stream["index"]
            break

    if gpmd_index is None:
        return []

    # Estrai pacchetti via ffprobe -show_packets per ottenere offset/size,
    # poi leggi direttamente. Ma è più semplice usare ffmpeg -f data.
    # Approach: ffmpeg dump to pipe
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-v", "quiet", "-y",
            "-i", video_path,
            "-map", f"0:{gpmd_index}",
            "-codec", "copy",
            "-f", "data",
            tmp_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)

        with open(tmp_path, "rb") as f:
            raw = f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not raw:
        return []

    # Parse top-level DEVC entries properly using KLV structure
    packets = []
    i = 0
    while i < len(raw) - 8:
        key = raw[i:i+4]
        if key == b"DEVC":
            struct_size = raw[i+5]
            repeat = struct.unpack(">H", raw[i+6:i+8])[0]
            payload_size = struct_size * repeat
            padded = payload_size + (4 - payload_size % 4) % 4
            pkt_end = i + 8 + padded
            packets.append(raw[i:pkt_end])
            i = pkt_end
        else:
            i += 4  # skip non-DEVC data

    return packets


def _parse_klv(data: bytes, offset: int = 0, end: int = None) -> list[tuple]:
    """
    Parsa KLV GPMF. Ritorna lista di (key, type, struct_size, repeat, payload_bytes, children).
    """
    if end is None:
        end = len(data)

    items = []
    i = offset
    while i < end - 8:
        # Header: 4-char key, 1-byte type, 1-byte struct_size, 2-byte repeat
        key = data[i:i+4]
        try:
            k = key.decode("ascii")
        except UnicodeDecodeError:
            break

        if not k.isprintable():
            break

        type_byte = data[i+4]
        struct_size = data[i+5]
        repeat = struct.unpack(">H", data[i+6:i+8])[0]
        payload_size = struct_size * repeat
        padded = payload_size + (4 - payload_size % 4) % 4

        payload = data[i+8:i+8+payload_size] if payload_size > 0 else b""

        children = []
        # Type 0x00 = nested container
        if type_byte == 0 and struct_size > 0:
            children = _parse_klv(data, i+8, i+8+padded)

        items.append((k, type_byte, struct_size, repeat, payload, children))

        if struct_size == 0 and type_byte == 0:
            i += 8
        else:
            i += 8 + padded

    return items


def _find_in_klv(items: list, key: str) -> list:
    """Cerca ricorsivamente un key nel KLV tree."""
    results = []
    for k, t, ss, rp, payload, children in items:
        if k == key:
            results.append((k, t, ss, rp, payload, children))
        if children:
            results.extend(_find_in_klv(children, key))
    return results


def _find_gps_in_device(items: list) -> list[dict]:
    """
    Cerca GPS5 o GPS9 dentro un albero KLV con il relativo SCAL.
    Ritorna lista di {lat, lon, alt, speed_2d, speed_3d}.
    """
    points = []

    # Cerca dentro STRM (stream) children
    for k, t, ss, rp, payload, children in items:
        if k == "STRM" and children:
            # Dentro STRM cerchiamo GPS5 + SCAL
            gps5_list = _find_in_klv(children, "GPS5")
            gps9_list = _find_in_klv(children, "GPS9")
            scal_list = _find_in_klv(children, "SCAL")
            gpsu_list = _find_in_klv(children, "GPSU")  # GPS UTC time
            gpsf_list = _find_in_klv(children, "GPSF")  # GPS fix (0=no, 2=2D, 3=3D)
            gpsp_list = _find_in_klv(children, "GPSP")  # GPS precision (DOP)

            # Check GPS fix
            gps_fix = 0
            if gpsf_list:
                _, _, fix_ss, fix_rp, fix_payload, _ = gpsf_list[0]
                if len(fix_payload) >= 4:
                    gps_fix = struct.unpack(">I", fix_payload[:4])[0]

            # Get scale factors
            scales = []
            if scal_list:
                _, _, scal_ss, scal_rp, scal_payload, _ = scal_list[0]
                for j in range(scal_rp):
                    off = j * scal_ss
                    if scal_ss == 4 and off + 4 <= len(scal_payload):
                        scales.append(struct.unpack(">i", scal_payload[off:off+4])[0])
                    elif scal_ss == 2 and off + 2 <= len(scal_payload):
                        scales.append(struct.unpack(">h", scal_payload[off:off+2])[0])

            # GPS UTC timestamp
            gps_time_str = ""
            if gpsu_list:
                _, _, _, _, gpsu_payload, _ = gpsu_list[0]
                try:
                    gps_time_str = gpsu_payload.rstrip(b"\x00").decode("ascii")
                except UnicodeDecodeError:
                    pass

            # Parse GPS5: lat(i32), lon(i32), alt(i32), speed2d(i32), speed3d(i32)
            if gps5_list and len(scales) >= 5:
                _, _, gps_ss, gps_rp, gps_payload, _ = gps5_list[0]
                for j in range(gps_rp):
                    off = j * gps_ss
                    if gps_ss == 20 and off + 20 <= len(gps_payload):
                        vals = struct.unpack(">iiiii", gps_payload[off:off+20])
                        pt = {
                            "lat":      vals[0] / scales[0],
                            "lon":      vals[1] / scales[1],
                            "alt":      vals[2] / scales[2],
                            "speed_2d": vals[3] / scales[3],
                            "speed_3d": vals[4] / scales[4],
                            "gps_time": gps_time_str,
                            "gps_fix":  gps_fix,
                        }
                        # Sanity check: lat in [-90, 90], lon in [-180, 180]
                        if -90 <= pt["lat"] <= 90 and -180 <= pt["lon"] <= 180:
                            points.append(pt)

            # Parse GPS9: lat(i32), lon(i32), alt(i32), speed2d(i32), speed3d(i32),
            #             days(i32), secs(i32), DOP(i32), fix(i32)  — 36 bytes
            elif gps9_list and len(scales) >= 5:
                _, _, gps_ss, gps_rp, gps_payload, _ = gps9_list[0]
                for j in range(gps_rp):
                    off = j * gps_ss
                    if off + gps_ss <= len(gps_payload):
                        # GPS9 has variable struct size, typically 36 bytes
                        if gps_ss >= 36:
                            vals = struct.unpack(">iiiiiiiii", gps_payload[off:off+36])
                            pt = {
                                "lat":      vals[0] / scales[0],
                                "lon":      vals[1] / scales[1],
                                "alt":      vals[2] / scales[2],
                                "speed_2d": vals[3] / scales[3],
                                "speed_3d": vals[4] / scales[4],
                                "gps_time": gps_time_str,
                                "gps_fix":  gps_fix,
                            }
                            if -90 <= pt["lat"] <= 90 and -180 <= pt["lon"] <= 180:
                                points.append(pt)

        # Recurse into nested containers (DEVC has children)
        if children:
            points.extend(_find_gps_in_device(children))

    return points


def extract_gps(video_path: str, require_fix: bool = False) -> list[dict]:
    """
    API principale: estrae punti GPS da un video GoPro.
    
    Args:
        video_path: percorso al file video
        require_fix: se True, scarta punti con gps_fix < 2
    
    Ritorna lista di dict:
      {lat, lon, alt, speed_2d, speed_3d, gps_time, gps_fix, packet_idx}
    
    Ogni pacchetto GPMF (~1/sec) contiene ~18 punti GPS (18 Hz su Hero 10).
    """
    packets = _extract_gpmf_packets(video_path)
    if not packets:
        return []

    all_points = []
    for pkt_idx, pkt_data in enumerate(packets):
        klv = _parse_klv(pkt_data)
        points = _find_gps_in_device(klv)
        for pt in points:
            pt["packet_idx"] = pkt_idx
            pt["time_offset_s"] = pkt_idx  # ~1 packet/sec
        all_points.extend(points)

    if require_fix:
        all_points = [p for p in all_points if p["gps_fix"] >= 2]

    return all_points


def extract_gps_summary(video_path: str) -> dict | None:
    """
    Estrae un riassunto GPS rapido: posizione mediana, fix migliore,
    numero punti totali. Utile per matching veloce senza processare tutto.
    """
    points = extract_gps(video_path)
    if not points:
        return None

    # Preferisci punti con fix se disponibili
    fixed = [p for p in points if p["gps_fix"] >= 2]
    src = fixed if fixed else points

    lats = [p["lat"] for p in src]
    lons = [p["lon"] for p in src]
    alts = [p["alt"] for p in src]

    # Mediana per robustezza
    lats.sort()
    lons.sort()
    alts.sort()
    mid = len(lats) // 2

    return {
        "lat": lats[mid],
        "lon": lons[mid],
        "alt": alts[mid],
        "total_points": len(points),
        "fixed_points": len(fixed),
        "best_fix": max(p["gps_fix"] for p in points),
        "gps_points": points,  # all points for detailed matching
    }


# ─── CLI test ───
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python gpmf_extract.py <video.mp4>")
        sys.exit(1)

    video = sys.argv[1]
    print(f"Estrazione GPS da: {video}\n")

    points = extract_gps(video)
    print(f"Punti GPS estratti: {len(points)}")

    if points:
        print(f"\nPrimi 10 punti:")
        for i, pt in enumerate(points[:10]):
            print(f"  [{i:3d}] lat={pt['lat']:.7f}  lon={pt['lon']:.7f}"
                  f"  alt={pt['alt']:.1f}m  spd={pt['speed_2d']:.1f}m/s"
                  f"  fix={pt['gps_fix']}  t={pt['gps_time']}")

        print(f"\nUltimi 5 punti:")
        for pt in points[-5:]:
            print(f"  lat={pt['lat']:.7f}  lon={pt['lon']:.7f}"
                  f"  alt={pt['alt']:.1f}m  spd={pt['speed_2d']:.1f}m/s")

        # Bounding box
        lats = [p["lat"] for p in points]
        lons = [p["lon"] for p in points]
        print(f"\nBBox: lat [{min(lats):.6f}, {max(lats):.6f}]"
              f"  lon [{min(lons):.6f}, {max(lons):.6f}]")

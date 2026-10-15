"""Pre-popolatore semi-automatico di `data/poi.json`.

Workflow:

1. Lancia `desnivel-discover-poi --gpx gpx/ --buffer-km 1.0
   --output data/poi_candidates.json`.
2. Lo script costruisce un buffer (bounding box leggermente espanso)
   intorno alle tracce e interroga Overpass per nodi/way con tag:
       - `place ~ city|town|village|hamlet`
       - `historic ~ castle|monastery|ruins|fort|tower`
       - `tourism = attraction`
3. Per ogni risultato unico (deduplicato per nome + coord arrotondate
   a ~10 m) propone un raggio default in base al tag.
4. Tu apri il JSON, cancelli cio' che non ti interessa, eventualmente
   correggi `radius_m`, lo rinomini `data/poi.json`. Il runtime non
   chiama mai rete: legge solo il JSON curato.

Dipendenza opzionale: `requests` (`pip install -e .[discover]`).
"""
from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


_OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Raggio di default per categoria (metri). Override per voce nel JSON.
_RADIUS_DEFAULT: dict[str, float] = {
    "city": 5000.0,
    "town": 1500.0,
    "village": 600.0,
    "hamlet": 300.0,
    "castle": 300.0,
    "monastery": 300.0,
    "ruins": 250.0,
    "fort": 300.0,
    "tower": 200.0,
    "attraction": 300.0,
    "poi": 300.0,
}


@dataclass
class _Candidate:
    name: str
    lat: float
    lon: float
    radius_m: float
    kind: str
    tags: list[str]
    osm_id: str
    source_tag: str  # es. "place=town" — utile in revisione manuale


# ---------- 1. Bounding box delle tracce ------------------------------------


def _track_points(gpx_path: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """Estrae array (lat, lon) di tutti i trkpt da un GPX (no resample)."""
    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    try:
        tree = ET.parse(gpx_path)
    except ET.ParseError:
        return None
    pts = tree.getroot().findall(".//g:trkpt", ns)
    if not pts:
        pts = tree.getroot().findall(".//trkpt")
    if not pts:
        return None
    lats = np.array([float(p.attrib["lat"]) for p in pts])
    lons = np.array([float(p.attrib["lon"]) for p in pts])
    return lats, lons


def _track_bbox(gpx_path: Path) -> tuple[float, float, float, float] | None:
    """Bbox (minlat, minlon, maxlat, maxlon) leggendo direttamente l'XML.

    Evita la dipendenza da `desnivel.loader` (che fa resample, derive...).
    """
    pts = _track_points(gpx_path)
    if pts is None:
        return None
    lats, lons = pts
    return float(lats.min()), float(lons.min()), float(lats.max()), float(lons.max())


def _expand_bbox(
    bbox: tuple[float, float, float, float], buffer_km: float,
) -> tuple[float, float, float, float]:
    minlat, minlon, maxlat, maxlon = bbox
    dlat = buffer_km / 111.0  # 1 grado lat ~ 111 km
    mid_lat = (minlat + maxlat) / 2.0
    dlon = buffer_km / (111.0 * max(math.cos(math.radians(mid_lat)), 0.1))
    return minlat - dlat, minlon - dlon, maxlat + dlat, maxlon + dlon


# ---------- 2. Query Overpass ----------------------------------------------


def _overpass_query(bbox: tuple[float, float, float, float]) -> str:
    s, w, n, e = bbox
    bb = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:180];
(
  node["place"~"city|town|village|hamlet"]({bb});
  node["historic"~"castle|monastery|ruins|fort|tower"]({bb});
  way["historic"~"castle|monastery|ruins|fort|tower"]({bb});
  node["tourism"="attraction"]({bb});
);
out center tags;
""".strip()


def _fetch_overpass(query: str) -> dict:
    try:
        import requests  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Manca `requests`. Installa con `pip install -e .[discover]`."
        ) from exc
    resp = requests.post(
        _OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "desnivel-discover-poi/0.1 (offline curator)"},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()


# ---------- 3. Da elementi OSM a candidati ----------------------------------


def _kind_and_source(tags: dict[str, str]) -> tuple[str, str] | None:
    """Ritorna (kind, source_tag) o None se l'elemento e' da scartare."""
    if "place" in tags and tags["place"] in _RADIUS_DEFAULT:
        return tags["place"], f"place={tags['place']}"
    if "historic" in tags and tags["historic"] in _RADIUS_DEFAULT:
        return tags["historic"], f"historic={tags['historic']}"
    if tags.get("tourism") == "attraction":
        return "attraction", "tourism=attraction"
    return None


def _candidates_from_osm(payload: dict) -> list[_Candidate]:
    out: list[_Candidate] = []
    seen: set[tuple[str, int, int]] = set()
    for el in payload.get("elements", []):
        tags = el.get("tags", {}) or {}
        name = tags.get("name")
        if not name:
            continue
        info = _kind_and_source(tags)
        if info is None:
            continue
        kind, source_tag = info
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue
        key = (name.lower(), round(lat * 1e4), round(lon * 1e4))
        if key in seen:
            continue
        seen.add(key)
        out.append(_Candidate(
            name=name,
            lat=float(lat),
            lon=float(lon),
            radius_m=_RADIUS_DEFAULT[kind],
            kind=kind,
            tags=[],
            osm_id=f"{el['type'][0]}{el['id']}",
            source_tag=source_tag,
        ))
    return out


# ---------- 4. Main CLI -----------------------------------------------------


def _collect_stages(
    gpx_arg: Path,
) -> list[tuple[str, tuple[float, float, float, float], tuple[np.ndarray, np.ndarray]]]:
    """Per ogni GPX ritorna (stem, bbox, (lats, lons) sottocampionati)."""
    if gpx_arg.is_dir():
        files = sorted(gpx_arg.glob("*.gpx"))
    elif gpx_arg.is_file():
        files = [gpx_arg]
    else:
        raise SystemExit(f"Percorso GPX non trovato: {gpx_arg}")
    out = []
    for f in files:
        pts = _track_points(f)
        if pts is None:
            continue
        lats, lons = pts
        bbox = (float(lats.min()), float(lons.min()),
                float(lats.max()), float(lons.max()))
        step = max(1, lats.size // 500)
        out.append((f.stem, bbox, (lats[::step], lons[::step])))
    return out


def _min_distance_to_track_m(
    lat: float, lon: float, track: tuple[np.ndarray, np.ndarray],
) -> float:
    lats, lons = track
    phi1 = math.radians(lat)
    phi2 = np.radians(lats)
    dphi = np.radians(lats - lat)
    dlmb = np.radians(lons - lon)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb / 2.0) ** 2
    d = 2.0 * 6_371_000.0 * np.arcsin(np.sqrt(np.minimum(a, 1.0)))
    return float(d.min())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Pre-popolatore di candidati POI da Overpass. Una query per "
            "tappa (bbox stretto), poi unione globale deduplicata. "
            "Output: JSON da rivedere e rinominare in data/poi.json."
        ),
    )
    p.add_argument("--gpx", type=Path, required=True,
                   help="File .gpx o cartella con .gpx.")
    p.add_argument("--buffer-km", type=float, default=1.0,
                   help="Espansione del bounding box per tappa in km (default 1.0).")
    p.add_argument("--output", type=Path, default=Path("data/poi_candidates.json"))
    args = p.parse_args(argv)

    stages = _collect_stages(args.gpx)
    if not stages:
        raise SystemExit("Nessuna traccia GPX leggibile.")
    print(f"Tappe da elaborare: {len(stages)}")

    buffer_m = args.buffer_km * 1000.0
    # Dedup globale: stesso POI vicino al confine fra due tappe non duplicato.
    seen: set[tuple[str, int, int]] = set()
    all_filtered: list[_Candidate] = []

    for stem, bbox, track in stages:
        expanded = _expand_bbox(bbox, args.buffer_km)
        query = _overpass_query(expanded)
        print(f"  [{stem}] Overpass... ", end="", flush=True)
        payload = _fetch_overpass(query)
        raw = _candidates_from_osm(payload)
        kept = []
        for c in raw:
            key = (c.name.lower(), round(c.lat * 1e4), round(c.lon * 1e4))
            if key in seen:
                continue
            if _min_distance_to_track_m(c.lat, c.lon, track) > buffer_m:
                continue
            seen.add(key)
            kept.append(c)
        all_filtered.extend(kept)
        print(f"{len(raw)} grezzi -> {len(kept)} mantenuti")

    print(f"Totale candidati unici: {len(all_filtered)}")

    rank = {k: i for i, k in enumerate(
        ["city", "town", "village", "hamlet", "castle", "monastery",
         "fort", "tower", "ruins", "attraction"])}
    all_filtered.sort(key=lambda c: (rank.get(c.kind, 99), c.name.lower()))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([asdict(c) for c in all_filtered], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Scritto {args.output}")
    print("Revisione: cancella le voci che non vuoi, correggi radius_m,")
    print("rimuovi 'osm_id'/'source_tag', e rinomina in data/poi.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

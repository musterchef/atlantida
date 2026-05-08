"""
DESNIVEL — POI Discovery along route
=====================================
Cerca punti di interesse iconici lungo le 12 tappe usando:
  1. Wikipedia Geosearch (posti famosi con pagina Wikipedia)
  2. Overpass / OpenStreetMap (viewpoint, monumenti, castelli, UNESCO)

Campiona ogni ~5km sul percorso, cerca nel raggio di 1km.
Salva risultati incrementali (riprende se interrotto).

Output: output/poi_discovery.json

Uso:
  cd src
  .venv\Scripts\python.exe poi_discovery.py
"""

import xml.etree.ElementTree as ET
import math, json, os, time, sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Serve 'requests': pip install requests")
    sys.exit(1)

# ─────────────── CONFIG ─────────────────
PROJECT_DIR     = Path(__file__).resolve().parent.parent
GPX_DIR         = PROJECT_DIR / "gpx"
OUT_DIR         = PROJECT_DIR / "output"
RESULT_FILE     = OUT_DIR / "poi_discovery.json"
SAMPLE_EVERY_KM = 2.0       # campiona un punto ogni N km
SEARCH_RADIUS_M = 100      # raggio di ricerca in metri
RATE_LIMIT_S    = 1.2        # pausa tra chiamate API (secondi)
NS              = {"gpx": "http://www.topografix.com/GPX/1/1"}

# ─────────────── FILTRI POI ─────────────
# Modifica queste liste per controllare cosa viene tenuto/scartato

# Articoli Wikipedia con meno di N byte vengono scartati (stub, pagine vuote)
WIKI_MIN_PAGE_SIZE = 5000

# Parole nel titolo → scarta (case-insensitive, match parziale)
TITLE_BLACKLIST = [
    "strada", "via ", "viale", "piazzale", "contrada", "contrade",
    "parrocchia", "diocesi", "circoscrizione",
    "scuola", "liceo", "istituto",
    "ospedale", "clinica",
    "stazione di", "fermata",
    "quartiere", "frazione", "municipio",
    "campionato", "stagione", "serie a", "serie b",
    "associazione", "società sportiva", "calcio",
]

# Parole nel titolo → tieni sempre (bypass size filter)
TITLE_WHITELIST = [
    "castello", "castel ", "fortezza", "torre",
    "cattedrale", "duomo", "basilica", "abbazia", "chiesa di",
    "museo", "galleria", "palazzo",
    "parco nazionale", "riserva naturale", "area marina",
    "unesco", "patrimonio",
    "ponte", "acquedotto", "anfiteatro", "teatro",
    "faro", "santuario", "monastero", "certosa",
    "villa ", "giardino",
]


def _is_blacklisted(title):
    """True se il titolo contiene parole della blacklist."""
    t = title.lower()
    return any(bl in t for bl in TITLE_BLACKLIST)


def _is_whitelisted(title):
    """True se il titolo contiene parole della whitelist (bypass size filter)."""
    t = title.lower()
    return any(wl in t for wl in TITLE_WHITELIST)


def _get_page_sizes(pageids):
    """Chiede a Wikipedia la dimensione delle pagine (batch)."""
    if not pageids:
        return {}
    ids_str = "|".join(str(pid) for pid in pageids)
    params = {
        "action": "query",
        "pageids": ids_str,
        "prop": "info",
        "format": "json",
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        return {int(pid): p.get("length", 0) for pid, p in pages.items()}
    except Exception:
        return {}

# ────────────────────────────────────────

WIKI_API = "https://it.wikipedia.org/w/api.php"
OVERPASS_API = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "Desnivel/1.0 (art project; marco; Python/requests)"}

OVERPASS_QUERY_TPL = """
[out:json][timeout:10];
(
  node["historic"](around:{radius},{lat},{lon});
  node["tourism"~"attraction|viewpoint|museum|artwork"](around:{radius},{lat},{lon});
  node["heritage"](around:{radius},{lat},{lon});
  node["building"~"castle|cathedral|church|chapel"](around:{radius},{lat},{lon});
  way["historic"](around:{radius},{lat},{lon});
  way["tourism"~"attraction|viewpoint|museum"](around:{radius},{lat},{lon});
);
out center tags;
"""


def haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(rlat1)*math.cos(rlat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def parse_gpx_points(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    points = []
    for trkpt in root.findall(".//gpx:trkpt", NS):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        points.append((lat, lon))
    return points


def sample_points(points, every_km):
    """Campiona punti ogni N km lungo il percorso."""
    if not points:
        return []
    samples = [points[0]]
    cum_dist = 0.0
    last_sample_dist = 0.0
    for i in range(1, len(points)):
        d = haversine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])
        cum_dist += d
        if cum_dist - last_sample_dist >= every_km * 1000:
            samples.append(points[i])
            last_sample_dist = cum_dist
    # aggiungi ultimo punto se non troppo vicino
    if haversine(samples[-1][0], samples[-1][1], points[-1][0], points[-1][1]) > 500:
        samples.append(points[-1])
    return samples


def query_wikipedia(lat, lon, radius=SEARCH_RADIUS_M):
    """Cerca articoli Wikipedia geolocalizzati nel raggio, con filtri."""
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius,
        "gslimit": 20,
        "format": "json",
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        raw_results = []
        for item in data.get("query", {}).get("geosearch", []):
            title = item["title"]
            # Filtro blacklist
            if _is_blacklisted(title):
                continue
            raw_results.append({
                "source": "wikipedia",
                "title": title,
                "lat": item["lat"],
                "lon": item["lon"],
                "dist_m": item["dist"],
                "pageid": item["pageid"],
            })

        # Filtro per dimensione pagina (batch query)
        if raw_results:
            pageids = [r["pageid"] for r in raw_results]
            time.sleep(RATE_LIMIT_S)
            sizes = _get_page_sizes(pageids)

            filtered = []
            for poi in raw_results:
                pid = poi["pageid"]
                size = sizes.get(pid, 0)
                poi["page_size"] = size
                if _is_whitelisted(poi["title"]):
                    filtered.append(poi)  # whitelist bypassa size filter
                elif size >= WIKI_MIN_PAGE_SIZE:
                    filtered.append(poi)
            return filtered

        return raw_results
    except Exception as e:
        print(f"    [WARN] Wikipedia error: {e}")
        return []


def query_overpass(lat, lon, radius=SEARCH_RADIUS_M):
    """Cerca POI storici/turistici via Overpass, con retry su 429."""
    query = OVERPASS_QUERY_TPL.format(lat=lat, lon=lon, radius=radius)
    for attempt in range(4):
        try:
            r = requests.post(OVERPASS_API, data={"data": query}, timeout=15)
            if r.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    [429] Overpass rate limit, aspetto {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            results = []
            seen = set()
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name", "")
                if not name or name in seen:
                    continue
                seen.add(name)

                # posizione
                if "center" in el:
                    plat, plon = el["center"]["lat"], el["center"]["lon"]
                else:
                    plat, plon = el.get("lat", lat), el.get("lon", lon)

                # tipo
                poi_type = (tags.get("historic") or tags.get("tourism")
                           or tags.get("building") or tags.get("heritage") or "poi")

                dist = haversine(lat, lon, plat, plon)
                results.append({
                    "source": "osm",
                    "title": name,
                    "type": poi_type,
                    "lat": plat,
                    "lon": plon,
                    "dist_m": round(dist, 1),
                })
            return results
        except Exception as e:
            print(f"    [WARN] Overpass error: {e}")
            return []
    return []  # tutti i retry falliti


def get_stage_number(filepath):
    stem = Path(filepath).stem
    import re
    m = re.match(r'tappa(\d+)', stem)
    return int(m.group(1)) if m else 0


def load_progress():
    """Carica risultati parziali se esistono."""
    if RESULT_FILE.exists():
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"stages": {}}


def save_progress(data):
    """Salva risultati (incrementale)."""
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    gpx_files = sorted(GPX_DIR.glob("tappa*.gpx"),
                       key=lambda f: get_stage_number(str(f)))

    if not gpx_files:
        print(f"Nessun GPX in {GPX_DIR}")
        sys.exit(1)

    data = load_progress()
    total_pois = 0
    total_queries = 0

    print(f"POI Discovery — {len(gpx_files)} tappe, campionamento ogni {SAMPLE_EVERY_KM}km")
    print(f"Raggio ricerca: {SEARCH_RADIUS_M}m")
    print(f"Output: {RESULT_FILE}")
    print()

    for gpx_file in gpx_files:
        num = get_stage_number(str(gpx_file))
        stage_key = f"tappa_{num:02d}"

        # Salta se già completata
        if stage_key in data["stages"] and data["stages"][stage_key].get("complete"):
            n = len(data["stages"][stage_key].get("pois", []))
            print(f"  {stage_key}: già completata ({n} POI) — skip")
            total_pois += n
            continue

        points = parse_gpx_points(str(gpx_file))
        samples = sample_points(points, SAMPLE_EVERY_KM)

        print(f"  {stage_key}: {len(points)} punti → {len(samples)} campioni ({SAMPLE_EVERY_KM}km)")

        all_pois = []
        seen_titles = set()

        for i, (lat, lon) in enumerate(samples):
            # Wikipedia
            wiki_results = query_wikipedia(lat, lon)
            time.sleep(RATE_LIMIT_S)
            total_queries += 1

            # Overpass
            osm_results = query_overpass(lat, lon)
            time.sleep(RATE_LIMIT_S)
            total_queries += 1

            # Deduplica per titolo
            for poi in wiki_results + osm_results:
                title = poi["title"]
                if title not in seen_titles:
                    seen_titles.add(title)
                    poi["sample_idx"] = i
                    poi["sample_km"] = round(i * SAMPLE_EVERY_KM, 1)
                    all_pois.append(poi)

            if (i + 1) % 5 == 0 or i == len(samples) - 1:
                print(f"    campione {i+1}/{len(samples)} — {len(all_pois)} POI unici fin qui")

        # Ordina per km
        all_pois.sort(key=lambda p: p.get("sample_km", 0))

        data["stages"][stage_key] = {
            "complete": True,
            "n_samples": len(samples),
            "n_pois": len(all_pois),
            "pois": all_pois,
        }

        save_progress(data)
        total_pois += len(all_pois)
        print(f"    → {len(all_pois)} POI trovati, salvato.\n")

    # Sommario finale
    print(f"\n{'='*60}")
    print(f"TOTALE: {total_pois} POI su {len(gpx_files)} tappe ({total_queries} API calls)")
    print(f"Output: {RESULT_FILE}")
    print(f"\nPOI per tappa:")
    for stage_key in sorted(data["stages"].keys()):
        s = data["stages"][stage_key]
        pois = s.get("pois", [])
        wiki_count = sum(1 for p in pois if p.get("source") == "wikipedia")
        osm_count = sum(1 for p in pois if p.get("source") == "osm")
        print(f"  {stage_key}: {len(pois):>3d} POI ({wiki_count} Wikipedia, {osm_count} OSM)")

    # Top POI per tappa (quelli più vicini al percorso)
    print(f"\n{'='*60}")
    print("HIGHLIGHTS per tappa:")
    for stage_key in sorted(data["stages"].keys()):
        pois = data["stages"][stage_key].get("pois", [])
        if not pois:
            continue
        # top 5 per vicinanza
        closest = sorted(pois, key=lambda p: p.get("dist_m", 9999))[:5]
        print(f"\n  {stage_key}:")
        for p in closest:
            src = "W" if p.get("source") == "wikipedia" else "O"
            km = p.get("sample_km", "?")
            print(f"    [{src}] km {km}: {p['title']} ({p['dist_m']}m)")

    print(f"\nDone!")


if __name__ == "__main__":
    main()

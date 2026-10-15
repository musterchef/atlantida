"""
DESNIVEL — Terrain Classification
==================================
Tre metodi per classificare il tipo di terreno (mare/pianura/collina/montagna)
a partire da lat, lon, ele. Ogni metodo ritorna un valore 0→1 continuo:

  0.00 = mare/costa
  0.33 = pianura
  0.66 = collina
  1.00 = montagna

Metodi:
  1. elevation_only   — solo soglie su elevazione (zero dipendenze esterne)
  2. coastline_dist   — elevazione + distanza dalla costa (shapely + pyshp)
  3. srtm_roughness   — rugosità locale da dati SRTM 90m (srtm.py)

Uso:
  from terrain_classify import classify_terrain
  values = classify_terrain(rows, method="coastline")
"""

import math
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════
#  METODO 1 — Solo elevazione (zero dipendenze)
# ═══════════════════════════════════════════════════════════

def _elevation_only(rows):
    """
    Classifica basata solo su ele (metri).
    Soglie calibrate per percorso Italia (Torino → Puglia):
      < 30m   → 0.0  (costa / mare)
      30-300m → 0.33 (pianura)
      300-800 → 0.66 (collina)
      > 800m  → 1.0  (montagna)
    Con transizioni smooth (interpolazione lineare nelle fasce di confine).
    """
    result = []
    for r in rows:
        ele = r.get("ele", 0.0)
        if ele < 15:
            v = 0.0
        elif ele < 50:
            # transizione costa → pianura
            v = _lerp(0.0, 0.33, (ele - 15) / 35)
        elif ele < 250:
            v = 0.33
        elif ele < 400:
            # transizione pianura → collina
            v = _lerp(0.33, 0.66, (ele - 250) / 150)
        elif ele < 700:
            v = 0.66
        elif ele < 900:
            # transizione collina → montagna
            v = _lerp(0.66, 1.0, (ele - 700) / 200)
        else:
            v = 1.0
        result.append(v)
    return result


# ═══════════════════════════════════════════════════════════
#  METODO 2 — Distanza dalla costa (shapely + pyshp)
# ═══════════════════════════════════════════════════════════

_coast_geom = None  # cache lazy

def _load_coastline():
    """Carica il shapefile Natural Earth 10m coastline (solo Italia/Mediterraneo)."""
    global _coast_geom
    if _coast_geom is not None:
        return _coast_geom

    import shapefile
    from shapely.geometry import MultiLineString, box
    from shapely.ops import unary_union
    from shapely import prepare

    shp_path = PROJECT_DIR / "data" / "coastline" / "ne_10m_coastline.shp"
    if not shp_path.exists():
        raise FileNotFoundError(
            f"Coastline shapefile non trovato: {shp_path}\n"
            "Scarica da: https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/"
        )

    # Bounding box Italia allargata (lon 6-19, lat 36-48)
    italy_bbox = box(6.0, 36.0, 19.0, 48.0)

    sf = shapefile.Reader(str(shp_path))
    lines = []
    for sr in sf.shapeRecords():
        geom_type = sr.shape.shapeTypeName
        coords = sr.shape.points
        if not coords:
            continue
        from shapely.geometry import LineString
        line = LineString(coords)
        if line.intersects(italy_bbox):
            clipped = line.intersection(italy_bbox)
            if not clipped.is_empty:
                lines.append(clipped)

    _coast_geom = unary_union(lines)
    prepare(_coast_geom)
    print(f"  Coastline caricata: {len(lines)} segmenti nell'area Italia")
    return _coast_geom


def _dist_to_coast_km(lat, lon):
    """Distanza approssimata in km dal punto alla costa più vicina."""
    from shapely.geometry import Point
    coast = _load_coastline()
    # In gradi, poi converti approssimativamente in km
    # A latitudine ~42° (centro Italia): 1° lon ≈ 82km, 1° lat ≈ 111km
    dist_deg = coast.distance(Point(lon, lat))
    # Approssimazione: media tra lon e lat scaling
    lat_rad = math.radians(lat)
    km_per_deg_lon = 111.32 * math.cos(lat_rad)
    km_per_deg_lat = 111.32
    km_approx = dist_deg * (km_per_deg_lon + km_per_deg_lat) / 2
    return km_approx


def _coastline_dist(rows):
    """
    Classifica combinando elevazione + distanza dalla costa.
    Più preciso del metodo 1: distingue pianura interna da zona costiera.
    """
    _load_coastline()  # preload

    result = []
    for i, r in enumerate(rows):
        ele = r.get("ele", 0.0)
        lat = r.get("lat", 0.0)
        lon = r.get("lon", 0.0)

        dist_km = _dist_to_coast_km(lat, lon)

        # Logica combinata
        if ele > 800:
            v = 1.0   # montagna sicura
        elif ele > 400:
            # collina, ma più vicino alla costa = un po' meno
            v = _lerp(0.55, 0.66, min(dist_km / 30, 1.0))
        elif ele > 200:
            v = _lerp(0.4, 0.55, min(dist_km / 40, 1.0))
        elif dist_km < 3 and ele < 50:
            v = 0.0   # costa
        elif dist_km < 8 and ele < 100:
            # zona costiera
            v = _lerp(0.0, 0.15, dist_km / 8)
        elif dist_km < 20:
            # fascia costiera/pianura
            v = _lerp(0.15, 0.33, (dist_km - 8) / 12)
        else:
            # pianura interna
            v = _lerp(0.33, 0.4, min((ele - 50) / 200, 1.0)) if ele > 50 else 0.33

        result.append(max(0.0, min(1.0, v)))

        if (i + 1) % 5000 == 0:
            print(f"    coastline: {i+1}/{len(rows)} punti...")

    return result


# ═══════════════════════════════════════════════════════════
#  METODO 3 — Rugosità SRTM (srtm.py)
# ═══════════════════════════════════════════════════════════

_srtm_data = None  # cache lazy

def _load_srtm():
    """Carica i dati SRTM (scarica tile al primo uso, ~20MB per Italia)."""
    global _srtm_data
    if _srtm_data is not None:
        return _srtm_data
    import srtm
    _srtm_data = srtm.get_data()
    print("  SRTM data caricati")
    return _srtm_data


def _srtm_roughness(rows, radius=3, step=0.003):
    """
    Campiona elevazioni SRTM in una griglia attorno al punto.
    Calcola varianza e media per determinare tipo di terreno.
    Ritorna valore continuo 0→1.

    radius: numero di campioni in ogni direzione (default 3 → griglia 7x7)
    step: passo in gradi (~330m a 0.003°)
    """
    elevation_data = _load_srtm()

    result = []
    for i, r in enumerate(rows):
        lat = r.get("lat", 0.0)
        lon = r.get("lon", 0.0)
        ele = r.get("ele", 0.0)

        # Campiona griglia attorno al punto
        samples = []
        for dlat in range(-radius, radius + 1):
            for dlon in range(-radius, radius + 1):
                e = elevation_data.get_elevation(lat + dlat * step, lon + dlon * step)
                if e is not None and e > -100:  # ignora valori invalidi
                    samples.append(e)

        if len(samples) < 4:
            # Fallback su metodo 1 se SRTM non disponibile
            if ele > 800:
                v = 1.0
            elif ele > 300:
                v = 0.66
            elif ele > 30:
                v = 0.33
            else:
                v = 0.0
            result.append(v)
            continue

        mean_ele = sum(samples) / len(samples)
        variance = sum((s - mean_ele) ** 2 for s in samples) / len(samples)
        roughness = math.sqrt(variance)  # deviazione standard

        # Classificazione basata su media + rugosità
        # Alta rugosità + alta quota = montagna
        # Bassa rugosità + bassa quota = pianura/costa
        # Alta rugosità + media quota = collina

        # Normalizza rugosità: 0-10m = piatto, >200m = molto mosso
        rough_norm = min(roughness / 200.0, 1.0)

        # Normalizza elevazione media: 0-1200m
        ele_norm = min(mean_ele / 1200.0, 1.0) if mean_ele > 0 else 0.0

        # Combina: peso 60% elevazione, 40% rugosità
        v = ele_norm * 0.6 + rough_norm * 0.4

        # Schiaccia in fasce più leggibili
        if v < 0.1:
            v = _lerp(0.0, 0.1, v / 0.1)
        elif v < 0.25:
            v = _lerp(0.1, 0.4, (v - 0.1) / 0.15)
        elif v < 0.5:
            v = _lerp(0.4, 0.7, (v - 0.25) / 0.25)
        else:
            v = _lerp(0.7, 1.0, min((v - 0.5) / 0.5, 1.0))

        result.append(max(0.0, min(1.0, v)))

        if (i + 1) % 2000 == 0:
            print(f"    srtm: {i+1}/{len(rows)} punti...")

    return result


# ═══════════════════════════════════════════════════════════
#  API PUBBLICA
# ═══════════════════════════════════════════════════════════

METHODS = {
    "elevation":  _elevation_only,
    "coastline":  _coastline_dist,
    "srtm":       _srtm_roughness,
}

def _lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def classify_terrain(rows, method="elevation"):
    """
    Classifica ogni punto in rows.

    Args:
        rows: lista di dict con almeno 'ele', 'lat', 'lon'
        method: "elevation" | "coastline" | "srtm"

    Returns:
        lista di float 0→1 (0=mare, 0.33=pianura, 0.66=collina, 1=montagna)
    """
    if method not in METHODS:
        raise ValueError(f"Metodo sconosciuto: {method}. Usa: {list(METHODS.keys())}")

    print(f"  Terrain classification: metodo '{method}' su {len(rows)} punti...")
    values = METHODS[method](rows)
    print(f"  Terrain done. Range: {min(values):.3f} → {max(values):.3f}")
    return values


def terrain_to_label(value):
    """Converte valore 0→1 in etichetta leggibile."""
    if value < 0.17:
        return "costa"
    elif value < 0.5:
        return "pianura"
    elif value < 0.83:
        return "collina"
    else:
        return "montagna"

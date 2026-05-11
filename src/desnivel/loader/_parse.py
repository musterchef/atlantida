"""Parsing minimale di file GPX 1.1 verso array numpy.

Solo stdlib (`xml.etree`, `datetime`). Estrae i campi essenziali:
``lat``, ``lon``, ``ele``, ``t_unix`` (in secondi). Se un trackpoint
non ha tempo o elevazione, vengono usati valori interpolabili
successivamente (NaN), oppure la riga viene scartata se mancano
le coordinate.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/1"}


def _parse_iso_utc(text: str) -> float:
    """Converte una timestamp ISO 8601 in secondi epoch UTC."""
    s = text.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def parse_gpx_points(path: str | Path) -> dict[str, np.ndarray]:
    """Legge un file GPX e ritorna gli array dei trackpoint.

    Returns:
        Dizionario con chiavi ``lat``, ``lon``, ``ele``, ``t_unix``,
        tutti ``float64`` della stessa lunghezza. ``ele`` può contenere
        zeri se il GPX non riporta elevazioni.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()

    lats: list[float] = []
    lons: list[float] = []
    eles: list[float] = []
    times: list[float] = []

    for trkpt in root.findall(".//gpx:trkpt", _GPX_NS):
        lat = trkpt.get("lat")
        lon = trkpt.get("lon")
        if lat is None or lon is None:
            continue
        ele_el = trkpt.find("gpx:ele", _GPX_NS)
        time_el = trkpt.find("gpx:time", _GPX_NS)
        lats.append(float(lat))
        lons.append(float(lon))
        eles.append(float(ele_el.text) if ele_el is not None and ele_el.text else 0.0)
        times.append(
            _parse_iso_utc(time_el.text) if time_el is not None and time_el.text else float("nan"),
        )

    if not lats:
        raise ValueError(f"Nessun trackpoint trovato in {path}")

    return {
        "lat": np.asarray(lats, dtype=float),
        "lon": np.asarray(lons, dtype=float),
        "ele": np.asarray(eles, dtype=float),
        "t_unix": np.asarray(times, dtype=float),
    }


def stage_id_from_path(path: str | Path) -> str:
    """Ricava lo `stage_id` dal nome file (es. ``tappa01_...gpx`` → ``tappa_01``).

    Convenzione: prefisso ``tappa<NN>_`` → ``tappa_<NN>``. Se il nome non
    matcha, ritorna lo stem così com'è.
    """
    stem = Path(path).stem
    head = stem.split("_", 1)[0]
    if head.startswith("tappa") and head[5:].isdigit():
        return f"tappa_{int(head[5:]):02d}"
    return stem

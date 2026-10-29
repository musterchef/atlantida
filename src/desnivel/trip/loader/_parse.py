"""Parsing minimale di file GPX 1.1 verso array numpy.

Solo stdlib (`xml.etree`, `datetime`). Estrae i campi essenziali:
``lat``, ``lon``, ``ele``, ``t_unix`` (in secondi). Se un trackpoint
non ha tempo o elevazione, il campo viene rappresentato come `NaN`;
la riga viene scartata se mancano le coordinate.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import re
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
        tutti ``float64`` della stessa lunghezza. ``ele`` contiene
        ``NaN`` se il GPX non riporta elevazione. Gli array interi
        ``source_index`` e ``segment_index`` conservano punto e segmento
        originali, numerati da 1; segmento 0 indica un punto fuori segmento.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()

    lats: list[float] = []
    lons: list[float] = []
    eles: list[float] = []
    times: list[float] = []
    source_indices: list[int] = []
    segment_indices: list[int] = []
    segments = {id(point): index for index, segment in enumerate(
        root.findall('.//gpx:trkseg', _GPX_NS), 1)
        for point in segment.findall('gpx:trkpt', _GPX_NS)}

    for source_index, trkpt in enumerate(root.findall(".//gpx:trkpt", _GPX_NS), 1):
        lat = trkpt.get("lat")
        lon = trkpt.get("lon")
        if lat is None or lon is None:
            continue
        ele_el = trkpt.find("gpx:ele", _GPX_NS)
        time_el = trkpt.find("gpx:time", _GPX_NS)
        lats.append(float(lat))
        lons.append(float(lon))
        eles.append(
            float(ele_el.text) if ele_el is not None and ele_el.text else float("nan"),
        )
        times.append(
            _parse_iso_utc(time_el.text) if time_el is not None and time_el.text else float("nan"),
        )
        source_indices.append(source_index)
        segment_indices.append(segments.get(id(trkpt), 0))

    if not lats:
        raise ValueError(f"Nessun trackpoint trovato in {path}")

    return {
        "lat": np.asarray(lats, dtype=float),
        "lon": np.asarray(lons, dtype=float),
        "ele": np.asarray(eles, dtype=float),
        "t_unix": np.asarray(times, dtype=float),
        "source_index": np.asarray(source_indices, dtype=int),
        "segment_index": np.asarray(segment_indices, dtype=int),
    }


def stage_id_from_path(path: str | Path) -> str:
    """Ricava lo `stage_id` dal nome file (es. ``tappa01_...gpx`` → ``tappa_01``).

    Convenzione: prefisso ``tappa<NN>_`` → ``tappa_<NN>``. Se il nome non
    matcha, ritorna lo stem così com'è.
    """
    stem = Path(path).stem
    match = re.search(r'(?:^|_)tappa_?(\d+)(?:_|$)', stem, re.IGNORECASE)
    if match:
        return f"tappa_{int(match[1]):02d}"
    return stem

"""Interpretazioni pesate del viaggio e sviluppo di una voce melodica."""
from __future__ import annotations

from itertools import groupby
import math

from desnivel.music import Pattern, PatternChange, SCALES
from desnivel.trip_metrics import MetricName


def compose(samples, config, weights):
    """Restituisce cambi riproducibili; nessuna dipendenza da device o rete.

    Finestre, filtro e scadenza dei dati sono espressi in secondi del viaggio.
    Una chiamata rappresenta un nuovo replay e riparte senza stato.
    """
    if set(weights) != {"movement", "effort"}:
        raise ValueError("pesi richiesti: movement, effort")
    if any(not math.isfinite(w) or w < 0 for w in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("pesi finiti, non negativi e somma positiva richiesti")
    for key in ("update_s", "smoothing_s", "stale_s", "speed_reference_kmh"):
        if not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"{key} deve essere finito e positivo")
    motif = config["motif_degrees"]
    order = config["gate_priority"]
    size = len(motif)
    if not size or any(type(d) is not int or d < 0 for d in motif):
        raise ValueError("motivo: gradi interi non negativi richiesti")
    if sorted(order) != list(range(size)):
        raise ValueError("gate_priority deve ordinare tutti gli indici del motivo una sola volta")
    lo, hi = config["gate_range"]
    if any(type(n) is not int for n in (lo, hi)) or not 0 <= lo <= hi <= size:
        raise ValueError("gate_range fuori dalla lunghezza del motivo")
    sections = config["sections"]
    starts = [s["from_progress"] for s in sections]
    if not starts or starts[0] != 0 or any(not math.isfinite(x) or not 0 <= x < 1 for x in starts) or any(a >= b for a, b in zip(starts, starts[1:])):
        raise ValueError("sezioni ordinate, dalla progressione 0 a meno di 1")
    for section in sections:
        if section["scale"] not in SCALES or type(section["root"]) is not int:
            raise ValueError("scala o tonica non valida")
    samples = sorted(samples, key=lambda s: s.elapsed_s)
    distances = [s.value for s in samples if s.name == MetricName.DISTANCE_TOTAL_M and math.isfinite(s.value)]
    if not distances or distances[-1] <= distances[0]:
        raise ValueError("distanza progressiva richiesta per le sezioni armoniche")
    origin, total = distances[0], distances[-1] - distances[0]
    filtered, timestamps, latest = {}, {}, {}
    previous = None
    previous_section = None
    next_update = 0.0
    changes = []
    for t, group in groupby(samples, key=lambda s: s.elapsed_s):
        for sample in group:
            if not math.isfinite(sample.value):
                continue
            latest[sample.name] = (sample.value, t)
            channel = {MetricName.SPEED_KMH: "movement", MetricName.EFFORT_ESTIMATE: "effort"}.get(sample.name)
            if channel:
                value = sample.value / config["speed_reference_kmh"] if channel == "movement" else sample.value
                value = min(1.0, max(0.0, value))
                dt = t - timestamps.get(channel, t)
                if channel not in filtered or dt > config["stale_s"]:
                    filtered[channel] = value
                else:
                    alpha = -math.expm1(-dt / config["smoothing_s"])
                    filtered[channel] += alpha * (value - filtered[channel])
                timestamps[channel] = t
        if t < next_update:
            continue
        active = [k for k, w in weights.items() if w > 0]
        # Non inventare dati: conserva il pattern finché tutti gli ingressi attivi sono validi.
        if any(k not in timestamps or t - timestamps[k] > config["stale_s"] for k in active):
            continue
        distance = latest.get(MetricName.DISTANCE_TOTAL_M)
        if distance is None or t - distance[1] > config["stale_s"]:
            continue
        next_update = t + config["update_s"]
        intensity = sum(filtered[k] * weights[k] for k in active) / sum(weights.values())
        count = int(math.floor(lo + (hi - lo) * intensity + 0.5))
        progress = min(1.0, max(0.0, (distance[0] - origin) / total))
        section = next(s for s in reversed(sections) if progress >= s["from_progress"])
        intervals = SCALES[section["scale"]]
        # Il motivo resta ancorato ai gradi della prima scala. Le sezioni successive
        # cambiano solo le posizioni dichiarate, preservando le altre note.
        base = SCALES[sections[0]["scale"]]
        degrees = section.get("degree_overrides", {})
        if any(not str(k).isdigit() or not 0 <= int(k) < size or type(v) is not int or v < 0 for k, v in degrees.items()):
            raise ValueError("degree_overrides: indice e grado non validi")
        notes = []
        for i, degree in enumerate(motif):
            pitch = base[degree % len(base)] + 12 * (degree // len(base))
            if str(i) in degrees:
                d = degrees[str(i)]
                pitch = intervals[d % len(intervals)] + 12 * (d // len(intervals))
            else:
                candidates = [x + 12 * octave for octave in range(pitch // 12 + 2) for x in intervals]
                pitch = min(candidates, key=lambda x: (abs(x - pitch), x))
            notes.append(section["root"] + pitch)
        opened = set(order[:count])
        pattern = Pattern(tuple(notes), tuple(int(i in opened) for i in range(size)))
        section_index = sections.index(section)
        if pattern != previous or section_index != previous_section:
            changes.append(PatternChange(t, f'{section["name"]} intensity={intensity:.2f}', pattern, section_index))
            previous = pattern
            previous_section = section_index
    return changes

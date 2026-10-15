"""
DESNIVEL — Weather data fetcher (v2: frame-aligned)
=====================================================
Recupera dati meteo storici a 15-min da Open-Meteo Historical Forecast API,
poi interpola frame-per-frame sulla stessa timeline di tappa_XX.csv.

Output per tappa:
  - weather_tappa_XX.csv  → stessi frame/td_time del CSV principale
  - weather_summary.json  → sommario globale

Ogni riga del weather CSV corrisponde esattamente alla stessa riga
del tappa CSV: frame 0 ↔ frame 0, frame 5394 ↔ frame 5394.
In TD basta caricare entrambi i Table DAT e leggere la stessa riga.

Nessuna API key necessaria.

Uso:
  python src/weather_fetch.py
"""

import xml.etree.ElementTree as ET
import requests
import csv
import json
import os
import time as time_mod
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────── CONFIG ────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
GPX_DIR     = PROJECT_DIR / "gpx"
OUT_DIR     = PROJECT_DIR / "output"

# Historical Forecast API: risoluzione fino a 15 min
FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

MINUTELY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "pressure_msl",
    "visibility",
    "is_day",
]

# Campi interpolabili (numerici continui)
LERP_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_gusts_10m",
    "pressure_msl",
    "visibility",
]

# Campi discreti (nearest-neighbor)
NEAREST_FIELDS = [
    "weather_code",
    "wind_direction_10m",
    "is_day",
]

NS = {"gpx": "http://www.topografix.com/GPX/1/1"}

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}
# ────────────────────────────────────────────────


def parse_gpx_times(filepath):
    """Estrae tutti i timestamp e coordinate dal GPX."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    points = []
    for trkpt in root.findall(".//gpx:trkpt", NS):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        time_el = trkpt.find("gpx:time", NS)
        t = datetime.strptime(time_el.text, "%Y-%m-%dT%H:%M:%SZ") if time_el is not None else None
        points.append({"lat": lat, "lon": lon, "time": t})
    return points


def fetch_weather_15min(lat, lon, date_str):
    """Chiama Open-Meteo Historical Forecast per dati a 15 min."""
    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "start_date": date_str,
        "end_date": date_str,
        "minutely_15": ",".join(MINUTELY_VARS),
        "timezone": "UTC",
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_weather_timeseries(data):
    """Converte risposta API in lista di (timestamp_s, {valori})."""
    m15 = data.get("minutely_15", {})
    times = m15.get("time", [])
    series = []
    for i, t_str in enumerate(times):
        dt = datetime.strptime(t_str, "%Y-%m-%dT%H:%M")
        vals = {}
        for var in MINUTELY_VARS:
            vals[var] = m15[var][i] if var in m15 and i < len(m15[var]) else None
        series.append({"dt": dt, "ts": dt.timestamp(), "vals": vals})
    return series


def _norm(val, vmin, vmax):
    """Normalizza a range 0-1."""
    if val is None:
        return 0.0
    return max(0.0, min(1.0, (val - vmin) / (vmax - vmin)))


def lerp(a, b, t):
    """Interpolazione lineare, gestisce None."""
    if a is None or b is None:
        return a if a is not None else b
    return a + (b - a) * t


def interpolate_weather_at(weather_series, target_ts, search_start=0):
    """
    Interpola i valori meteo al timestamp target_ts.
    Ritorna (dict_valori, nuovo_search_start).
    """
    n = len(weather_series)
    # Avanza l'indice di ricerca
    j = search_start
    while j < n - 2 and weather_series[j + 1]["ts"] < target_ts:
        j += 1

    a = weather_series[j]
    b = weather_series[min(j + 1, n - 1)]

    span = b["ts"] - a["ts"]
    frac = (target_ts - a["ts"]) / span if span > 0 else 0.0
    frac = max(0.0, min(1.0, frac))

    result = {}

    # Interpolazione lineare per campi continui
    for f in LERP_FIELDS:
        result[f] = lerp(a["vals"].get(f), b["vals"].get(f), frac)
        if result[f] is not None:
            result[f] = round(result[f], 2)

    # Nearest-neighbor per campi discreti
    nearest = a if frac < 0.5 else b
    for f in NEAREST_FIELDS:
        result[f] = nearest["vals"].get(f)

    return result, j


def read_tappa_frames(tappa_num):
    """Legge il CSV della tappa e ritorna n_frames e td_time_max."""
    csv_path = OUT_DIR / f"tappa_{tappa_num:02d}.csv"
    if not csv_path.exists():
        return None
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return None
    return {
        "n_frames": len(rows),
        "td_time_max": float(rows[-1]["td_time"]),
    }


def build_weather_frames(gpx_points, weather_series, n_frames):
    """
    Costruisce n_frames righe meteo interpolate.
    Ogni frame è mappato al suo tempo reale nel GPX → meteo a quel momento.
    """
    start_ts = gpx_points[0]["time"].timestamp()
    end_ts = gpx_points[-1]["time"].timestamp()
    real_duration = end_ts - start_ts
    if real_duration <= 0:
        real_duration = 1.0

    # td_time per ogni frame (come nel pipeline principale)
    td_time_max = (n_frames - 1) / 30.0 if n_frames > 1 else 0.0

    frames = []
    search_j = 0

    for frame_i in range(n_frames):
        # Progresso normalizzato del frame
        progress = frame_i / (n_frames - 1) if n_frames > 1 else 0.0

        # Tempo reale corrispondente
        real_ts = start_ts + progress * real_duration
        td_time = frame_i / 30.0

        # Interpola meteo
        vals, search_j = interpolate_weather_at(weather_series, real_ts, search_j)

        # Descrizione WMO
        wc = vals.get("weather_code")
        weather_desc = WMO_WEATHER_CODES.get(int(wc), "") if wc is not None else ""

        # Normalizzazioni TD
        row = {
            "frame": frame_i,
            "td_time": round(td_time, 6),
            "td_time_norm": round(progress, 6),
            # Raw
            "temperature_2m": vals["temperature_2m"],
            "apparent_temperature": vals["apparent_temperature"],
            "relative_humidity_2m": vals["relative_humidity_2m"],
            "precipitation": vals["precipitation"],
            "rain": vals["rain"],
            "weather_code": vals["weather_code"],
            "weather_desc": weather_desc,
            "cloud_cover": vals["cloud_cover"],
            "cloud_cover_low": vals["cloud_cover_low"],
            "cloud_cover_mid": vals["cloud_cover_mid"],
            "cloud_cover_high": vals["cloud_cover_high"],
            "wind_speed_10m": vals["wind_speed_10m"],
            "wind_direction_10m": vals["wind_direction_10m"],
            "wind_gusts_10m": vals["wind_gusts_10m"],
            "pressure_msl": vals["pressure_msl"],
            "visibility": vals["visibility"],
            "is_day": vals["is_day"],
            # Normalizzati 0-1
            "temperature_norm": round(_norm(vals["temperature_2m"], -10, 45), 4),
            "humidity_norm": round((vals["relative_humidity_2m"] or 0) / 100.0, 4),
            "cloud_norm": round((vals["cloud_cover"] or 0) / 100.0, 4),
            "cloud_low_norm": round((vals["cloud_cover_low"] or 0) / 100.0, 4),
            "cloud_mid_norm": round((vals["cloud_cover_mid"] or 0) / 100.0, 4),
            "cloud_high_norm": round((vals["cloud_cover_high"] or 0) / 100.0, 4),
            "wind_norm": round(_norm(vals["wind_speed_10m"], 0, 100), 4),
            "wind_dir_norm": round((vals["wind_direction_10m"] or 0) / 360.0, 4),
            "wind_gust_norm": round(_norm(vals["wind_gusts_10m"], 0, 120), 4),
            "precip_norm": round(_norm(vals["precipitation"], 0, 50), 4),
            "pressure_norm": round(_norm(vals["pressure_msl"], 970, 1050), 4),
            "visibility_norm": round(_norm(vals["visibility"], 0, 50000), 4),
        }
        frames.append(row)

    return frames


def save_weather_csv(rows, filepath):
    """Salva righe meteo in CSV."""
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {}
            for k in fieldnames:
                v = r.get(k, "")
                if isinstance(v, float):
                    out[k] = round(v, 6)
                else:
                    out[k] = v
            w.writerow(out)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    gpx_files = sorted(GPX_DIR.glob("tappa*.gpx"))

    if not gpx_files:
        print("Nessun file GPX tappa trovato in", GPX_DIR)
        return

    summary = []

    for i, gpx_path in enumerate(gpx_files, 1):
        tappa_num = i
        num_str = f"{i:02d}"
        print(f"\n{'='*60}")
        print(f"TAPPA {num_str}: {gpx_path.name}")
        print(f"{'='*60}")

        # Leggi n_frames dal CSV della tappa
        tappa_info = read_tappa_frames(tappa_num)
        if tappa_info is None:
            print(f"  ! CSV tappa_{num_str}.csv non trovato, skip.")
            continue

        n_frames = tappa_info["n_frames"]
        print(f"  Frames tappa: {n_frames}")

        # Parsa GPX
        gpx_points = parse_gpx_times(str(gpx_path))
        if not gpx_points or gpx_points[0]["time"] is None:
            print("  ! Nessun punto con timestamp, skip.")
            continue

        start_time = gpx_points[0]["time"]
        end_time = gpx_points[-1]["time"]
        date_str = start_time.strftime("%Y-%m-%d")
        real_dur = (end_time - start_time).total_seconds()

        # Punto medio per coordinate meteo
        mid = gpx_points[len(gpx_points) // 2]
        print(f"  Data:    {date_str}")
        print(f"  Ora:     {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} UTC ({real_dur/3600:.1f}h)")
        print(f"  Centro:  {mid['lat']:.4f}, {mid['lon']:.4f}")

        # Fetch meteo a 15 min
        print(f"  Fetching meteo 15-min da Open-Meteo...")
        try:
            data = fetch_weather_15min(mid["lat"], mid["lon"], date_str)
        except requests.RequestException as e:
            print(f"  X Errore API: {e}")
            continue

        weather_series = parse_weather_timeseries(data)
        if not weather_series:
            print("  X Nessun dato meteo ricevuto.")
            continue

        print(f"  Dati meteo: {len(weather_series)} campioni a 15-min")

        # Interpola su tutti i frame
        frames = build_weather_frames(gpx_points, weather_series, n_frames)

        out_path = OUT_DIR / f"weather_tappa_{num_str}.csv"
        save_weather_csv(frames, out_path)
        print(f"  -> Salvato: {out_path.name} ({len(frames)} frame)")

        # Stampa sommario rapido percepito durante la pedalata
        temps  = [r["temperature_2m"] for r in frames if r["temperature_2m"] is not None]
        app_temps = [r["apparent_temperature"] for r in frames if r["apparent_temperature"] is not None]
        winds  = [r["wind_speed_10m"] for r in frames if r["wind_speed_10m"] is not None]
        gusts  = [r["wind_gusts_10m"] for r in frames if r["wind_gusts_10m"] is not None]
        rain   = max((r["precipitation"] for r in frames if r["precipitation"] is not None), default=0)
        clouds = [r["cloud_cover"] for r in frames if r["cloud_cover"] is not None]
        descs  = set(r["weather_desc"] for r in frames if r["weather_desc"])
        vis    = [r["visibility"] for r in frames if r["visibility"] is not None]

        if temps:
            print(f"  Temp:       {min(temps):.1f} - {max(temps):.1f} C")
        if app_temps:
            print(f"  Percepita:  {min(app_temps):.1f} - {max(app_temps):.1f} C")
        if winds:
            print(f"  Vento:      {min(winds):.0f} - {max(winds):.0f} km/h (raffiche: {max(gusts):.0f})")
        total_precip = sum(r["precipitation"] or 0 for r in frames) / max(1, n_frames) * (real_dur / 900)
        print(f"  Pioggia:    ~{total_precip:.1f} mm")
        if clouds:
            print(f"  Nuvole:     {min(clouds):.0f} - {max(clouds):.0f}%")
        if vis:
            print(f"  Visibilita: {min(vis)/1000:.0f} - {max(vis)/1000:.0f} km")
        if descs:
            print(f"  Condizioni: {', '.join(sorted(descs))}")

        # Sommario per JSON
        stage_info = {
            "tappa": i,
            "date": date_str,
            "lat": round(mid["lat"], 4),
            "lon": round(mid["lon"], 4),
            "csv_file": f"weather_tappa_{num_str}.csv",
            "n_frames": len(frames),
            "matches_tappa_csv": f"tappa_{num_str}.csv",
            "temp_min_c": round(min(temps), 1) if temps else None,
            "temp_max_c": round(max(temps), 1) if temps else None,
            "apparent_temp_min_c": round(min(app_temps), 1) if app_temps else None,
            "apparent_temp_max_c": round(max(app_temps), 1) if app_temps else None,
            "wind_max_kmh": round(max(winds), 1) if winds else None,
            "gust_max_kmh": round(max(gusts), 1) if gusts else None,
            "total_rain_mm": round(total_precip, 1),
            "cloud_avg_pct": round(sum(clouds) / len(clouds), 1) if clouds else None,
            "conditions": sorted(descs),
        }
        summary.append(stage_info)

        # Rate limiting rispettoso
        time_mod.sleep(0.5)

    # Salva sommario globale JSON
    summary_path = OUT_DIR / "weather_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "project": "DESNIVEL",
            "description": "Dati meteo storici 15-min interpolati frame-per-frame (Open-Meteo Historical Forecast)",
            "source": "https://open-meteo.com/",
            "note": "Ogni weather CSV ha lo stesso numero di frame del tappa CSV. frame 0 = frame 0.",
            "n_stages": len(summary),
            "stages": summary,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Sommario meteo salvato: {summary_path.name}")
    print(f"Tappe elaborate: {len(summary)}")
    print("Done!")


if __name__ == "__main__":
    main()

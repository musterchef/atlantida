"""
DESNIVEL — Generate Sonic Visualization Index
==============================================
Crea un indice HTML per navigare i plot sonori di tutte le tappe.

Uso:
    .venv/bin/python generate_sonic_index.py
    # → output/viz/index.html
"""

import json
from pathlib import Path
from datetime import datetime


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
VIZ_DIR = OUTPUT_DIR / "viz"


def load_summary():
    """Carica il summary JSON con metadati delle tappe."""
    path = OUTPUT_DIR / "desnivel_summary.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def generate_index():
    """Genera index.html per la visualizzazione."""
    summary = load_summary()
    stages = summary.get("stages", [])

    html = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DESNIVEL — Sonic Timeline Visualization</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            padding: 40px 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
        }
        h1 {
            font-size: 48px;
            background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }
        .subtitle {
            font-size: 16px;
            color: #aaa;
            margin-top: 15px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .card:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(124, 58, 237, 0.5);
            transform: translateY(-5px);
        }
        .card img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            display: block;
        }
        .card-info {
            padding: 20px;
        }
        .card-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }
        .card-meta {
            font-size: 13px;
            color: #aaa;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        .meta-item {
            padding: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
        }
        .meta-label {
            color: #00d4ff;
            font-weight: 600;
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 3px;
        }
        .meta-value {
            color: #e0e0e0;
            font-size: 14px;
        }
        a {
            color: #00d4ff;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }
        a:hover {
            color: #7c3aed;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #666;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-box {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stat-label {
            color: #aaa;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 DESNIVEL</h1>
            <div class="subtitle">
                <strong>Sonic Timeline Visualization</strong><br>
                Ogni curva, ogni pendenza si trasforma in suono e immagine
            </div>
        </header>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Tappe visualizzate</div>
                <div class="stat-value">12</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Distanza totale</div>
                <div class="stat-value">1,183 km</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Dislivello positivo</div>
                <div class="stat-value">12,104 m</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Durata totale</div>
                <div class="stat-value">96 h</div>
            </div>
        </div>
        
        <h2 style="margin-bottom: 30px; font-size: 28px;">Timeline sonore</h2>
        <div class="grid">
"""
    
    for stage in stages:
        num = stage["tappa"]
        name = stage["name"]
        duration_h = stage["real_duration_h"]
        dist_km = stage["total_dist_km"]
        ele_gain = stage["ele_gain_m"]
        sonic_file = stage.get("sonic_file")
        
        if not sonic_file:
            continue
        
        # Check if PNG exists
        png_file = f"tappa_{num:02d}_sonic.png"
        png_path = VIZ_DIR / png_file
        
        if not png_path.exists():
            continue
        
        # Extract stage location from name
        parts = name.split("_")
        stage_name = " → ".join(parts[-2:]) if len(parts) >= 2 else name
        
        html += f"""        <div class="card">
            <img src="{png_file}" alt="Tappa {num:02d}">
            <div class="card-info">
                <div class="card-title">Tappa {num:02d}</div>
                <div style="font-size: 13px; color: #00d4ff; margin-bottom: 12px;">
                    {stage_name}
                </div>
                <div class="card-meta">
                    <div class="meta-item">
                        <span class="meta-label">Durata reale</span>
                        <span class="meta-value">{duration_h:.1f} h</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Distanza</span>
                        <span class="meta-value">{dist_km:.0f} km</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Dislivello +</span>
                        <span class="meta-value">{ele_gain:.0f} m</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Frames sonori</span>
                        <span class="meta-value">{stage.get("n_output_frames", 0):,}</span>
                    </div>
                </div>
                <a href="{png_file}" target="_blank">Visualizza plot completo →</a>
            </div>
        </div>
"""
    
    html += """        </div>
        
        <div class="footer">
            <p><strong>Leggenda visiva:</strong></p>
            <p style="margin-top: 10px; font-size: 13px;">
                <strong>Row 1:</strong> Pitch in MIDI (con colore scala armonica: cyan=major, yellow=pentatonic, orange=dorian, purple=phrygian)<br>
                <strong>Row 2:</strong> BPM (pulsazione corpo)<br>
                <strong>Row 3:</strong> Drive (sforzo), Reverb (flow), Volume, e Cutoff (apertura)<br>
                <strong>Row 4:</strong> Density ritmica (curvatura della strada)<br>
                <strong>Background:</strong> Temperatura colore (alba→tramonto)<br>
            </p>
            <p style="margin-top: 20px; color: #666;">
                Generato il: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    html = generate_index()
    
    index_path = VIZ_DIR / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✓ Indice generato: {index_path}")
    print(f"  Apri nel browser: file://{index_path.absolute()}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

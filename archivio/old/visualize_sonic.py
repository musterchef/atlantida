"""
DESNIVEL — Sonic Timeline Visualization
=========================================
Plotta la narrazione sonora di una tappa: pitch, BPM, drive, reverb, scale,
terrain, ecc. Perfetto per validare il mapping audio e capire come il viaggio
si trasforma in suono.

Uso:
    .venv/bin/python visualize_sonic.py tappa_01
    .venv/bin/python visualize_sonic.py tappa_01 --show
    .venv/bin/python visualize_sonic.py tappa_03 --output /tmp/viz.png

Genera:
    output/viz/tappa_NN_sonic.png
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, List
import argparse

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection
    import numpy as np
except ImportError:
    print("Error: matplotlib e numpy richiesti.")
    print("  pip install matplotlib numpy")
    sys.exit(1)


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
VIZ_DIR = OUTPUT_DIR / "viz"


def load_sonic_json(tappa_num: int) -> list[dict]:
    """Carica tappa_NN_sonic.json."""
    path = OUTPUT_DIR / f"tappa_{tappa_num:02d}_sonic.json"
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scale_color(scale: str) -> tuple[float, float, float]:
    """Scale name → RGB color."""
    colors = {
        "major":            (0.2, 0.8, 1.0),     # cyan
        "pentatonic_major": (1.0, 0.9, 0.1),     # yellow
        "dorian":           (1.0, 0.5, 0.2),     # orange
        "phrygian":         (0.6, 0.2, 0.8),     # purple
    }
    return colors.get(scale, (0.5, 0.5, 0.5))


def voice_marker(voice: str) -> str:
    """Voice name → matplotlib marker."""
    markers = {
        "drone_water":    "o",
        "pad_plain":      "s",
        "pluck_hill":     "^",
        "brass_mountain": "D",
    }
    return markers.get(voice, ".")


def plot_sonic_timeline(rows: list[dict], tappa_num: int,
                        figsize=(16, 10)) -> None:
    """Plotta la timeline sonora con subplots coordinati."""
    if not rows:
        print("No data to plot.")
        return

    t_arr = np.array([r["t"] for r in rows])
    t_norm = np.array([r["t_norm"] for r in rows])
    pitch_arr = np.array([r["pitch"] for r in rows])
    bpm_arr = np.array([r["bpm"] for r in rows])
    drive_arr = np.array([r["drive"] for r in rows])
    reverb_arr = np.array([r["reverb"] for r in rows])
    volume_arr = np.array([r["volume"] for r in rows])
    density_arr = np.array([r["density"] for r in rows])
    cutoff_arr = np.array([r["cutoff"] for r in rows])
    scale_arr = [r["scale"] for r in rows]
    voice_arr = [r["voice"] for r in rows]
    color_temp = np.array([r["color_temp"] for r in rows])

    # Mappa scale → colore per ogni frame
    scale_colors = np.array([scale_color(s) for s in scale_arr])

    fig, axes = plt.subplots(4, 1, figsize=figsize, sharex=True)
    fig.suptitle(f"DESNIVEL — Tappa {tappa_num:02d} — Sonic Timeline",
                 fontsize=16, fontweight="bold", y=0.995)

    # ─── Row 0: Pitch (con colore scala) ───────────────────────────────────
    ax = axes[0]
    for i in range(len(rows) - 1):
        ax.plot(t_arr[i:i+2], pitch_arr[i:i+2],
                color=scale_colors[i], linewidth=1.5, alpha=0.8)
    # Scatter dei voice marker
    for voice in set(voice_arr):
        mask = np.array([v == voice for v in voice_arr])
        marker = voice_marker(voice)
        ax.scatter(t_arr[mask], pitch_arr[mask], marker=marker, s=30,
                  alpha=0.4, label=voice, edgecolors="black", linewidth=0.5)
    ax.set_ylabel("Pitch (MIDI)", fontsize=11, fontweight="bold")
    ax.set_ylim(30, 90)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=8, ncol=4)

    # ─── Row 1: BPM (pulsazione) ──────────────────────────────────────────
    ax = axes[1]
    ax.fill_between(t_arr, bpm_arr, alpha=0.3, color="steelblue", label="BPM")
    ax.plot(t_arr, bpm_arr, color="steelblue", linewidth=1.5)
    ax.axhline(y=90, color="gray", linestyle=":", alpha=0.5, label="ref 90 BPM")
    ax.set_ylabel("BPM", fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=9)

    # ─── Row 2: Drive, Reverb, Volume (modulazioni dinamiche) ─────────────
    ax = axes[2]
    ax.plot(t_arr, drive_arr, color="red", linewidth=1.5, label="Drive (sforzo)",
            alpha=0.8)
    ax.plot(t_arr, reverb_arr, color="blue", linewidth=1.5, label="Reverb (flow)",
            alpha=0.8)
    ax.plot(t_arr, volume_arr, color="green", linewidth=1.5, label="Volume",
            alpha=0.8)
    ax.fill_between(t_arr, 0, cutoff_arr * 0.5, alpha=0.1, color="orange",
                    label="Cutoff (alt)")
    ax.set_ylabel("Amp. [0, 1]", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.05, 1.1)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=9, ncol=2)

    # ─── Row 3: Density (ritmica) + Terrain (background hatch) ────────────
    ax = axes[3]
    ax.fill_between(t_arr, density_arr, alpha=0.5, color="mediumvioletred",
                    label="Density (curve)")
    ax.plot(t_arr, density_arr, color="darkviolet", linewidth=1.5)
    ax.set_ylabel("Density [0, 1]", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.05, 1.1)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper left", fontsize=9)

    # ─── Asse X condiviso ──────────────────────────────────────────────────
    ax.set_xlabel("Time (seconds)", fontsize=11, fontweight="bold")
    ax.set_xlim(t_arr[0], t_arr[-1])

    # ─── Background color progression: color_temp (alba→tramonto) ──────────
    for ax_idx, ax in enumerate(axes):
        # Overlay a colore di fondo per rappresentare tempo del giorno
        for i in range(len(rows) - 1):
            ct = color_temp[i]  # 0 = cold (notte), 1 = warm (tramonto)
            # Colore interpolato: blue (notte) → red (tramonto)
            bg_color = (ct, 0.5, 1 - ct)  # R=temp, G=0.5, B=1-temp
            ax.axvspan(t_arr[i], t_arr[i+1], alpha=0.02, color=bg_color)

    # Layout
    plt.tight_layout()
    return fig, axes


def main():
    parser = argparse.ArgumentParser(
        description="Visualizza la timeline sonora di una tappa Desnivel."
    )
    parser.add_argument("tappa", type=str,
                        help="Nome tappa (es. tappa_01 o 01 o 1)")
    parser.add_argument("--output", type=str, default=None,
                        help="Cartella output (default: output/viz/)")
    parser.add_argument("--show", action="store_true",
                        help="Mostra il plot invece di salvare (plt.show())")
    parser.add_argument("--dpi", type=int, default=150,
                        help="DPI per salvataggio PNG")
    args = parser.parse_args()

    # Parse tappa number
    tappa_str = args.tappa.replace("tappa_", "").replace("tappa", "")
    try:
        tappa_num = int(tappa_str)
    except ValueError:
        print(f"Error: tappa '{args.tappa}' non valida. Usa: 1, tappa_01, tappa01")
        sys.exit(1)

    print(f"Carico tappa {tappa_num:02d}...")
    rows = load_sonic_json(tappa_num)
    print(f"  {len(rows)} frame caricati")

    print(f"Plotto timeline sonora...")
    fig, axes = plot_sonic_timeline(rows, tappa_num)

    if args.show:
        print("  mostrando plot...")
        plt.show()
    else:
        # Salva PNG
        VIZ_DIR.mkdir(parents=True, exist_ok=True)
        output_path = args.output
        if output_path is None:
            output_path = VIZ_DIR / f"tappa_{tappa_num:02d}_sonic.png"
        else:
            output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.savefig(str(output_path), dpi=args.dpi, bbox_inches="tight")
        print(f"  salvato: {output_path}")
        print(f"  size: {output_path.stat().st_size / 1024:.1f} KB")

    plt.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

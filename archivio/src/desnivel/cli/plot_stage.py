"""CLI: plotta i canali di modulazione di una tappa.

Legge ``output/<stage>_modulations.csv`` prodotto da ``FileSink`` e
disegna un grafico con un subplot per canale, condividendo l'asse del
tempo. Opzionalmente sovrappone gli eventi letti da
``output/<stage>_events.json`` come linee verticali colorate per
categoria.

Strumento di ispezione, non di produzione: serve a vedere a colpo
d'occhio se i modulatori si comportano come ci aspettiamo.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


# Import "lazy" di matplotlib: l'utility non deve impattare l'import del
# pacchetto se matplotlib non è installato.
def _import_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover - dipende dall'ambiente
        raise SystemExit(
            "matplotlib non è installato. Installa con: pip install matplotlib",
        ) from exc
    return plt


# ── Caricamento dati ───────────────────────────────────────────────────


def _load_modulations(csv_path: Path) -> tuple[list[float], dict[str, list[float]]]:
    """Legge il CSV prodotto da ``ModulationFrame.to_csv``."""
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header[0] != "t":
            raise ValueError(f"CSV inatteso: prima colonna è '{header[0]}', attesa 't'")
        channel_names = header[1:]
        t: list[float] = []
        channels: dict[str, list[float]] = {name: [] for name in channel_names}
        for row in reader:
            t.append(float(row[0]))
            for name, value in zip(channel_names, row[1:]):
                channels[name].append(float(value))
    return t, channels


def _load_events(json_path: Path) -> list[dict]:
    """Legge il JSON degli eventi se esiste. Ritorna lista vuota altrimenti.

    Accetta sia il formato di ``FileSink`` (``{"stage_id": ..., "events": [...]}``)
    sia una lista nuda di eventi.
    """
    if not json_path.exists():
        return []
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return list(data.get("events", []))
    return list(data)


# ── Plotting ───────────────────────────────────────────────────────────


_CATEGORY_COLORS = {
    "major": "#d6336c",
    "minor": "#1c7ed6",
}


def _plot(
    stage_id: str,
    t: list[float],
    channels: dict[str, list[float]],
    events: list[dict],
    output: Path | None,
) -> None:
    plt = _import_matplotlib()
    n = len(channels)
    if n == 0:
        raise SystemExit("Nessun canale trovato nel CSV.")

    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(12, 1.8 * n + 0.5))
    if n == 1:
        axes = [axes]

    # Tempo in minuti: più leggibile per tappe da 30+ minuti.
    t_min = [v / 60.0 for v in t]

    for ax, (name, values) in zip(axes, channels.items()):
        ax.plot(t_min, values, linewidth=0.9)
        ax.set_ylabel(name, fontsize=9)
        ax.grid(True, alpha=0.25)
        _overlay_events(ax, events)

    axes[-1].set_xlabel("tempo (min)")
    fig.suptitle(f"DESNIVEL — {stage_id}", fontsize=11)
    fig.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=120)
        print(f"[plot_stage] salvato in {output}")
    else:
        plt.show()


def _overlay_events(ax, events: list[dict]) -> None:
    """Aggiunge linee verticali per gli eventi sul subplot dato."""
    for e in events:
        t_min = float(e["t"]) / 60.0
        color = _CATEGORY_COLORS.get(e.get("category", ""), "#888888")
        ax.axvline(t_min, color=color, alpha=0.35, linewidth=0.8)


# ── CLI ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plot_stage",
        description="Plotta i canali di modulazione di una tappa.",
    )
    parser.add_argument("--stage", required=True, help="Stage id, es. tappa_01.")
    parser.add_argument(
        "--output-dir", default="output", type=Path,
        help="Cartella dove FileSink ha scritto i CSV/JSON.",
    )
    parser.add_argument(
        "--save", type=Path, default=None,
        help="Se passato, salva il PNG invece di aprire la finestra.",
    )
    args = parser.parse_args(argv)

    csv_path = args.output_dir / f"{args.stage}_modulations.csv"
    json_path = args.output_dir / f"{args.stage}_events.json"
    if not csv_path.exists():
        raise SystemExit(f"File non trovato: {csv_path}. Lancia prima run_stage.")

    t, channels = _load_modulations(csv_path)
    events = _load_events(json_path)
    _plot(args.stage, t, channels, events, args.save)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

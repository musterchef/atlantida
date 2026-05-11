"""Sink che scrive le modulazioni in CSV e gli eventi in JSON."""
from __future__ import annotations

import json
from pathlib import Path

from ..events import Event
from ..modulation import ModulationFrame


class FileSink:
    """Scrive in ``<output_dir>/<stage>_modulations.csv`` e
    ``<output_dir>/<stage>_events.json``.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def emit(self, stage_id: str, frame: ModulationFrame,
             events: list[Event]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = self.output_dir / f"{stage_id}_modulations.csv"
        json_path = self.output_dir / f"{stage_id}_events.json"

        frame.to_csv(csv_path)

        payload = {
            "stage_id": stage_id,
            "events": [e.to_dict() for e in events],
        }
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

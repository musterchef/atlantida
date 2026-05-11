"""Entry point del loader GPX."""
from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_CONFIG, Config
from ..track import Track
from ._derive import derive_channels
from ._parse import parse_gpx_points, stage_id_from_path
from ._resample import resample_to_uniform_grid


def load_track(
    gpx_path: str | Path,
    config: Config = DEFAULT_CONFIG,
    stage_id: str | None = None,
) -> Track:
    """Carica un file GPX e produce un `Track` ricampionato.

    Pipeline interna (tutta pura, testabile a pezzi):

    1. ``parse_gpx_points`` legge il file in array numpy grezzi.
    2. ``derive_channels`` calcola velocità, pendenza, sforzo, ecc.
    3. ``resample_to_uniform_grid`` porta tutto sulla griglia uniforme
       di ``config.timing.internal_rate_hz``.

    Args:
        gpx_path: percorso al file ``.gpx``.
        config: configurazione (legge ``timing`` e ``gpx``).
        stage_id: identificatore tappa; se ``None`` viene dedotto dal nome file.

    Returns:
        `Track` con asse temporale uniforme e samples derivati.
    """
    gpx_path = Path(gpx_path)
    raw = parse_gpx_points(gpx_path)
    derived = derive_channels(raw, config.gpx)

    elapsed = derived.pop("elapsed_s")
    t, samples = resample_to_uniform_grid(
        elapsed_s=elapsed,
        channels=derived,
        rate_hz=config.timing.internal_rate_hz,
    )

    return Track(
        stage_id=stage_id or stage_id_from_path(gpx_path),
        t=t,
        samples=samples,
        metadata={"source_path": str(gpx_path)},
    )

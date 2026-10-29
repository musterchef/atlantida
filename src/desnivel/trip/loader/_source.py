"""Selezione esplicita del lettore in base al formato della sorgente."""
from pathlib import Path

from ._parse import parse_gpx_points


def read_source(path):
    """Restituisce campioni originali e metadati, senza filtri o ricampionamento."""
    path = Path(path)
    if path.suffix.lower() == '.gpx':
        return parse_gpx_points(path), {'format': 'gpx'}
    if path.suffix.lower() == '.fit':
        from ._fit import parse_fit
        return parse_fit(path)
    raise ValueError(f'formato del viaggio non supportato: {path.suffix}; usare .fit o .gpx')

"""Collega analisi e famiglie del percorso alle sezioni musicali configurate."""
from copy import deepcopy
import json
from pathlib import Path

from desnivel.trip.analysis import analyze_track
from desnivel.trip.sections import group_zones


def load_trip_sections(track, path):
    """Prepara le sezioni per il Director esistente, una volta all'avvio.

    I percorsi di analisi e raggruppamento sono relativi al JSON di direzione.
    I modelli musicali vengono copiati integralmente per ogni macrosezione.
    """
    path = Path(path)
    definition = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(definition, dict) or set(definition) != {'analysis', 'grouping', 'families'}:
        raise ValueError('la direzione del viaggio richiede analysis, grouping e families')
    for key in ('analysis', 'grouping'):
        if not isinstance(definition[key], str) or not definition[key]:
            raise ValueError(f'{key} deve indicare un file JSON')
    analysis_config = json.loads((path.parent/definition['analysis']).read_text(encoding='utf-8'))
    grouping_config = json.loads((path.parent/definition['grouping']).read_text(encoding='utf-8'))
    analysis = analyze_track(track, analysis_config)
    grouping = group_zones(analysis, grouping_config)
    arrangements = definition['families']
    if not isinstance(arrangements, dict) or set(arrangements) != set(grouping_config['families']):
        raise ValueError('ogni famiglia configurata richiede un assetto musicale, senza famiglie aggiuntive')
    for family, arrangement in arrangements.items():
        if not isinstance(arrangement, dict) or set(arrangement) != {'root', 'scale', 'assignments'}:
            raise ValueError(f'{family}: richiesti root, scale e assignments')
        if not isinstance(arrangement['assignments'], dict):
            raise ValueError(f'{family}: assignments deve contenere le assegnazioni delle voci')
    return [{**deepcopy(arrangements[section['kind']]),
             'name': section['kind'], 'from_progress': section['from_progress'],
             'trip': deepcopy(section)}
            for section in grouping['sections']]

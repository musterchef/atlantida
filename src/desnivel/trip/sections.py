"""Macrosezioni del percorso ricavate da famiglie configurate di zone contigue."""
from copy import deepcopy
import math


def measure_section_bridges(sections, *, flank_kind, middle_kind):
    """Misura sezioni intermedie tra due sezioni della famiglia richiesta.

    Legge le macrosezioni originali senza raggrupparle né applicare soglie.
    """
    if (not isinstance(flank_kind, str) or not flank_kind
            or not isinstance(middle_kind, str) or not middle_kind or flank_kind == middle_kind):
        raise ValueError('due famiglie distinte con nomi non vuoti richieste')
    lengths = [s['end_distance_m']-s['start_distance_m'] for s in sections]
    if any(not math.isfinite(length) or length <= 0 for length in lengths):
        raise ValueError('lunghezze delle macrosezioni positive e finite richieste')
    candidates = []
    for i in range(1, len(sections)-1):
        if (sections[i]['kind'] != middle_kind or sections[i-1]['kind'] != flank_kind
                or sections[i+1]['kind'] != flank_kind):
            continue
        before, middle, after = lengths[i-1:i+2]
        # Forma equivalente a 2ab/(a+b), senza il prodotto delle lunghezze.
        lower, upper = min(before, after), max(before, after)
        reference = lower/(.5+.5*(lower/upper))
        ratio = middle/reference
        if not math.isfinite(reference) or not math.isfinite(ratio):
            raise ValueError('riferimento locale o rapporto non rappresentabile')
        candidates.append({'before_index': sections[i-1]['index'],
                           'middle_index': sections[i]['index'],
                           'after_index': sections[i+1]['index'],
                           'before_distance_m': before, 'middle_distance_m': middle,
                           'after_distance_m': after, 'reference_distance_m': reference,
                           'distance_ratio': ratio})
    return {'flank_kind': flank_kind, 'middle_kind': middle_kind, 'candidates': candidates}


def group_zones(analysis: dict, config: dict) -> dict:
    """Raggruppa le zone consecutive senza modificarne rilevamento o confini.

    Ogni fascia dell'analisi deve appartenere esattamente a una famiglia.
    Le zone figlie restano rintracciabili tramite i loro indici originali.
    """
    if not isinstance(config, dict) or set(config) != {'families'}:
        raise ValueError('la configurazione delle macrosezioni richiede families')
    families = config['families']
    if not isinstance(families, dict) or not families:
        raise ValueError('families deve contenere almeno una famiglia')
    membership = {}
    for family, kinds in families.items():
        if not isinstance(family, str) or not family or not isinstance(kinds, list) or not kinds:
            raise ValueError('ogni famiglia richiede un nome non vuoto e una lista di fasce')
        for kind in kinds:
            if not isinstance(kind, str) or not kind:
                raise ValueError('nomi delle fasce non vuoti richiesti')
            if kind in membership:
                raise ValueError(f'fascia assegnata più volte: {kind}')
            membership[kind] = family
    available = {band['name'] for band in analysis['config']['bands']}
    if set(membership) != available:
        missing, unknown = available - membership.keys(), membership.keys() - available
        raise ValueError(f'fasce senza famiglia: {sorted(missing)}; fasce sconosciute: {sorted(unknown)}')

    sections = []
    for zone in analysis['zones']:
        family = membership[zone['kind']]
        if (sections and sections[-1]['kind'] == family
                and sections[-1]['end_distance_m'] == zone['start_distance_m']):
            section = sections[-1]
            section['end_distance_m'] = zone['end_distance_m']
            section['zone_indices'].append(zone['index'])
            section['elevation_delta_m'] += zone['elevation_delta_m']
        else:
            sections.append({'index': len(sections), 'kind': family,
                             'start_distance_m': zone['start_distance_m'],
                             'end_distance_m': zone['end_distance_m'],
                             'zone_indices': [zone['index']],
                             'elevation_delta_m': zone['elevation_delta_m']})
    for section in sections:
        start, end = section['start_distance_m'], section['end_distance_m']
        section['from_progress'] = start / analysis['total_distance_m']
        section['until_progress'] = end / analysis['total_distance_m']
        section['mean_slope_ratio'] = section['elevation_delta_m'] / (end-start)
    return {'config': deepcopy(config), 'sections': sections}

"""Integrità dei dati fra analisi, esportazione JSON e report HTML."""
import json
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pytest

from desnivel.reports.trip import render_trip_report
from desnivel.trip.analysis import analyze_track
from desnivel.trip.track import Track


class EmbeddedAnalysis(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.in_data = False
        self.payload = ''
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.in_data = tag == 'script' and dict(attrs).get('id') == 'analysis-data'

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_data = False

    def handle_data(self, data):
        if self.in_data:
            self.payload += data


def test_arbitrary_names_are_preserved_as_data_and_cannot_close_script():
    name = '</script><img src=x onerror=alert(1)>'
    config = {'sample_distance_m': 100, 'slope_window_m': 200,
              'min_zone_distance_m': 100,
              'bands': [{'name': name, 'from_slope_ratio': None}]}
    track = Track(name, np.array([0., 1.]),
                  {'cum_dist_m': np.array([0., 200.]), 'ele': np.array([100., 110.])})
    analysis = analyze_track(track, config)
    html = render_trip_report(analysis)
    assert json.loads(EmbeddedAnalysis(html).payload) == analysis
    assert name not in html
    assert '<script src=' not in html and '<link ' not in html
    assert '/* REPORT_SCRIPT */' not in html and '/* REPORT_STYLE */' not in html


def test_profile_preserves_endpoints_and_midpoints_in_distance_coordinates():
    config = {'sample_distance_m': 100, 'slope_window_m': 100,
              'min_zone_distance_m': 100,
              'bands': [{'name': 'any', 'from_slope_ratio': None}]}
    track = Track('profile', np.array([0., 1.]),
                  {'cum_dist_m': np.array([50., 175.]), 'ele': np.array([100., 105.])})
    profile = analyze_track(track, config)['profile']
    assert [p['distance_m'] for p in profile] == [0, 50, 100, 112.5, 125]
    assert [p['elevation_m'] for p in profile] == pytest.approx([100, 102, 104, 104.5, 105])


@pytest.mark.parametrize('with_grouping', [False, True])
def test_cli_embeds_exactly_the_exported_analysis(tmp_path, with_grouping):
    from desnivel.cli.analyze_trip import main

    root = Path(__file__).resolve().parents[2]
    output, report = tmp_path/'nested/analysis.json', tmp_path/'nested/report.html'
    args = ['--gpx', str(root/'gpx/tappa05_Firenze_San_Gimignano.gpx'),
            '--config', str(root/'presets/analisi-percorso.json'),
            '--output', str(output), '--html', str(report)]
    if with_grouping:
        args += ['--grouping', str(root/'presets/macrosezioni-percorso.json')]
    assert main(args) == 0
    result = json.loads(output.read_text())
    assert json.loads(EmbeddedAnalysis(report.read_text()).payload) == result
    if with_grouping:
        assert len(result['grouping']['sections']) < len(result['zones'])
        grouped = result
        assert main(args[:-2]) == 0
        assert {key: value for key, value in grouped.items() if key != 'grouping'} == json.loads(output.read_text())


def test_cli_rejects_colliding_output_paths_before_writing(tmp_path):
    from desnivel.cli.analyze_trip import main

    output = tmp_path/'same'
    with pytest.raises(SystemExit):
        main(['--gpx', 'unused.gpx', '--config', 'unused.json',
              '--output', str(output), '--html', str(output)])
    assert not output.exists()


def test_report_requires_profile_instead_of_inventing_elevation():
    with pytest.raises(ValueError):
        render_trip_report({'version': 1})

from dataclasses import asdict

import pytest

from desnivel.music.bass.analysis import recommend_bass
from desnivel.music.patterns import Pattern, PatternChange


def change(t, opened):
    return PatternChange(t, 'test', Pattern((60,) * 4, (1,) * opened + (0,) * (4 - opened)))


def test_recommendation_weights_duration_not_number_of_updates():
    report = recommend_bass([change(0, 1), change(90, 4)], 100)
    split = recommend_bass([change(0, 1), change(30, 1), change(60, 1), change(90, 4)], 100)
    assert report == split
    assert report.mean_gate_fraction == pytest.approx(.325)
    assert report.analyzed_seconds == 100


def test_busier_melody_leaves_more_space_and_variability_changes_variation():
    sparse = recommend_bass([change(0, 1)], 100)
    dense = recommend_bass([change(0, 4)], 100)
    varying = recommend_bass([change(0, 1), change(50, 4)], 100)
    assert dense.settings.density < sparse.settings.density
    assert dense.settings.articulation < sparse.settings.articulation
    assert dense.settings.syncopation < sparse.settings.syncopation
    assert varying.settings.variation > sparse.settings.variation
    assert dense.settings.lowest == sparse.settings.lowest == 28
    assert dense.settings.highest == sparse.settings.highest == 47
    assert varying.settings.mobility == sparse.settings.mobility


def test_initial_wait_is_not_treated_as_melodic_silence():
    report = recommend_bass([change(10, 2)], 100)
    assert report.analyzed_seconds == 90
    assert report.mean_gate_fraction == .5
    assert recommend_bass([change(0, 2), change(100, 4)], 100).mean_gate_fraction == .5


@pytest.mark.parametrize('changes,end', [([], 100), ([change(0, 2)], float('nan')),
    ([change(100, 2)], 100), ([change(10, 2), change(5, 3)], 100),
    ([change(0, 2), change(0, 3)], 100), ([change(-1, 2)], 100)])
def test_invalid_timeline_is_rejected(changes, end):
    with pytest.raises(ValueError):
        recommend_bass(changes, end)


def test_manual_cli_prints_a_valid_bass_command_without_network(monkeypatch, tmp_path, capsys):
    import shlex
    from desnivel.cli import analyze_bass
    from desnivel.cli.bass_options import add_bass_options, bass_settings
    from desnivel.trip.metrics import MetricSample, MetricName
    import argparse
    config = tmp_path / 'stage.json'
    config.write_text('{}')
    weights = tmp_path / 'weights.json'
    weights.write_text('{}')
    monkeypatch.setattr(analyze_bass, 'load_track', lambda path: None)
    monkeypatch.setattr(analyze_bass, 'build_metric_samples', lambda track: (
        MetricSample(100, MetricName.DISTANCE_TOTAL_M, 1000),))
    monkeypatch.setattr(analyze_bass, 'compose', lambda *args: [change(0, 2)])
    assert analyze_bass.main(['--gpx', 'test.gpx', '--stage-music', str(config),
                              '--preset', str(weights)]) == 0
    output = capsys.readouterr().out
    command = shlex.split(output.splitlines()[-1])
    parser = argparse.ArgumentParser()
    add_bass_options(parser)
    settings = bass_settings(parser.parse_args(command[1:]))
    assert asdict(settings) == asdict(recommend_bass([change(0, 2)], 100).settings)
    assert 'nessun comando inviato' in output

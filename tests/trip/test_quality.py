import json

import numpy as np
import pytest

from desnivel.trip.loader._parse import parse_gpx_points
from desnivel.trip.quality import inspect_source


def source(lat, times, *, segments=None):
    n = len(lat)
    return {'lat': np.array(lat), 'lon': np.zeros(n), 'ele': np.full(n, np.nan),
            't_unix': np.array(times), 'source_index': np.arange(1, n+1),
            'segment_index': np.array(segments if segments is not None else [1]*n)}


def test_large_jump_is_exposed_with_original_times_coordinates_and_neighbors():
    raw = source([45., 45.00001, 45.005, 45.00002], [0., 1., 2., 3.])
    original = {key: value.copy() for key, value in raw.items()}
    result = inspect_source(raw, top_count=1)
    fastest = result['fastest_intervals'][0]
    assert fastest['start']['source_index'] == 2
    assert fastest['end']['source_index'] == 3
    assert fastest['duration_s'] == 1
    assert fastest['distance_m'] == pytest.approx(554.86, abs=.1)
    assert fastest['speed_kmh'] == pytest.approx(1997.49, abs=.1)
    assert fastest['start']['time_utc'] == '1970-01-01T00:00:01+00:00'
    assert fastest['end']['lat'] == 45.005
    assert len(fastest['neighbors']) == 4
    for key in raw:
        np.testing.assert_equal(raw[key], original[key])
    json.dumps(result, allow_nan=False)


def test_missing_and_non_increasing_times_never_produce_a_speed():
    result = inspect_source(source([45.]*5, [0., np.nan, 2., 2., 1.]))
    assert result['missing_time_points'] == 1
    assert result['unavailable_reasons']['missing_time'] == 2
    assert result['unavailable_reasons']['non_increasing_time'] == 2
    assert result['available_speed_intervals'] == 0
    assert result['speed_median_kmh'] is None
    assert result['fastest_intervals'] == []
    json.dumps(result, allow_nan=False)


def test_segment_boundary_and_skipped_points_are_not_interpreted_as_motion():
    raw = source([45., 45.001, 46., 46.001], [0., 60., 61., 121.], segments=[1, 1, 2, 2])
    raw['source_index'][-1] = 5
    result = inspect_source(raw)
    assert result['segments'] == 2
    assert result['unavailable_reasons']['segment_boundary'] == 1
    assert result['unavailable_reasons']['skipped_point'] == 1
    assert result['available_speed_intervals'] == 1
    assert len(result['fastest_intervals']) == 1


def test_zero_speed_is_available_but_invalid_coordinates_are_not():
    result = inspect_source(source([45., 45., 100.], [0., 1., 2.]))
    assert result['speed_median_kmh'] == 0
    assert result['fastest_intervals'][0]['speed_kmh'] == 0
    assert result['invalid_coordinate_points'] == 1
    assert result['unavailable_reasons']['invalid_coordinates'] == 1
    single = inspect_source(source([45.], [0.]))
    assert single['available_speed_intervals'] == 0
    json.dumps(single, allow_nan=False)


def test_parser_preserves_source_indices_even_when_a_point_is_skipped(tmp_path):
    path = tmp_path/'source.gpx'
    path.write_text('''<gpx xmlns="http://www.topografix.com/GPX/1/1"><trk>
      <trkseg><trkpt lat="45" lon="7"/><trkpt lon="7"/><trkpt lat="45.1" lon="7"/></trkseg>
      <trkseg><trkpt lat="46" lon="8"/></trkseg></trk></gpx>''')
    raw = parse_gpx_points(path)
    assert raw['source_index'].tolist() == [1, 3, 4]
    assert raw['segment_index'].tolist() == [1, 1, 2]
    assert np.isnan(raw['t_unix']).all()


def test_a_real_stop_without_a_jump_is_not_flagged_as_signal_loss():
    result = inspect_source(source([45.]*5, [0., 10., 20., 30., 60.]))
    assert result['review_segments'] == []


def test_review_finds_a_resume_after_stationary_coordinates_without_claiming_a_tunnel():
    result = inspect_source(source([45., 45., 45., 45., 45.001], [0., 10., 20., 30., 40.]))
    segment, = result['review_segments']
    assert segment['id'] == 'p4-5'
    assert segment['reasons'] == ['resume_after_stationary_coordinates']
    assert segment['peak_speed_kmh'] < 70
    assert segment['context_start']['source_index'] == 1
    assert 'tunnel' not in segment


def test_moving_sampling_gaps_are_reviewed_even_with_plausible_average_speed():
    result = inspect_source(source([45., 45.002], [0., 120.]))
    segment, = result['review_segments']
    assert segment['reasons'] == ['moving_sampling_gap']
    assert segment['peak_speed_kmh'] < 70


def test_review_grouping_uses_time_and_keeps_track_segments_separate():
    raw = source([45., 45.005, 45.0051, 45.010], [0., 1., 20., 21.])
    result = inspect_source(raw)
    assert len(result['review_segments']) == 1
    assert result['review_segments'][0]['flagged_interval_count'] == 2
    raw['segment_index'][2:] = 2
    result = inspect_source(raw)
    assert len(result['review_segments']) > 1

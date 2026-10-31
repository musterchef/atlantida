import json
from dataclasses import replace
from pathlib import Path

import pytest

from desnivel.cli.generators import build_generator
from desnivel.music.coordinator import PlanningRequest
from desnivel.music.percussion.styles import STYLE_BY_ID, style_events
from desnivel.music.phrases import Note, Phrase


def definition():
    return json.loads(Path('presets/dialogo.json').read_text())['generators']['percussion']


def request(start=0, length=4, silent=False, **parameters):
    foreground = Phrase(length, () if silent else tuple(Note(i, 60, .1, 90) for i in range(0, length, 4)))
    return PlanningRequest(start, length, None, {'voice_01': foreground, 'voice_02': Phrase(length, ())},
                           'percussion', parameters, start)


def compose(generator, req):
    prepared = generator.prepare_reference(req)
    result = generator.stage(replace(req, rhythm=prepared.reference, prepared_material=prepared.material))
    generator.accept(result)
    return result


def events(phrase, offset=0):
    return [(round(n.beat+offset, 8), n.pitch, n.velocity) for n in phrase.notes]


def test_none_preserves_existing_material_and_profiles_need_explicit_mapping():
    a, b = build_generator(definition()).generator.generate, build_generator(definition()).generator.generate
    for start in range(0, 64, 4):
        assert compose(a, request(start)).phrase == compose(b, request(start, style='none')).phrase
    spec = definition()
    del spec['style_lanes']
    g = build_generator(spec)
    with pytest.raises(ValueError, match='style_lanes'):
        g.generator.validate('percussion', {'style': 'house_classic'})
    assert g.describe_controls('percussion', {})['style']['inactive_reason']
    with pytest.raises(ValueError, match='sconosciuto'):
        a.validate('percussion', {'style': 'unknown'})


@pytest.mark.parametrize('style', STYLE_BY_ID)
@pytest.mark.parametrize('amount', [0, .5, 1])
def test_identity_survives_silent_sources_and_full_transformations(style, amount):
    spec = definition()
    spec['development'] = ['statement', 'subtract', 'displace', 'accent']
    spec['settings']['variation'] = 1
    gen = build_generator(spec).generator.generate
    for start in range(0, 32, 4):
        result = compose(gen, request(start, silent=True, style=style, conceptuality=amount, velocity_ratio=1))
        cores = [(round(b-start, 8), p, v) for b, p, v, core in
                 style_events(STYLE_BY_ID[style], gen.style_lanes, start, start+4, 7) if core]
        assert all(event in events(result.phrase) for event in cores)
        assert result.decision['style_weights'] == {style: 1}


@pytest.mark.parametrize('style', STYLE_BY_ID)
@pytest.mark.parametrize('amount', [0, .5, 1])
def test_phase_and_swing_are_independent_of_window_partition(style, amount):
    spec = definition()
    spec['development'] = ['statement', 'displace']
    # Isola fase e sviluppo: il filtro interattivo legge soltanto le note
    # della finestra corrente, non gli attacchi della finestra futura.
    spec['settings']['answer_clearance_beats'] = 0
    full, split = build_generator(spec).generator.generate, build_generator(spec).generator.generate
    whole = compose(full, request(length=16, style=style, conceptuality=amount)).phrase
    pieces = [compose(split, request(start, style=style, conceptuality=amount)).phrase for start in range(0, 16, 4)]
    assert events(whole) == [event for i, part in enumerate(pieces) for event in events(part, 4*i)]
    guide = full.prepare_reference(request(length=16, style=style)).reference
    sliced = [split.prepare_reference(request(start, style=style)).reference for start in range(0, 16, 4)]
    assert [(round(b, 8), w) for b, w in guide.points] == [(round(4*i+b, 8), w) for i, part in enumerate(sliced) for b, w in part.points]
    if STYLE_BY_ID[style].swing_delay:
        assert any(round(n.beat % 1, 2) == round(.5+STYLE_BY_ID[style].swing_delay, 2)
                   for n in compose(split, request(16, style=style, conceptuality=0)).phrase.notes)


def test_styles_are_distinct_and_guide_contains_the_selected_structural_rhythm():
    signatures = []
    for style in STYLE_BY_ID:
        gen = build_generator(definition()).generator.generate
        req = request(style=style, conceptuality=0, velocity_ratio=1)
        prepared = gen.prepare_reference(req)
        result = compose(gen, req)
        signatures.append(events(result.phrase))
        assert all((beat, pitch, velocity) in events(result.phrase) for beat, pitch, velocity in prepared.material)
        assert all(beat in dict(prepared.reference.points) for beat, _, _ in prepared.material)
    assert all(a != b for i, a in enumerate(signatures) for b in signatures[i+1:])


def test_switch_keeps_position_and_other_controls_and_silence_is_explicit():
    gen = build_generator(definition()).generator.generate
    compose(gen, request(style='house_classic'))
    plan = compose(gen, request(4, style='boom_bap_90s', variation=.25, conceptuality=.7))
    assert gen.position == 8 and plan.decision['logical_start'] == 4
    assert gen.settings['variation'] == .7 and gen.settings['conceptuality'] == 1
    spec = definition()
    spec['development'] = ['statement', 'silence']
    gen = build_generator(spec).generator.generate
    assert not compose(gen, request(8, style='house_classic', conceptuality=1)).phrase.notes
    assert compose(gen, request(12, style='house_classic', conceptuality=0)).phrase.notes


def test_profiles_have_finite_consistent_events_without_unintended_duplicates():
    for style in STYLE_BY_ID.values():
        assert len(style.variants) >= 2
        for variant in style.variants:
            assert len({(h.beat, h.role) for h in variant}) == len(variant)
            assert all(0 <= h.beat < style.cycle_beats and 1 <= h.velocity <= 127 for h in variant)

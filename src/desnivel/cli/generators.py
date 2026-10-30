"""Registro esplicito dei generatori e dei controlli esposti nella sessione."""
from dataclasses import asdict, dataclass

from desnivel.adapters.voice_device import Control
from desnivel.cli.ensemble import Generator
from desnivel.music.melodic.generator import MotifGenerator, ROLES
from desnivel.music.bass.voice import BassVoice
from desnivel.music.percussion.generator import PercussionGenerator, ROLES as PERCUSSION_ROLES
from desnivel.music.percussion.development import PercussionPhraseGenerator
from desnivel.music.texture.generator import TextureGenerator, ROLES as TEXTURE_ROLES


@dataclass
class RegisteredGenerator:
    generator: Generator
    controls: dict
    values: dict
    presets: dict
    reset: object = None
    describe_controls: object = None


def build_generator(spec):
    kind = spec['type']
    if kind == 'motif':
        compose = MotifGenerator(spec['degrees'], spec.get('settings'))
        controls = {'octave': Control(-5, 5, True), 'step_beats': Control(.25, 8),
                    'articulation': Control(.05, 1), 'velocity': Control(1, 127, True),
                    'development': Control(0, 1), 'activity': Control(0, 1),
                    'phrase_windows': Control(2, 8, True), 'seed': Control(0, 2147483647, True)}
        roles = ROLES
        values = compose.settings
    elif kind == 'responsive_line':
        compose = BassVoice(spec.get('settings'))
        controls = {'density': Control(0, 4), 'syncopation': Control(0, 1),
                    'rhythm_follow': Control(0, 1), 'melody_follow': Control(0, 1),
                    'mobility': Control(0, 1), 'variation': Control(0, 1),
                    'articulation': Control(.05, 1)}
        roles = ('bass_line',)
        values = asdict(compose.settings)
    elif kind == 'sustained_texture':
        compose = TextureGenerator(spec.get('degree', 0), spec.get('settings'))
        controls = {'octave': Control(-5, 5, True), 'velocity': Control(1, 127, True),
                    'follow_source': Control(0, 1, True, toggle=True)}
        roles = TEXTURE_ROLES
        values = compose.settings
    elif kind == 'percussion_phrase':
        compose = PercussionPhraseGenerator(spec['lanes'], spec['material'], spec['anchor_beats'],
                                           spec['development'], spec['interaction'], spec.get('settings'),
                                           standard_material=spec.get('standard_material'))
        controls = {'conceptuality': Control(0, 1), 'variation': Control(0, 1), 'displacement_beats': Control(0, 1),
                    'velocity_ratio': Control(.05, 1), 'gate_beats': Control(.01, 1),
                    'seed': Control(0, 2147483647, True), 'support_tolerance_beats': Control(0, 1),
                    'answer_clearance_beats': Control(0, 1)}
        roles = PERCUSSION_ROLES
        values = compose.settings
    elif kind == 'percussion_pattern':
        compose = PercussionGenerator(spec['lanes'], spec['patterns'], spec.get('settings'))
        controls = {'pattern': Control(0, len(compose.patterns)-1, True),
                    'velocity_ratio': Control(.05, 1), 'gate_beats': Control(.01, 1)}
        roles = PERCUSSION_ROLES
        values = compose.settings
    else:
        raise ValueError(f'tipo di generatore sconosciuto: {kind}')
    initial = {name: values[name] for name in controls}
    presets = {name: {**initial, **parameters} for name, parameters in spec.get('presets', {}).items()}
    for values in [initial, *presets.values()]:
        if set(values) != set(controls):
            raise ValueError('preset con controlli sconosciuti')
        for name, value in values.items():
            controls[name].validate(value)
        for role in roles:
            compose.validate(role, values)
    def validate(role, parameters):
        compose.validate(role, parameters)
        for name, control in controls.items():
            if name in parameters:
                control.validate(parameters[name])
    describe = (lambda: compose.last_decision) if kind in ('motif', 'sustained_texture', 'percussion_pattern', 'percussion_phrase') else None
    return RegisteredGenerator(Generator(compose, roles, validate, describe), controls,
                               initial, presets, getattr(compose, 'reset', None),
                               getattr(compose, 'describe_controls', None))

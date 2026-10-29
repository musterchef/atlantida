"""Libreria JSON dei preset compositivi creati dall'utente, separata dai preset base."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile


class VoicePresetLibrary:
    def __init__(self, path):
        self.path = Path(path)
        data = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {'version': 1, 'voices': {}}
        if (not isinstance(data, dict) or set(data) != {'version', 'voices'}
                or data['version'] != 1 or not isinstance(data['voices'], dict)
                or any(not isinstance(presets, dict) for presets in data['voices'].values())):
            raise ValueError('libreria dei preset voce versione 1 non valida')
        self.voices = data['voices']

    def save(self, voice, name, values, overwrite=False):
        candidate = deepcopy(self.voices)
        presets = candidate.setdefault(voice, {})
        if (name in presets) != overwrite:
            raise ValueError('preset già presente: usare Aggiorna' if name in presets else 'preset da aggiornare non presente')
        presets[name] = dict(values)
        payload = json.dumps({'version': 1, 'voices': candidate}, ensure_ascii=False, allow_nan=False, indent=2)+'\n'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                         prefix=self.path.name+'.', delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(payload)
                stream.close()
                temporary.replace(self.path)
            finally:
                temporary.unlink(missing_ok=True)
        self.voices = candidate

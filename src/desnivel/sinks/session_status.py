"""Scrittura atomica dello stato globale della sessione, separata dall'esecuzione."""
import json
from pathlib import Path
import tempfile


class SessionStatusStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, state):
        payload = json.dumps(state, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                         prefix=self.path.name+'.', delete=False) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(self.path)

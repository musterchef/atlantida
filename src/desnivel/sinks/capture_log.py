"""Archivio versionato delle acquisizioni; indipendente da OSC e Snake."""
from datetime import datetime, timezone
import json
import time
from typing import Any, Protocol, TextIO
from uuid import uuid4

SCHEMA_VERSION = 1


class CaptureStore(Protocol):
    def append(self, address: str, payload: Any, *, raw_args=None, error=None) -> None: ...
    def finish(self, reason: str) -> None: ...


class JsonlCaptureStore:
    """Una sessione per file, eventi append-only e chiusura esplicita.

    Il chiamante possiede lo stream. Flush per riga, senza fsync: i dati
    arrivano al sistema operativo ma non sono garantiti contro perdita di corrente.
    """
    def __init__(self, stream: TextIO, metadata: dict, *, clock=time.monotonic_ns):
        self.stream = stream
        self.clock = clock
        self.started_ns = clock()
        self.session_id = str(uuid4())
        self.count = 0
        self.closed = False
        self._write('session', {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata,
        })

    def _write(self, kind, fields):
        record = {'schema_version': SCHEMA_VERSION, 'record_type': kind,
                  'session_id': self.session_id, **fields}
        line = json.dumps(record, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        self.stream.write(line + '\n')
        self.stream.flush()

    def append(self, address, payload, *, raw_args=None, error=None):
        if self.closed:
            raise ValueError('acquisizione già chiusa')
        self._write('event', {
            'event_id': self.count + 1,
            'elapsed_ns': self.clock() - self.started_ns,
            'address': address,
            'payload': payload,
            'raw_args': raw_args,
            'decode_error': error,
        })
        self.count += 1

    def finish(self, reason):
        if self.closed:
            return
        self._write('end', {'elapsed_ns': self.clock() - self.started_ns,
                            'event_count': self.count, 'reason': reason})
        self.closed = True

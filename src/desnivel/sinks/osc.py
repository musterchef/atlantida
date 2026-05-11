"""Sink OSC: invia in tempo reale modulazioni continue ed eventi.

Architettura modulare in tre strati:

1. **Costruzione della schedule** (`build_schedule`): funzione pura che
   trasforma `ModulationFrame` + lista eventi in una sequenza ordinata
   di `ScheduledMessage`. Niente IO, niente rete: completamente
   testabile.

2. **Client OSC** (`OscClient` Protocol + `UdpOscClient`): astrazione
   sottile su `python_osc.udp_client.SimpleUDPClient`. Permette di
   iniettare un `FakeOscClient` nei test.

3. **Orchestrazione** (`OscSink`): consuma la schedule e gestisce il
   timing wall-clock con `time.monotonic()`, applicando `speed` per
   playback accelerato.

Conversione nomi: i canali in `ModulationFrame` sono `journey_phase`,
`meso_tension`, ecc.; gli address OSC del contratto sono
`/mod/journey/phase`, `/mod/meso/tension`. La prima parte determina
il **gruppo** (`journey`, `macro`, `meso`, `body`, `micro`) che a sua
volta determina la **frequenza di invio** (`config.osc.rates_hz`).

Gli eventi diventano `/event/major/<kind>` o `/event/minor/<kind>`,
con un singolo argomento JSON che porta `t` e `payload` (compatto e
direttamente leggibile lato TouchDesigner/Max).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, runtime_checkable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..modulation import ModulationFrame


# ──────────────────── Schedule (funzione pura) ─────────────────────


@dataclass(frozen=True)
class ScheduledMessage:
    """Un messaggio OSC pianificato a un istante `t` della tappa.

    Attributes:
        t: tempo in secondi dall'inizio della tappa.
        address: OSC address completo (es. ``/mod/journey/phase``).
        args: argomenti del messaggio. Per modulazioni: un singolo
            ``float`` o ``int``. Per eventi: una stringa JSON.
    """

    t: float
    address: str
    args: tuple[Any, ...]


def _group_of(channel: str) -> str | None:
    """Estrae il gruppo OSC dal nome canale (es. `journey_phase` -> `journey`)."""
    if "_" not in channel:
        return None
    return channel.split("_", 1)[0]


def _address_of(channel: str) -> str | None:
    """`journey_phase` -> `/mod/journey/phase`. Niente split = niente address."""
    if "_" not in channel:
        return None
    group, name = channel.split("_", 1)
    return f"/mod/{group}/{name}"


def _event_address(event: Event) -> str:
    """`/event/major/<kind>` o `/event/minor/<kind>`."""
    bus = "major" if event.category is EventCategory.MAJOR else "minor"
    return f"/event/{bus}/{event.kind}"


def _event_payload_json(event: Event) -> str:
    """Serializza l'evento come JSON compatto.

    Include: ``t``, ``payload`` (dict liberi), ``location`` se presente,
    ``source_id``. Le varianti dentro ``payload.variants`` sono gia'
    una lista di stringhe.
    """
    obj: dict[str, Any] = {"t": event.t, "payload": dict(event.payload)}
    if event.location is not None:
        obj["location"] = {
            "lat": event.location.lat,
            "lon": event.location.lon,
            "ele": event.location.ele,
        }
    if event.source_id is not None:
        obj["source_id"] = event.source_id
    return json.dumps(obj, ensure_ascii=False)


def _sample_channel(
    t: np.ndarray, values: np.ndarray, rate_hz: float,
) -> Iterable[tuple[float, float]]:
    """Sottocampiona un canale a `rate_hz`.

    Restituisce coppie ``(t_k, value_k)`` agli istanti
    ``0, 1/rate, 2/rate, ..., t_end``. Usa interpolazione lineare:
    il modulator interno gira a 10 Hz, l'OSC esce piu' lento.
    """
    if t.size == 0:
        return
    rate_hz = max(rate_hz, 1e-3)
    period = 1.0 / rate_hz
    t_end = float(t[-1])
    n = int(np.floor(t_end / period)) + 1
    ticks = np.arange(n, dtype=float) * period
    sampled = np.interp(ticks, t, values)
    for tk, vk in zip(ticks, sampled):
        yield float(tk), float(vk)


def build_schedule(
    frame: ModulationFrame,
    events: list[Event],
    config: Config = DEFAULT_CONFIG,
) -> list[ScheduledMessage]:
    """Costruisce la schedule completa, ordinata per `t`.

    Per i canali continui usa la frequenza configurata per gruppo
    (`config.osc.rates_hz`); canali senza gruppo o senza rate
    configurato vengono ignorati con `int` cast quando il nome
    suggerisce un canale intero (`scale`, `palette`, `root`,
    `euclid_k`, `euclid_rot`).
    """
    schedule: list[ScheduledMessage] = []

    # 1. Modulazioni continue.
    rates = config.osc.rates_hz
    for channel_name, values in frame.channels.items():
        group = _group_of(channel_name)
        if group is None or group not in rates:
            continue
        address = _address_of(channel_name)
        if address is None:
            continue
        cast_int = _CHANNEL_IS_INT.get(channel_name, False)
        for tk, vk in _sample_channel(frame.t, values, rates[group]):
            arg: Any = int(round(vk)) if cast_int else vk
            schedule.append(ScheduledMessage(t=tk, address=address, args=(arg,)))

    # 2. Eventi.
    for ev in events:
        schedule.append(ScheduledMessage(
            t=float(ev.t),
            address=_event_address(ev),
            args=(_event_payload_json(ev),),
        ))

    # 3. Ordinamento stabile per (t, address).
    schedule.sort(key=lambda m: (m.t, m.address))
    return schedule


# Canali del contratto che viaggiano come `int` (vedi
# CONTRATTO-MODULAZIONI.md §2.1, §2.2, §2.4).
_CHANNEL_IS_INT: dict[str, bool] = {
    "macro_scale": True,
    "macro_palette": True,
    "meso_root": True,
    "body_euclid_k": True,
    "body_euclid_rot": True,
}


# ──────────────────── Client OSC (Protocol) ────────────────────────


@runtime_checkable
class OscClient(Protocol):
    """Interfaccia minima per inviare un messaggio OSC."""

    def send_message(self, address: str, args: Any) -> None: ...


class UdpOscClient:
    """Wrapper su `python_osc.udp_client.SimpleUDPClient`.

    Import lazy: il modulo `sinks.osc` si importa anche senza
    `python-osc` installato; istanziare `UdpOscClient` solleva
    ``ImportError`` con messaggio utile.
    """

    def __init__(self, host: str, port: int) -> None:
        try:
            from pythonosc.udp_client import SimpleUDPClient
        except ImportError as exc:
            raise ImportError(
                "python-osc non installato. `pip install -e .[osc]`."
            ) from exc
        self._client = SimpleUDPClient(host, port)

    def send_message(self, address: str, args: Any) -> None:
        self._client.send_message(address, args)


class FakeOscClient:
    """Client OSC che accumula i messaggi in memoria. Usato nei test."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, Any]] = []

    def send_message(self, address: str, args: Any) -> None:
        self.sent.append((address, args))


# ──────────────────── OscSink (orchestratore) ──────────────────────


@dataclass
class OscSink:
    """Sink che invia `frame` + `events` come stream OSC in tempo reale.

    Args:
        client: implementazione di `OscClient` (default: ``UdpOscClient``
            costruito da ``config.osc``).
        config: usato per leggere le frequenze OSC per gruppo.
        speed: moltiplicatore di playback. `1.0` = tempo reale; `8.0`
            = otto volte piu' veloce. Utile per audit rapido di una
            tappa di 6 ore in ~45 minuti.
        sleep: funzione di sleep iniettabile (test la sostituiscono).

    Conforme al `Sink` Protocol: `emit(stage_id, frame, events)`
    blocca per ``duration_tappa / speed`` secondi.
    """

    client: OscClient
    config: Config = field(default_factory=lambda: DEFAULT_CONFIG)
    speed: float = 1.0
    sleep: Any = staticmethod(time.sleep)
    monotonic: Any = staticmethod(time.monotonic)

    def emit(self, stage_id: str, frame: ModulationFrame,
             events: list[Event]) -> None:
        if self.speed <= 0:
            raise ValueError("speed deve essere > 0")
        schedule = build_schedule(frame, events, self.config)
        self._play(schedule)

    def _play(self, schedule: list[ScheduledMessage]) -> None:
        if not schedule:
            return
        start_wall = self.monotonic()
        speed = self.speed
        for msg in schedule:
            target_wall = start_wall + msg.t / speed
            delay = target_wall - self.monotonic()
            if delay > 0:
                self.sleep(delay)
            self.client.send_message(msg.address, list(msg.args))


__all__ = [
    "ScheduledMessage",
    "build_schedule",
    "OscClient",
    "UdpOscClient",
    "FakeOscClient",
    "OscSink",
]

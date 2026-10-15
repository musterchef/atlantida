"""Test per `sinks.osc`: schedule pura + sink con FakeOscClient."""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest

from desnivel.config import DEFAULT_CONFIG, Config, OscConfig
from desnivel.events import Event, EventCategory
from desnivel.modulation import ModulationFrame
from desnivel.sinks.osc import (
    FakeOscClient,
    OscSink,
    ScheduledMessage,
    build_schedule,
)
from desnivel.track import GeoPoint


# ──────────────────── build_schedule ────────────────────


def _frame(duration_s: float, rate_hz: float = 10.0,
           **channels: np.ndarray) -> ModulationFrame:
    n = int(duration_s * rate_hz) + 1
    t = np.arange(n, dtype=float) / rate_hz
    return ModulationFrame(t=t, channels=dict(channels))


def test_empty_inputs_yield_empty_schedule():
    schedule = build_schedule(_frame(0.0), [])
    assert schedule == []


def test_continuous_channel_sampled_at_group_rate():
    """`journey_phase` viene campionato a 0.2 Hz (config default)."""
    duration_s = 30.0
    values = np.linspace(0.0, 1.0, int(duration_s * 10.0) + 1)
    frame = _frame(duration_s, journey_phase=values)
    schedule = build_schedule(frame, [])
    journey_msgs = [m for m in schedule if m.address == "/mod/journey/phase"]
    # 0.2 Hz su 30s -> ticks 0, 5, 10, 15, 20, 25, 30 = 7 messaggi.
    assert len(journey_msgs) == 7
    assert journey_msgs[0].t == 0.0
    assert journey_msgs[-1].t == pytest.approx(30.0)
    # Valore agli estremi: 0 e ~1.
    assert journey_msgs[0].args == (pytest.approx(0.0),)
    assert journey_msgs[-1].args == (pytest.approx(1.0),)


def test_channel_without_known_group_ignored():
    """Un canale `random_thing` non finisce nello stream OSC."""
    frame = _frame(5.0, random_thing=np.zeros(51))
    schedule = build_schedule(frame, [])
    assert schedule == []


def test_int_channel_cast():
    """`macro_scale` deve viaggiare come int."""
    frame = _frame(5.0, macro_scale=np.full(51, 2.7))
    schedule = build_schedule(frame, [])
    macros = [m for m in schedule if m.address == "/mod/macro/scale"]
    assert macros
    assert all(isinstance(m.args[0], int) for m in macros)
    assert macros[0].args == (3,)


def test_event_addresses_and_payload():
    frame = _frame(0.0)
    events = [
        Event(kind="summit", category=EventCategory.MAJOR, t=120.0,
              location=GeoPoint(lat=44.0, lon=10.0, ele=900.0),
              payload={"ele_m": 900.0, "prominence_m": 200.0},
              source_id="gpx_auto"),
        Event(kind="stop", category=EventCategory.MINOR, t=200.0,
              payload={"intensity": 0.7}),
    ]
    schedule = build_schedule(frame, events)
    assert schedule[0].address == "/event/major/summit"
    assert schedule[1].address == "/event/minor/stop"
    obj = json.loads(schedule[0].args[0])
    assert obj["t"] == 120.0
    assert obj["payload"]["ele_m"] == 900.0
    assert obj["location"]["lat"] == 44.0
    assert obj["source_id"] == "gpx_auto"


def test_schedule_ordered_by_time():
    frame = _frame(60.0, journey_phase=np.linspace(0.0, 1.0, 601),
                   meso_tension=np.linspace(0.0, 1.0, 601))
    events = [
        Event(kind="end", category=EventCategory.MAJOR, t=60.0, payload={}),
        Event(kind="start", category=EventCategory.MAJOR, t=0.0, payload={}),
    ]
    schedule = build_schedule(frame, events)
    times = [m.t for m in schedule]
    assert times == sorted(times)


# ──────────────────── OscSink ────────────────────


class _RecordingSleep:
    """Sostituto di `time.sleep` che accumula i delay richiesti."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, delay: float) -> None:
        self.delays.append(delay)


def _fake_monotonic(start: float = 1000.0):
    """Ritorna una funzione `monotonic()` che avanza di `0` ogni call
    (e' la `sleep` finta che dovrebbe avanzare il tempo). Per i test
    qui non serve avanzare: ci interessa solo cosa viene inviato."""
    def _mono() -> float:
        return start
    return _mono


def test_osc_sink_sends_schedule_in_order():
    client = FakeOscClient()
    sink = OscSink(client=client, sleep=_RecordingSleep(),
                   monotonic=_fake_monotonic())
    frame = _frame(10.0, journey_phase=np.linspace(0.0, 1.0, 101))
    events = [Event(kind="start", category=EventCategory.MAJOR, t=0.0,
                    payload={})]
    sink.emit("test", frame, events)
    addresses = [a for a, _ in client.sent]
    assert "/event/major/start" in addresses
    assert "/mod/journey/phase" in addresses


def test_osc_sink_respects_speed():
    """`speed=2.0` dimezza i tempi pianificati."""
    client = FakeOscClient()
    # Simulo un orologio che avanza ogni volta che sleep() viene chiamato.
    clock = [1000.0]

    def fake_sleep(d: float) -> None:
        clock[0] += d

    sink = OscSink(client=client, speed=2.0, sleep=fake_sleep,
                   monotonic=lambda: clock[0])
    frame = _frame(20.0, journey_phase=np.linspace(0.0, 1.0, 201))
    sink.emit("test", frame, [])
    # Tempo totale trascorso ~ 20 / 2 = 10s.
    elapsed = clock[0] - 1000.0
    assert elapsed == pytest.approx(10.0, abs=0.5)


def test_osc_sink_rejects_invalid_speed():
    with pytest.raises(ValueError):
        OscSink(client=FakeOscClient(), speed=0.0).emit(
            "x", _frame(0.0), [])


def test_osc_sink_skips_negative_delays():
    """Se lo scheduler e' in ritardo, non chiede sleep negativi."""
    client = FakeOscClient()
    recorder = _RecordingSleep()
    # `monotonic` che parte alto: la prima call torna 0, la seconda 1e6:
    # il primo delay diventa negativo.
    seq = iter([0.0, 1e6, 1e6, 1e6, 1e6, 1e6, 1e6, 1e6, 1e6, 1e6])
    sink = OscSink(client=client, sleep=recorder,
                   monotonic=lambda: next(seq))
    frame = _frame(1.0, journey_phase=np.linspace(0.0, 1.0, 11))
    sink.emit("test", frame, [])
    assert all(d >= 0 for d in recorder.delays)


def test_custom_osc_rates():
    """Cambiando `config.osc.rates_hz` cambia la cadenza."""
    config = replace(DEFAULT_CONFIG, osc=OscConfig(
        rates_hz={"journey": 1.0},  # 5x rispetto al default
    ))
    frame = _frame(10.0, journey_phase=np.linspace(0.0, 1.0, 101))
    schedule = build_schedule(frame, [], config=config)
    journey_msgs = [m for m in schedule if m.address == "/mod/journey/phase"]
    # 1 Hz su 10s -> 11 messaggi (0, 1, ..., 10).
    assert len(journey_msgs) == 11

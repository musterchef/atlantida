"""Messaggi OSC temporizzati e riproduzione con velocita' configurabile."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol


@dataclass(frozen=True)
class ScheduledMessage:
    """Messaggio OSC da inviare al tempo relativo `t` della tappa."""

    t: float
    address: str
    args: tuple[Any, ...]


class OscSender(Protocol):
    def send_message(self, address: str, args: Any) -> None: ...


def play_schedule(
    schedule: Iterable[ScheduledMessage],
    client: OscSender,
    speed: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> None:
    """Invia una schedule rispettando i tempi relativi divisi per `speed`."""
    if speed <= 0:
        raise ValueError("speed deve essere > 0")

    start_wall = monotonic()
    for message in schedule:
        target_wall = start_wall + message.t / speed
        delay = target_wall - monotonic()
        if delay > 0:
            sleep(delay)
        client.send_message(message.address, list(message.args))


__all__ = ["ScheduledMessage", "OscSender", "play_schedule"]
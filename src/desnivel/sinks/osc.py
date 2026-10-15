"""Client OSC condivisi dal producer e dagli adattatori."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


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


__all__ = ["OscClient", "UdpOscClient", "FakeOscClient"]

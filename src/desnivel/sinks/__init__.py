"""Sink: destinazioni di output (file, OSC, replay)."""
from .base import Sink
from .file_sink import FileSink
from .osc import (
    FakeOscClient,
    OscClient,
    OscSink,
    ScheduledMessage,
    UdpOscClient,
    build_schedule,
)

__all__ = [
    "Sink",
    "FileSink",
    "OscClient",
    "UdpOscClient",
    "FakeOscClient",
    "OscSink",
    "ScheduledMessage",
    "build_schedule",
]

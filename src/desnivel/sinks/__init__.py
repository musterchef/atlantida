"""Sink: destinazioni di output (file, OSC, replay)."""
from .base import Sink
from .file_sink import FileSink

__all__ = ["Sink", "FileSink"]

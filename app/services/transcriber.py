"""ASR engine protocol and test double.

The real faster-whisper implementation arrives in T3.2.  Keeping the protocol
small lets the API be tested without importing a model or touching the network.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    language: str


@runtime_checkable
class Transcriber(Protocol):
    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        """Transcribe mono 16 kHz float32 samples for the requested language."""


class FakeTranscriber:
    """Deterministic test double used by API tests and local smoke tests."""

    def __init__(
        self,
        text: str = "这是一段测试识别文本。",
        error: Exception | None = None,
        errors: list[Exception | None] | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        self.text = text
        self.error = error
        self._errors = list(errors) if errors is not None else None
        self.delay_seconds = delay_seconds
        self.calls: list[tuple[np.ndarray, str]] = []

    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        self.calls.append((samples, language))
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self._errors is not None and self._errors:
            error = self._errors.pop(0)
            if error is not None:
                raise error
        elif self._errors is None and self.error is not None:
            raise self.error
        return TranscriptionResult(text=self.text, language=language)


__all__ = ["FakeTranscriber", "Transcriber", "TranscriptionResult"]

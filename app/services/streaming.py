"""PCM streaming helpers for the optional realtime WebSocket path.

The regular HTTP path decodes a complete file with PyAV.  The realtime path
receives raw 16 kHz mono PCM16 little-endian chunks from the browser, keeps a
rolling buffer, and periodically transcribes the last few seconds to provide
near-real-time text.  The final message transcribes the full recording.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.errors import AudioTooLongError
from app.services.transcriber import Transcriber, TranscriptionResult

SAMPLE_RATE = 16_000
BYTES_PER_SAMPLE = 2
F6_MAX_SECONDS = 60.0
F6_WINDOW_SECONDS = 3.0
F6_PARTIAL_INTERVAL_SECONDS = 1.5
F6_FIRST_PARTIAL_SECONDS = 1.2
F6_RETRY_PARTIAL_SECONDS = 0.5


def pcm16le_to_float32(pcm: bytes) -> np.ndarray:
    """Convert little-endian PCM16 mono bytes to float32 in [-1, 1]."""

    if len(pcm) % BYTES_PER_SAMPLE:
        raise ValueError("PCM16 data must contain an even number of bytes")
    if not pcm:
        return np.empty(0, dtype=np.float32)
    return np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0


@dataclass
class StreamingConfig:
    sample_rate: int = SAMPLE_RATE
    max_seconds: float = F6_MAX_SECONDS
    window_seconds: float = F6_WINDOW_SECONDS
    partial_interval_seconds: float = F6_PARTIAL_INTERVAL_SECONDS
    first_partial_seconds: float = F6_FIRST_PARTIAL_SECONDS
    retry_partial_seconds: float = F6_RETRY_PARTIAL_SECONDS


class StreamingBuffer:
    """Accumulate PCM16 chunks and decide when to run a partial transcription."""

    def __init__(self, config: StreamingConfig | None = None) -> None:
        self.config = config or StreamingConfig()
        self._pcm = bytearray()
        self._last_partial_samples = 0
        self._partial_count = 0
        self._last_partial_empty = False

    @property
    def duration_seconds(self) -> float:
        return (len(self._pcm) // BYTES_PER_SAMPLE) / self.config.sample_rate

    @property
    def samples(self) -> int:
        return len(self._pcm) // BYTES_PER_SAMPLE

    def append(self, pcm: bytes) -> None:
        if not pcm:
            return
        if len(pcm) % BYTES_PER_SAMPLE:
            raise ValueError("PCM16 data must contain an even number of bytes")
        self._pcm.extend(pcm)
        max_bytes = int(self.config.max_seconds * self.config.sample_rate) * BYTES_PER_SAMPLE
        if len(self._pcm) > max_bytes:
            raise AudioTooLongError(int(self.config.max_seconds))

    def should_emit_partial(self) -> bool:
        if self._partial_count == 0:
            seconds = self.config.first_partial_seconds
        elif self._last_partial_empty:
            seconds = self.config.retry_partial_seconds
        else:
            seconds = self.config.partial_interval_seconds
        interval_samples = int(seconds * self.config.sample_rate)
        return self.samples - self._last_partial_samples >= interval_samples

    def mark_partial(self, had_text: bool = True) -> None:
        self._last_partial_samples = self.samples
        self._partial_count += 1
        self._last_partial_empty = not had_text

    def partial_pcm(self) -> bytes:
        window_bytes = int(self.config.window_seconds * self.config.sample_rate) * BYTES_PER_SAMPLE
        return bytes(self._pcm[-window_bytes:])

    def full_pcm(self) -> bytes:
        return bytes(self._pcm)


def transcribe_pcm(
    transcriber: Transcriber,
    pcm: bytes,
    language: str,
    *,
    use_prompt: bool = True,
    beam_size: int | None = None,
) -> TranscriptionResult:
    return transcriber.transcribe(
        pcm16le_to_float32(pcm),
        language,
        use_prompt=use_prompt,
        beam_size=beam_size,
    )


__all__ = [
    "BYTES_PER_SAMPLE",
    "F6_FIRST_PARTIAL_SECONDS",
    "F6_MAX_SECONDS",
    "F6_PARTIAL_INTERVAL_SECONDS",
    "F6_RETRY_PARTIAL_SECONDS",
    "F6_WINDOW_SECONDS",
    "SAMPLE_RATE",
    "StreamingBuffer",
    "StreamingConfig",
    "pcm16le_to_float32",
    "transcribe_pcm",
]

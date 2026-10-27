from __future__ import annotations

import io
import math
import struct
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.transcriber import FakeTranscriber


def make_wav_bytes(
    duration_seconds: float = 1.0,
    sample_rate: int = 16_000,
    silent: bool = False,
) -> bytes:
    """Create a small, valid mono 16-bit PCM WAV without external tools."""

    frame_count = max(1, int(duration_seconds * sample_rate))
    frames = bytearray()
    for index in range(frame_count):
        if silent:
            sample = 0
        else:
            sample = int(0.2 * 32767 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.extend(struct.pack("<h", sample))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))
    return buffer.getvalue()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_transcriber() -> FakeTranscriber:
    return FakeTranscriber()


@pytest.fixture
def failing_transcriber() -> FakeTranscriber:
    return FakeTranscriber(error=RuntimeError("fake transcription failure"))


@pytest.fixture
def wav_bytes() -> bytes:
    return make_wav_bytes(duration_seconds=1.0)


@pytest.fixture
def silent_wav_bytes() -> bytes:
    return make_wav_bytes(duration_seconds=0.5, silent=True)


@pytest.fixture
def corrupt_audio_bytes() -> bytes:
    return b"RIFF\x00\x00\x00\x00WAVEfmt-not-really-audio"


@pytest.fixture
def wav_file(tmp_path: Path, wav_bytes: bytes) -> Path:
    path = tmp_path / "sample.wav"
    path.write_bytes(wav_bytes)
    return path


@pytest.fixture
def wav_file_factory(tmp_path: Path):
    def make(
        duration_seconds: float = 1.0,
        *,
        silent: bool = False,
        name: str | None = None,
    ) -> Path:
        path = tmp_path / (
            name or f"sample-{duration_seconds}-{'silent' if silent else 'tone'}.wav"
        )
        path.write_bytes(make_wav_bytes(duration_seconds, silent=silent))
        return path

    return make

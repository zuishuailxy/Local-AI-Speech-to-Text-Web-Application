from __future__ import annotations

import time

import numpy as np
import pytest

from app.services.transcriber import FakeTranscriber, Transcriber, TranscriptionResult


def test_fake_satisfies_protocol() -> None:
    assert isinstance(FakeTranscriber(), Transcriber)


def test_result_contract() -> None:
    result = TranscriptionResult(text="hello", language="en")

    assert result.text == "hello"
    assert result.language == "en"
    assert result == TranscriptionResult(text="hello", language="en")


def test_fake_records_audio_and_language() -> None:
    fake = FakeTranscriber(text="result")
    audio = np.zeros(16_000, dtype=np.float32)

    result = fake.transcribe(audio, "zh")

    assert result == TranscriptionResult(text="result", language="zh")
    assert len(fake.calls) == 1
    samples, language = fake.calls[0]
    assert samples is audio
    assert language == "zh"


def test_fake_error_is_persistent() -> None:
    fake = FakeTranscriber(error=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        fake.transcribe(np.zeros(1, dtype=np.float32), "zh")
    with pytest.raises(RuntimeError, match="boom"):
        fake.transcribe(np.zeros(1, dtype=np.float32), "zh")
    assert len(fake.calls) == 2


def test_fake_errors_sequence_allows_recovery() -> None:
    fake = FakeTranscriber(
        text="recovered",
        errors=[RuntimeError("transient"), None],
    )
    audio = np.zeros(1, dtype=np.float32)

    with pytest.raises(RuntimeError, match="transient"):
        fake.transcribe(audio, "zh")
    result = fake.transcribe(audio, "zh")

    assert result.text == "recovered"
    assert len(fake.calls) == 2


def test_fake_delay(delayed_transcriber: FakeTranscriber) -> None:
    started = time.perf_counter()
    delayed_transcriber.transcribe(np.zeros(1, dtype=np.float32), "zh")
    elapsed = time.perf_counter() - started

    assert elapsed >= 0.008


def test_fake_rejects_negative_delay() -> None:
    with pytest.raises(ValueError, match="delay_seconds"):
        FakeTranscriber(delay_seconds=-0.1)

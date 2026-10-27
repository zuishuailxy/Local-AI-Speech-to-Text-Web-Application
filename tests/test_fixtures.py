from __future__ import annotations

import io
import wave

import pytest


def test_generated_wav_is_valid_and_one_second(wav_bytes: bytes) -> None:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16_000
        assert wav_file.getnframes() == 16_000


def test_silent_wav_contains_only_zero_samples(silent_wav_bytes: bytes) -> None:
    with wave.open(io.BytesIO(silent_wav_bytes), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())

    assert frames
    assert set(frames) == {0}


def test_corrupt_audio_fixture_is_not_empty(corrupt_audio_bytes: bytes) -> None:
    assert corrupt_audio_bytes.startswith(b"RIFF")
    assert corrupt_audio_bytes


def test_fake_transcriber_records_calls(fake_transcriber) -> None:
    result = fake_transcriber.transcribe(b"audio", "zh")

    assert result.text == "这是一段测试识别文本。"
    assert result.language == "zh"
    assert fake_transcriber.calls == [(b"audio", "zh")]


def test_fake_transcriber_can_raise(failing_transcriber) -> None:
    with pytest.raises(RuntimeError, match="fake transcription failure"):
        failing_transcriber.transcribe(b"audio", "en")


def test_default_app_has_no_model_loaded(client) -> None:
    assert client.app.state.transcriber is None


def test_markers_are_registered(pytestconfig) -> None:
    markers = "\n".join(pytestconfig.getini("markers"))

    assert "real_model" in markers
    assert "e2e" in markers


def test_default_addopts_excludes_heavy_tests(pytestconfig) -> None:
    addopts = " ".join(pytestconfig.getini("addopts"))

    assert "not real_model" in addopts
    assert "not e2e" in addopts

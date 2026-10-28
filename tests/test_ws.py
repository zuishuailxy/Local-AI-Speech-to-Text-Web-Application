from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import AudioTooLongError
from app.main import create_app
from app.services.streaming import (
    StreamingBuffer,
    StreamingConfig,
    pcm16le_to_float32,
)
from app.services.transcriber import FakeTranscriber


def pcm(seconds: float, sample_rate: int = 16_000) -> bytes:
    return np.zeros(int(seconds * sample_rate), dtype="<i2").tobytes()


def make_client(tmp_path, transcriber=None) -> TestClient:
    settings = Settings.from_env(
        environ={"MAX_AUDIO_SECONDS": "60", "LOG_LEVEL": "WARNING"},
        project_root=tmp_path,
    )
    return TestClient(create_app(transcriber=transcriber, settings=settings))


def test_pcm16le_to_float32() -> None:
    samples = np.array([0, 16384, -32768], dtype="<i2")
    converted = pcm16le_to_float32(samples.tobytes())

    assert converted.dtype == np.float32
    assert converted.tolist() == pytest.approx([0.0, 0.5, -1.0])


def test_streaming_buffer_partial_and_window() -> None:
    buffer = StreamingBuffer(
        StreamingConfig(
            max_seconds=4,
            window_seconds=1,
            partial_interval_seconds=1,
            first_partial_seconds=1,
        )
    )

    buffer.append(pcm(0.5))
    assert buffer.should_emit_partial() is False
    buffer.append(pcm(0.5))
    assert buffer.should_emit_partial() is True
    assert buffer.duration_seconds == pytest.approx(1.0)
    assert len(buffer.partial_pcm()) == 16_000 * 2
    assert len(buffer.full_pcm()) == 16_000 * 2

    buffer.mark_partial()
    assert buffer.should_emit_partial() is False


def test_streaming_buffer_rejects_too_long_and_odd_pcm() -> None:
    buffer = StreamingBuffer(StreamingConfig(max_seconds=1))

    with pytest.raises(AudioTooLongError):
        buffer.append(pcm(1.1))
    with pytest.raises(ValueError):
        buffer.append(b"\x00")


def test_ws_partial_then_final(tmp_path) -> None:
    fake = FakeTranscriber(text="实时识别文本。")
    client = make_client(tmp_path, fake)

    with client.websocket_connect("/ws/transcribe?language=zh") as ws:
        ws.send_bytes(pcm(2.0))
        partial = ws.receive_json()
        assert partial["type"] == "partial"
        assert partial["text"] == "实时识别文本。"
        assert partial["duration_seconds"] == pytest.approx(2.0)
        assert partial["processing_seconds"] >= 0

        ws.send_bytes(pcm(1.0))
        ws.send_text('{"type":"stop"}')
        final = ws.receive_json()

    assert final["type"] == "final"
    assert final["text"] == "实时识别文本。"
    assert final["language"] == "zh"
    assert final["duration_seconds"] == pytest.approx(3.0)
    assert final["processing_seconds"] >= 0
    assert len(fake.calls) == 2


def test_ws_stop_without_audio_returns_empty_final(tmp_path) -> None:
    fake = FakeTranscriber(text="不应调用")
    client = make_client(tmp_path, fake)

    with client.websocket_connect("/ws/transcribe?language=en") as ws:
        ws.send_text('{"type":"stop"}')
        final = ws.receive_json()

    assert final == {
        "type": "final",
        "text": "",
        "language": "en",
        "duration_seconds": 0.0,
        "processing_seconds": 0.0,
    }
    assert fake.calls == []


def test_ws_rejects_invalid_language(tmp_path) -> None:
    client = make_client(tmp_path, FakeTranscriber())

    with client.websocket_connect("/ws/transcribe?language=fr") as ws:
        error = ws.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "invalid_language"


def test_ws_rejects_missing_transcriber(tmp_path) -> None:
    client = make_client(tmp_path, None)

    with client.websocket_connect("/ws/transcribe?language=zh") as ws:
        error = ws.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "model_unavailable"


def test_ws_rejects_invalid_message(tmp_path) -> None:
    client = make_client(tmp_path, FakeTranscriber())

    with client.websocket_connect("/ws/transcribe?language=zh") as ws:
        ws.send_text("not-json")
        error = ws.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "invalid_message"


def test_ws_auto_language_returns_detected_language(tmp_path) -> None:
    fake = FakeTranscriber(text="auto ws", detected_language="zh")
    client = make_client(tmp_path, fake)

    with client.websocket_connect("/ws/transcribe?language=auto") as ws:
        ws.send_bytes(pcm(2.0))
        partial = ws.receive_json()
        assert partial["type"] == "partial"
        ws.send_text('{"type":"stop"}')
        final = ws.receive_json()

    assert final["type"] == "final"
    assert final["language"] == "zh"
    assert fake.calls[0][1] == "auto"


def test_partial_transcription_disables_prompt() -> None:
    from app.services.streaming import transcribe_pcm
    from app.services.transcriber import TranscriptionResult

    calls: list[tuple[bool, int | None]] = []

    class Spy:
        def transcribe(self, samples, language, *, use_prompt=True, beam_size=None):
            calls.append((use_prompt, beam_size))
            return TranscriptionResult(text="x", language="zh")

    pcm = b"\x00\x00" * 1600
    transcribe_pcm(Spy(), pcm, "zh", use_prompt=False, beam_size=1)
    transcribe_pcm(Spy(), pcm, "zh")
    assert calls == [(False, 1), (True, None)]


def test_first_partial_uses_shorter_initial_threshold() -> None:
    buffer = StreamingBuffer(StreamingConfig())
    buffer.append(pcm(1.1))
    assert buffer.should_emit_partial() is False
    buffer.append(pcm(0.2))
    assert buffer.should_emit_partial() is True

    buffer.mark_partial()
    buffer.append(pcm(1.0))
    assert buffer.should_emit_partial() is False
    buffer.append(pcm(0.5))
    assert buffer.should_emit_partial() is True

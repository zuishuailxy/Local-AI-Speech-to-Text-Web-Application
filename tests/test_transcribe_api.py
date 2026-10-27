from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.transcriber import FakeTranscriber


def make_transcribe_client(
    tmp_path,
    transcriber=None,
    *,
    max_audio_seconds: int = 10,
) -> TestClient:
    settings = Settings.from_env(
        environ={
            "MAX_AUDIO_SECONDS": str(max_audio_seconds),
            "MAX_UPLOAD_MB": "10",
        },
        project_root=tmp_path,
    )
    return TestClient(create_app(transcriber=transcriber, settings=settings))


def post_wav(
    client: TestClient,
    wav_bytes: bytes,
    *,
    language: str = "zh",
    filename: str = "sample.wav",
    content_type: str = "audio/wav",
):
    return client.post(
        "/api/transcribe",
        data={"language": language},
        files={"file": (filename, wav_bytes, content_type)},
    )


def test_transcribe_chinese_contract(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber(text="你好，欢迎使用语音识别系统。")
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes, language="zh")

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "你好，欢迎使用语音识别系统。"
    assert body["language"] == "zh"
    assert body["duration_seconds"] == pytest.approx(1.0, abs=0.02)
    assert body["processing_seconds"] >= 0
    assert set(body) == {
        "text",
        "language",
        "duration_seconds",
        "processing_seconds",
    }

    samples, language = fake.calls[0]
    assert isinstance(samples, np.ndarray)
    assert samples.dtype == np.float32
    assert samples.shape == (16_000,)
    assert language == "zh"


def test_transcribe_english_contract(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber(text="Hello, this is a local speech test.")
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes, language="en")

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Hello, this is a local speech test."
    assert body["language"] == "en"
    assert fake.calls[0][1] == "en"


def test_transcribe_twice_has_no_request_state(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber(text="repeatable")
    client = make_transcribe_client(tmp_path, fake)

    first = post_wav(client, wav_bytes, language="zh")
    second = post_wav(client, wav_bytes, language="en")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["text"] == "repeatable"
    assert second.json()["language"] == "en"
    assert len(fake.calls) == 2


def test_language_is_normalized_in_response(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber(text="normalized")
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes, language="ZH")

    assert response.status_code == 200
    assert response.json()["language"] == "zh"
    assert fake.calls[0][1] == "zh"


def test_invalid_language_returns_400(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber()
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes, language="fr")

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_language"
    assert fake.calls == []


def test_missing_file_returns_422(tmp_path) -> None:
    client = make_transcribe_client(tmp_path, FakeTranscriber())

    response = client.post("/api/transcribe", data={"language": "zh"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_missing_language_returns_422(tmp_path, wav_bytes: bytes) -> None:
    client = make_transcribe_client(tmp_path, FakeTranscriber())

    response = client.post(
        "/api/transcribe",
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_unsupported_format_returns_415(tmp_path, wav_bytes: bytes) -> None:
    client = make_transcribe_client(tmp_path, FakeTranscriber())

    response = post_wav(
        client,
        wav_bytes,
        filename="notes.txt",
        content_type="text/plain",
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_format"


def test_empty_file_returns_400(tmp_path) -> None:
    client = make_transcribe_client(tmp_path, FakeTranscriber())

    response = client.post(
        "/api/transcribe",
        data={"language": "zh"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "empty_file"


def test_fake_wav_returns_400(tmp_path) -> None:
    client = make_transcribe_client(tmp_path, FakeTranscriber())

    response = client.post(
        "/api/transcribe",
        data={"language": "zh"},
        files={"file": ("fake.wav", b"not a wave", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_audio"


def test_too_long_audio_returns_400(
    tmp_path, wav_file_factory
) -> None:
    client = make_transcribe_client(
        tmp_path,
        FakeTranscriber(),
        max_audio_seconds=1,
    )
    payload = wav_file_factory(2.0).read_bytes()

    response = post_wav(client, payload, language="zh", filename="long.wav")

    assert response.status_code == 400
    assert response.json()["code"] == "audio_too_long"


def test_model_unavailable_returns_503(tmp_path, wav_bytes: bytes) -> None:
    client = make_transcribe_client(tmp_path, None)

    response = post_wav(client, wav_bytes)

    assert response.status_code == 503
    assert response.json()["code"] == "model_unavailable"


def test_transcription_failure_returns_500(
    tmp_path, wav_bytes: bytes
) -> None:
    fake = FakeTranscriber(error=RuntimeError("private implementation detail"))
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes)

    assert response.status_code == 500
    assert response.json()["code"] == "transcription_failed"
    assert "private implementation detail" not in response.text


def test_empty_text_is_returned_as_200(tmp_path, wav_bytes: bytes) -> None:
    fake = FakeTranscriber(text="")
    client = make_transcribe_client(tmp_path, fake)

    response = post_wav(client, wav_bytes)

    assert response.status_code == 200
    assert response.json()["text"] == ""

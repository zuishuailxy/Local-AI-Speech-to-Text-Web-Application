from __future__ import annotations

import logging
import re

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.transcriber import FakeTranscriber


def make_client(tmp_path, *, text: str = "测试文本") -> TestClient:
    settings = Settings.from_env(
        environ={"LOG_LEVEL": "INFO"},
        project_root=tmp_path,
    )
    return TestClient(
        create_app(transcriber=FakeTranscriber(text=text), settings=settings)
    )


def test_request_id_is_returned_and_logged(client, caplog) -> None:
    with caplog.at_level(logging.INFO, logger="app.main"):
        response = client.get("/health", headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "trace-123"
    assert "http_request method=GET path=/health status=200" in caplog.text
    assert "request_id=trace-123" in caplog.text
    assert "duration_ms=" in caplog.text


def test_request_id_is_generated_when_missing(client) -> None:
    response = client.get("/health")

    request_id = response.headers["x-request-id"]
    assert re.fullmatch(r"[a-f0-9]{12}", request_id)


def test_transcribe_logs_metadata_but_not_text(
    tmp_path, wav_bytes: bytes, caplog
) -> None:
    secret = "这是一段不应写入日志的识别文本。"
    client = make_client(tmp_path, text=secret)

    with caplog.at_level(logging.INFO, logger="app"):
        response = client.post(
            "/api/transcribe",
            data={"language": "zh"},
            files={"file": ("sample.wav", wav_bytes, "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json()["text"] == secret

    log = caplog.text
    assert "transcribe_request" in log
    assert "language=zh" in log
    assert "extension=.wav" in log
    assert "audio_upload_stored" in log
    assert "audio_decoded" in log
    assert "transcribe_complete outcome=success" in log
    assert "text_chars=" in log
    assert "request_id=" in log
    assert secret not in log


def test_api_error_is_logged_with_code(tmp_path, wav_bytes: bytes, caplog) -> None:
    client = make_client(tmp_path)

    with caplog.at_level(logging.INFO, logger="app"):
        response = client.post(
            "/api/transcribe",
            data={"language": "fr"},
            files={"file": ("sample.wav", wav_bytes, "audio/wav")},
        )

    assert response.status_code == 400
    assert "api_error outcome=error" in caplog.text
    assert "status=400" in caplog.text
    assert "code=invalid_language" in caplog.text


def test_app_log_level_is_applied(tmp_path) -> None:
    settings = Settings.from_env(
        environ={"LOG_LEVEL": "DEBUG"},
        project_root=tmp_path,
    )
    app_logger = logging.getLogger("app")
    previous_level = app_logger.level

    try:
        create_app(settings=settings)
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.setLevel(previous_level)

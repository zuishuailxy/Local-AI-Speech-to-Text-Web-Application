from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.transcriber import FakeTranscriber


def make_settings(tmp_path: Path, **overrides: str) -> Settings:
    environ = {"LOG_LEVEL": "INFO", **overrides}
    return Settings.from_env(environ=environ, project_root=tmp_path)


def cleanup_app_handlers() -> None:
    app_logger = logging.getLogger("app")
    for handler in list(app_logger.handlers):
        if getattr(handler, "_stt_handler", False):
            app_logger.removeHandler(handler)
            handler.close()
    app_logger.propagate = True


def test_text_log_file_and_privacy(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.log"
    settings = make_settings(tmp_path, LOG_FILE=str(log_path))
    secret = "这条识别文本不能出现在日志里"
    app = create_app(transcriber=FakeTranscriber(text=secret), settings=settings)
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
            response = client.post(
                "/api/transcribe",
                data={"language": "zh"},
                files={"file": ("sample.wav", b"RIFF" + b"\0" * 100, "audio/wav")},
            )
        # Invalid WAV is enough to exercise request logging; no model call.
        contents = log_path.read_text(encoding="utf-8")
        assert "http_request" in contents
        assert "outcome=error" in contents
        assert secret not in contents
    finally:
        cleanup_app_handlers()


def test_json_log_format(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "server.jsonl"
    settings = make_settings(
        tmp_path,
        LOG_FILE=str(log_path),
        LOG_FORMAT="json",
    )
    app = create_app(transcriber=FakeTranscriber(), settings=settings)
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
        lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
        assert lines
        parsed = [json.loads(line) for line in lines]
        assert any(entry["level"] == "INFO" for entry in parsed)
        assert any("http_request" in entry["message"] for entry in parsed)
    finally:
        cleanup_app_handlers()


def test_rotating_handler_is_configured(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "rotating.log"
    settings = make_settings(
        tmp_path,
        LOG_FILE=str(log_path),
        LOG_MAX_BYTES="1024",
        LOG_BACKUP_COUNT="2",
    )
    create_app(transcriber=FakeTranscriber(), settings=settings)
    try:
        handlers = [
            handler
            for handler in logging.getLogger("app").handlers
            if getattr(handler, "_stt_handler", False)
        ]
        assert len(handlers) == 1
        handler = handlers[0]
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 1024
        assert handler.backupCount == 2
    finally:
        cleanup_app_handlers()


def test_default_logging_has_no_file_handler(tmp_path: Path) -> None:
    create_app(transcriber=FakeTranscriber(), settings=make_settings(tmp_path))
    try:
        assert not any(
            getattr(handler, "_stt_handler", False)
            for handler in logging.getLogger("app").handlers
        )
    finally:
        cleanup_app_handlers()

from __future__ import annotations

import asyncio
import io

import pytest
from fastapi import File, Form, UploadFile
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import EmptyFileError, FileTooLargeError, InvalidLanguageError
from app.main import create_app
from app.services.audio import (
    save_upload_to_temp,
    validate_content_length,
    validate_language,
    validate_upload,
    validate_upload_metadata,
)


@pytest.fixture
def audio_client():
    app = create_app()

    @app.post("/__test/transcribe")
    async def test_transcribe(
        file: UploadFile = File(...), language: str = Form(...)
    ) -> dict[str, str]:
        extension = await validate_upload(file, language)
        return {"extension": extension}

    return TestClient(app)


def test_missing_file_returns_422(audio_client: TestClient) -> None:
    response = audio_client.post("/__test/transcribe", data={"language": "zh"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_missing_language_returns_422(
    audio_client: TestClient, wav_bytes: bytes
) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("language", ["fr", "zh-CN", "auto"])
def test_invalid_language_returns_400(
    audio_client: TestClient, wav_bytes: bytes, language: str
) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": language},
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_language"


def test_language_is_case_insensitive() -> None:
    assert validate_language("ZH") == "zh"
    assert validate_language(" en ") == "en"


def test_empty_language_is_rejected() -> None:
    with pytest.raises(InvalidLanguageError):
        validate_language("")


def test_empty_file_returns_400(audio_client: TestClient) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "zh"},
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "empty_file"


def test_unsupported_extension_returns_415(
    audio_client: TestClient, wav_bytes: bytes
) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "zh"},
        files={"file": ("notes.txt", wav_bytes, "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_format"


def test_extensionless_filename_returns_415(
    audio_client: TestClient, wav_bytes: bytes
) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "zh"},
        files={"file": ("recording", wav_bytes, "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_format"


def test_fake_wav_content_returns_400(audio_client: TestClient) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "zh"},
        files={"file": ("fake.wav", b"this is not a wave file", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_audio"


def test_valid_wav_is_accepted(audio_client: TestClient, wav_bytes: bytes) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "zh"},
        files={"file": ("sample.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {"extension": ".wav"}


def test_uppercase_wav_extension_is_accepted(
    audio_client: TestClient, wav_bytes: bytes
) -> None:
    response = audio_client.post(
        "/__test/transcribe",
        data={"language": "en"},
        files={"file": ("SAMPLE.WAV", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {"extension": ".wav"}


def test_validate_upload_metadata_directly() -> None:
    assert validate_upload_metadata("clip.WEBM", 123, "en") == ".webm"


def test_zero_size_metadata_is_empty_file() -> None:
    with pytest.raises(EmptyFileError):
        validate_upload_metadata("clip.wav", 0, "zh")


def test_validate_content_length_rejects_excess() -> None:
    with pytest.raises(FileTooLargeError) as exc_info:
        validate_content_length(
            str(10 * 1024 * 1024 + 1),
            10 * 1024 * 1024,
            overhead_bytes=0,
        )

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "file_too_large"


def test_validate_content_length_allows_multipart_overhead() -> None:
    validate_content_length(
        str(10 * 1024 * 1024 + 512 * 1024),
        10 * 1024 * 1024,
    )


def test_content_length_guard_runs_before_route(tmp_path) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "1"}, project_root=tmp_path
    )
    app = create_app(settings=settings)

    @app.post("/api/transcribe")
    async def transcribe_probe() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    response = client.post(
        "/api/transcribe",
        content=b"x" * (3 * 1024 * 1024),
    )

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_small_request_passes_content_length_guard(tmp_path) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "1"}, project_root=tmp_path
    )
    app = create_app(settings=settings)

    @app.post("/api/transcribe")
    async def transcribe_probe() -> dict[str, bool]:
        return {"ok": True}

    response = TestClient(app).post("/api/transcribe", content=b"ok")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_save_upload_to_temp_writes_and_cleans(tmp_path, wav_bytes: bytes) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "10"}, project_root=tmp_path
    )
    upload = UploadFile(
        file=io.BytesIO(wav_bytes),
        filename="sample.wav",
        size=len(wav_bytes),
    )
    stored = asyncio.run(
        save_upload_to_temp(
            upload,
            "zh",
            settings,
            temp_dir=tmp_path / "uploads",
            chunk_size=1024,
        )
    )

    assert stored.path.exists()
    assert stored.path.read_bytes() == wav_bytes
    assert stored.size == len(wav_bytes)
    assert stored.extension == ".wav"

    path = stored.path
    stored.cleanup()
    assert not path.exists()


def test_save_upload_to_temp_rejects_declared_oversize(tmp_path) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "1"}, project_root=tmp_path
    )
    payload = b"x" * (1024 * 1024 + 1)
    upload = UploadFile(
        file=io.BytesIO(payload),
        filename="oversize.webm",
        size=len(payload),
    )
    upload_dir = tmp_path / "uploads"

    with pytest.raises(FileTooLargeError):
        asyncio.run(
            save_upload_to_temp(
                upload,
                "zh",
                settings,
                temp_dir=upload_dir,
            )
        )

    assert not upload_dir.exists() or not list(upload_dir.iterdir())


def test_save_upload_to_temp_enforces_limit_while_streaming(tmp_path) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "1"}, project_root=tmp_path
    )
    payload = b"x" * (2 * 1024 * 1024)
    upload = UploadFile(
        file=io.BytesIO(payload),
        filename="oversize.webm",
        size=None,
    )
    upload_dir = tmp_path / "uploads"

    with pytest.raises(FileTooLargeError):
        asyncio.run(
            save_upload_to_temp(
                upload,
                "zh",
                settings,
                temp_dir=upload_dir,
                chunk_size=64 * 1024,
            )
        )

    assert not upload_dir.exists() or not list(upload_dir.iterdir())


def test_save_upload_to_temp_context_manager_cleans(tmp_path, wav_bytes: bytes) -> None:
    settings = Settings.from_env(
        environ={"MAX_UPLOAD_MB": "10"}, project_root=tmp_path
    )
    upload = UploadFile(
        file=io.BytesIO(wav_bytes),
        filename="sample.wav",
        size=len(wav_bytes),
    )

    with asyncio.run(save_upload_to_temp(upload, "en", settings)) as stored:
        path = stored.path
        assert path.exists()

    assert not path.exists()


def test_default_ten_mb_plus_one_is_rejected(tmp_path) -> None:
    settings = Settings.from_env(environ={}, project_root=tmp_path)
    payload = b"x" * (10 * 1024 * 1024 + 1)
    upload = UploadFile(
        file=io.BytesIO(payload),
        filename="oversize.webm",
        size=len(payload),
    )

    with pytest.raises(FileTooLargeError):
        asyncio.run(save_upload_to_temp(upload, "zh", settings))

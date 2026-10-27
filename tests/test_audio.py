from __future__ import annotations

import pytest
from fastapi import File, Form, UploadFile
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.audio import validate_language, validate_upload, validate_upload_metadata


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
    from app.errors import InvalidLanguageError

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
    from app.errors import EmptyFileError

    with pytest.raises(EmptyFileError):
        validate_upload_metadata("clip.wav", 0, "zh")

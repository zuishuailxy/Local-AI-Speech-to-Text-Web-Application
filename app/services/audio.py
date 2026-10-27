"""Audio upload validation and (later) decoding helpers.

T2.1 deliberately validates metadata and the WAV container header only.  Full
decoding, duration checks and temporary-file streaming are implemented in T2.2
and T2.3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from fastapi import UploadFile

from app.config import SUPPORTED_LANGUAGES
from app.errors import (
    EmptyFileError,
    InvalidAudioError,
    InvalidLanguageError,
    UnsupportedFormatError,
)

ALLOWED_AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".wav",
        ".webm",
        ".ogg",
        ".oga",
        ".mp3",
        ".m4a",
        ".mp4",
        ".flac",
    }
)

_WAV_HEADER_SIZE = 12


def validate_language(
    language: str, supported: tuple[str, ...] = SUPPORTED_LANGUAGES
) -> str:
    """Normalize and validate the requested language."""

    normalized = (language or "").strip().lower()
    if normalized not in supported:
        raise InvalidLanguageError(
            f"language 仅支持 {', '.join(supported)}，收到: {language!r}。"
        )
    return normalized


def validate_upload_metadata(
    filename: str | None,
    size: int | None,
    language: str,
    supported_languages: tuple[str, ...] = SUPPORTED_LANGUAGES,
) -> str:
    """Validate cheap metadata before reading the file body.

    Returns the normalized extension (including the leading dot).  MIME types
    are not trusted because browsers frequently send ``application/octet-stream``.
    """

    validate_language(language, supported_languages)

    if not filename or not filename.strip():
        raise EmptyFileError("文件名为空，无法判断音频格式。")

    extension = Path(filename).suffix.lower()
    if not extension or extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise UnsupportedFormatError(
            "不支持该文件格式，请上传 WAV、WebM、OGG、MP3、M4A、MP4 或 FLAC。"
        )

    if size is not None and size <= 0:
        raise EmptyFileError()

    return extension


def _is_wav_header(header: bytes) -> bool:
    return (
        len(header) >= _WAV_HEADER_SIZE
        and header[:4] == b"RIFF"
        and header[8:12] == b"WAVE"
    )


async def validate_upload(
    file: UploadFile,
    language: str,
    supported_languages: tuple[str, ...] = SUPPORTED_LANGUAGES,
) -> str:
    """Validate language, filename/extension, non-empty body and WAV header.

    The file position is reset to 0 so the caller can read/stream it afterwards.
    Other containers (WebM/OGG/MP3/...) are validated fully by the decoder in
    T2.3; this function only rejects obviously invalid WAV headers early.
    """

    extension = validate_upload_metadata(
        file.filename,
        file.size,
        language,
        supported_languages,
    )

    header = b""
    if file.size is None or extension == ".wav":
        header = await file.read(_WAV_HEADER_SIZE)
        await file.seek(0)
        if not header:
            raise EmptyFileError()

    if extension == ".wav" and not _is_wav_header(header):
        raise InvalidAudioError(
            "文件扩展名为 .wav，但内容不是有效的 WAV 文件。"
        )

    return extension


__all__ = [
    "ALLOWED_AUDIO_EXTENSIONS",
    "validate_language",
    "validate_upload",
    "validate_upload_metadata",
]

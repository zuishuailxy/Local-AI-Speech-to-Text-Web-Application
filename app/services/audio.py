"""Audio upload validation, streaming and decoding helpers.

T2.1 validates metadata; T2.2 copies uploads with a size limit; T2.3 decodes
supported containers to 16 kHz mono float32 and enforces the duration limit.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import av
import numpy as np
from fastapi import UploadFile

from app.config import SUPPORTED_LANGUAGES, Settings
from app.errors import (
    ApiError,
    AudioTooLongError,
    EmptyFileError,
    FileTooLargeError,
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
ASR_SAMPLE_RATE: Final[int] = 16_000
MAX_MULTIPART_OVERHEAD_BYTES: Final[int] = 1024 * 1024
DEFAULT_CHUNK_SIZE: Final[int] = 1024 * 1024


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


def validate_content_length(
    content_length: str | None,
    max_upload_bytes: int,
    *,
    overhead_bytes: int = MAX_MULTIPART_OVERHEAD_BYTES,
) -> None:
    """Reject obviously oversized requests before multipart parsing.

    Multipart boundaries add a small amount of overhead, so the header check
    allows one MiB more than the file limit.  The exact byte limit is still
    enforced while copying the file in ``save_upload_to_temp``.
    """

    if content_length is None:
        return
    try:
        total_bytes = int(content_length)
    except (TypeError, ValueError):
        return
    if total_bytes < 0:
        return
    if total_bytes > max_upload_bytes + overhead_bytes:
        limit_mb = max(1, max_upload_bytes // (1024 * 1024))
        raise FileTooLargeError(limit_mb)


@dataclass
class StoredUpload:
    """A temporary upload that must be cleaned up by the caller."""

    path: Path
    size: int
    extension: str
    _tempdir: tempfile.TemporaryDirectory

    def cleanup(self) -> None:
        self._tempdir.cleanup()

    def __enter__(self) -> "StoredUpload":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.cleanup()


async def save_upload_to_temp(
    file: UploadFile,
    language: str,
    settings: Settings,
    *,
    temp_dir: Path | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> StoredUpload:
    """Copy an upload to a temporary file while enforcing the byte limit.

    The upload is never fully loaded into memory.  The returned object keeps
    its temporary directory alive; callers must use it as a context manager or
    call ``cleanup()`` in a ``finally`` block.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    extension = await validate_upload(
        file, language, settings.supported_languages
    )
    await file.seek(0)

    max_bytes = settings.max_upload_bytes
    if file.size is not None and file.size > max_bytes:
        raise FileTooLargeError(settings.max_upload_mb)

    if temp_dir is not None:
        temp_dir.mkdir(parents=True, exist_ok=True)

    tempdir = tempfile.TemporaryDirectory(prefix="local-stt-", dir=temp_dir)
    target = Path(tempdir.name) / f"upload{extension}"
    total = 0
    try:
        with target.open("wb") as destination:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise FileTooLargeError(settings.max_upload_mb)
                destination.write(chunk)

        if total == 0:
            raise EmptyFileError()
    except Exception:
        tempdir.cleanup()
        raise

    return StoredUpload(
        path=target,
        size=total,
        extension=extension,
        _tempdir=tempdir,
    )


@dataclass(frozen=True, slots=True)
class DecodedAudio:
    """Decoded mono float32 audio at the ASR sample rate."""

    samples: np.ndarray
    sample_rate: int = ASR_SAMPLE_RATE

    @property
    def duration_seconds(self) -> float:
        return len(self.samples) / self.sample_rate


def _frame_to_float_samples(frame: av.AudioFrame) -> np.ndarray:
    array = np.asarray(frame.to_ndarray(), dtype=np.float32)
    if array.ndim == 2:
        # PyAV returns (channels, samples) for planar/2-D frames.  The resampler
        # is configured for mono, but averaging keeps this safe for odd inputs.
        array = array.mean(axis=0) if array.shape[0] > 1 else array[0]
    return np.asarray(array, dtype=np.float32).reshape(-1)


def decode_audio(path: Path, settings: Settings) -> DecodedAudio:
    """Decode an audio file to 16 kHz mono float32.

    The container duration is checked before decoding when available, then the
    actual decoded sample count is capped to ``settings.max_audio_seconds``.
    The caller owns the input file and must clean up its temporary directory.
    """

    max_seconds = settings.max_audio_seconds
    max_samples = int(max_seconds * ASR_SAMPLE_RATE)
    chunks: list[np.ndarray] = []
    total_samples = 0

    try:
        with av.open(str(path), mode="r") as container:
            if not container.streams.audio:
                raise InvalidAudioError("文件中没有可识别的音频流。")

            if container.duration is not None:
                container_seconds = container.duration / av.time_base
                if container_seconds > max_seconds + 0.05:
                    raise AudioTooLongError(max_seconds)

            stream = container.streams.audio[0]
            resampler = av.AudioResampler(
                format="flt",
                layout="mono",
                rate=ASR_SAMPLE_RATE,
            )

            for frame in container.decode(stream):
                for resampled in resampler.resample(frame):
                    samples = _frame_to_float_samples(resampled)
                    total_samples += len(samples)
                    if total_samples > max_samples:
                        raise AudioTooLongError(max_seconds)
                    chunks.append(samples)

            for resampled in resampler.resample(None):
                samples = _frame_to_float_samples(resampled)
                total_samples += len(samples)
                if total_samples > max_samples:
                    raise AudioTooLongError(max_seconds)
                chunks.append(samples)
    except ApiError:
        raise
    except (av.FFmpegError, OSError, ValueError, IndexError) as exc:
        raise InvalidAudioError(
            "无法解码该音频文件，请检查文件是否损坏或格式是否受支持。"
        ) from exc

    if not chunks or total_samples == 0:
        raise InvalidAudioError("音频中没有可解码的采样数据。")

    samples = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
    return DecodedAudio(samples=samples, sample_rate=ASR_SAMPLE_RATE)


__all__ = [
    "ALLOWED_AUDIO_EXTENSIONS",
    "ASR_SAMPLE_RATE",
    "DEFAULT_CHUNK_SIZE",
    "DecodedAudio",
    "MAX_MULTIPART_OVERHEAD_BYTES",
    "StoredUpload",
    "decode_audio",
    "save_upload_to_temp",
    "validate_content_length",
    "validate_language",
    "validate_upload",
    "validate_upload_metadata",
]

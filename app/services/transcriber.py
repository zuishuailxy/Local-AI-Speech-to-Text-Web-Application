"""ASR engine protocol, test double, and the faster-whisper adapter.

The real model is imported lazily inside the adapter.  Merely importing this
module (and therefore ``app.main``) must never load a model or access the
network.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

import numpy as np

from app.config import Settings
from app.errors import (
    ApiError,
    ModelUnavailableError,
    TranscriptionFailedError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    language: str


@runtime_checkable
class Transcriber(Protocol):
    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        """Transcribe mono 16 kHz float32 samples for the requested language."""


class FakeTranscriber:
    """Deterministic test double used by API tests and local smoke tests."""

    def __init__(
        self,
        text: str = "这是一段测试识别文本。",
        error: Exception | None = None,
        errors: list[Exception | None] | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        self.text = text
        self.error = error
        self._errors = list(errors) if errors is not None else None
        self.delay_seconds = delay_seconds
        self.calls: list[tuple[np.ndarray, str]] = []

    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        self.calls.append((samples, language))
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self._errors is not None and self._errors:
            error = self._errors.pop(0)
            if error is not None:
                raise error
        elif self._errors is None and self.error is not None:
            raise self.error
        return TranscriptionResult(text=self.text, language=language)


ModelFactory = Callable[..., Any]


def _load_faster_whisper_model(
    model_path: str,
    *,
    device: str,
    compute_type: str,
    cpu_threads: int,
) -> Any:
    # Deliberately late import: no model/network work at module import time.
    from faster_whisper import WhisperModel

    return WhisperModel(
        model_path,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads,
    )


class WhisperTranscriber:
    """Thread-safe, lazy faster-whisper adapter.

    One instance owns one model.  Loading and inference are serialized with a
    lock; the application is intentionally single-user, and concurrent
    CTranslate2 inference is not required by this assessment.
    """

    def __init__(
        self,
        settings: Settings,
        model_factory: ModelFactory | None = None,
    ) -> None:
        self._settings = settings
        self._model_factory: ModelFactory = (
            model_factory or _load_faster_whisper_model
        )
        self._model: Any | None = None
        self._lock = threading.Lock()

    @property
    def model_path(self) -> Path:
        return self._settings.asr_model_path

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _load_model(self) -> Any:
        path = self._settings.asr_model_path
        if not path.exists():
            raise ModelUnavailableError(
                f"本地识别模型不存在：{path}。请先运行模型下载脚本。"
            )

        try:
            model = self._model_factory(
                str(path),
                device=self._settings.asr_device,
                compute_type=self._settings.asr_compute_type,
                cpu_threads=self._settings.asr_cpu_threads,
            )
        except ApiError:
            raise
        except Exception as exc:
            logger.exception("Failed to load ASR model from %s", path)
            raise ModelUnavailableError(
                "本地识别模型加载失败，请检查模型文件和运行环境。"
            ) from exc

        self._model = model
        logger.info("Loaded ASR model from %s (device=%s)", path, self._settings.asr_device)
        return model

    def warmup(self) -> None:
        with self._lock:
            if self._model is None:
                self._load_model()

    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        with self._lock:
            model = self._model
            if model is None:
                model = self._load_model()

            try:
                segments, _info = model.transcribe(
                    samples,
                    language=language,
                    beam_size=self._settings.asr_beam_size,
                    vad_filter=self._settings.asr_vad_filter,
                )
                text = "".join(segment.text for segment in segments).strip()
            except ApiError:
                raise
            except Exception as exc:
                logger.exception("ASR inference failed")
                raise TranscriptionFailedError("语音识别失败，请稍后重试。") from exc

        return TranscriptionResult(text=text, language=language)


__all__ = [
    "FakeTranscriber",
    "ModelFactory",
    "Transcriber",
    "TranscriptionResult",
    "WhisperTranscriber",
]

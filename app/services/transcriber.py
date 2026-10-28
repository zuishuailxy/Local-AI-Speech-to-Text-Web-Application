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
from app.services.metrics import cjk_ratio, latin_ratio
from app.services.text import to_simplified

logger = logging.getLogger(__name__)
AUTO_LANGUAGE = "auto"
AUTO_MIN_PROBABILITY = 0.55


def _output_language_hint(text: str) -> str:
    """Best-effort script hint for observability; never changes the result."""

    cjk = cjk_ratio(text)
    latin = latin_ratio(text)
    if cjk >= 0.5 and cjk > latin:
        return "zh"
    if latin >= 0.5 and latin > cjk:
        return "en"
    return "unknown"


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
        detected_language: str | None = None,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        self.text = text
        self.error = error
        self._errors = list(errors) if errors is not None else None
        self.delay_seconds = delay_seconds
        self.detected_language = detected_language
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
        return TranscriptionResult(
            text=self.text,
            language=self.detected_language or language,
        )


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
            started = time.perf_counter()
            model = self._model_factory(
                str(path),
                device=self._settings.asr_device,
                compute_type=self._settings.asr_compute_type,
                cpu_threads=self._settings.asr_cpu_threads,
            )
            load_seconds = time.perf_counter() - started
        except ApiError:
            raise
        except Exception as exc:
            logger.exception("Failed to load ASR model from %s", path)
            raise ModelUnavailableError(
                "本地识别模型加载失败，请检查模型文件和运行环境。"
            ) from exc

        self._model = model
        logger.info(
            "Loaded ASR model from %s (device=%s, compute_type=%s, "
            "cpu_threads=%d, model_load_seconds=%.3f)",
            path,
            self._settings.asr_device,
            self._settings.asr_compute_type,
            self._settings.asr_cpu_threads,
            load_seconds,
        )
        return model

    def warmup(self) -> None:
        with self._lock:
            if self._model is None:
                self._load_model()

    def transcribe(self, samples: np.ndarray, language: str) -> TranscriptionResult:
        sample_count = int(samples.size)
        logger.info(
            "asr_start requested_language=%s samples=%d", language, sample_count
        )
        with self._lock:
            model = self._model
            if model is None:
                model = self._load_model()

            started = time.perf_counter()
            try:
                model_language = None if language == AUTO_LANGUAGE else language
                segments, info = model.transcribe(
                    samples,
                    language=model_language,
                    beam_size=self._settings.asr_beam_size,
                    vad_filter=self._settings.asr_vad_filter,
                )
                text = "".join(segment.text for segment in segments).strip()
                detected_language = getattr(info, "language", None)
                result_language = language
                if language == AUTO_LANGUAGE:
                    probability = getattr(info, "language_probability", None)
                    confident = (
                        probability is None
                        or probability >= AUTO_MIN_PROBABILITY
                    )
                    if detected_language in {"zh", "en"} and confident:
                        result_language = detected_language
                    else:
                        hint = _output_language_hint(text)
                        result_language = (
                            hint if hint in {"zh", "en"} else AUTO_LANGUAGE
                        )
                        logger.warning(
                            "asr_auto_low_confidence detected_language=%s "
                            "language_probability=%s fallback_language=%s "
                            "text_language=%s",
                            detected_language,
                            probability,
                            result_language,
                            hint,
                        )
                if result_language == "zh":
                    text = to_simplified(text)
            except ApiError:
                raise
            except Exception as exc:
                logger.exception("ASR inference failed")
                raise TranscriptionFailedError("语音识别失败，请稍后重试。") from exc
            inference_seconds = time.perf_counter() - started

        language_probability = getattr(info, "language_probability", None)
        output_language = _output_language_hint(text)
        normalization = "zhconv-zh-cn" if result_language == "zh" else "none"
        logger.info(
            "asr_complete requested_language=%s detected_language=%s "
            "language_probability=%s output_language=%s output_cjk_ratio=%.3f "
            "output_latin_ratio=%.3f normalization=%s samples=%d "
            "inference_seconds=%.3f text_chars=%d",
            language,
            detected_language,
            language_probability,
            output_language,
            cjk_ratio(text),
            latin_ratio(text),
            normalization,
            sample_count,
            inference_seconds,
            len(text),
        )
        if output_language != "unknown" and output_language != result_language:
            logger.warning(
                "asr_language_mismatch requested_language=%s "
                "resolved_language=%s output_language=%s detected_language=%s "
                "text_chars=%d",
                language,
                result_language,
                output_language,
                detected_language,
                len(text),
            )

        return TranscriptionResult(text=text, language=result_language)


__all__ = [
    "FakeTranscriber",
    "ModelFactory",
    "Transcriber",
    "TranscriptionResult",
    "WhisperTranscriber",
]

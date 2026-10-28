from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.errors import (
    ApiError,
    ModelUnavailableError,
    TranscriptionFailedError,
)
from app.schemas import TranscriptionResponse
from app.services.audio import process_audio_upload, validate_language
from app.services.transcriber import Transcriber

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness/readiness probe required by the assessment."""

    return {"status": "ok"}


@router.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    tags=["speech"],
)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form(...),
) -> TranscriptionResponse:
    """Validate/decode an upload, run the injected ASR engine, return the result."""

    started = time.perf_counter()
    settings = request.app.state.settings
    normalized_language = validate_language(
        language, settings.supported_languages, allow_auto=True
    )
    request_id = getattr(request.state, "request_id", "-")
    extension = Path(file.filename or "").suffix.lower() or "unknown"

    logger.info(
        "transcribe_request request_id=%s language=%s extension=%s size=%s",
        request_id,
        normalized_language,
        extension,
        file.size,
    )

    # Decoding and temporary-file cleanup happen before the model call.  All
    # file/language errors therefore remain 4xx even when no model is loaded.
    audio = await process_audio_upload(
        file,
        normalized_language,
        settings,
        allow_auto=normalized_language == "auto",
    )

    logger.info(
        "transcribe_decoded request_id=%s language=%s duration_seconds=%.3f "
        "sample_rate=%d samples=%d",
        request_id,
        normalized_language,
        audio.duration_seconds,
        audio.sample_rate,
        audio.samples.size,
    )

    transcriber: Transcriber | None = getattr(
        request.app.state, "transcriber", None
    )
    if transcriber is None:
        logger.warning(
            "transcribe_unavailable request_id=%s reason=no_transcriber",
            request_id,
        )
        raise ModelUnavailableError(
            "识别引擎尚未配置，请先初始化本地模型。"
        )

    try:
        result = await run_in_threadpool(
            transcriber.transcribe,
            audio.samples,
            normalized_language,
        )
    except ApiError:
        raise
    except Exception as exc:
        logger.exception(
            "transcribe_failed request_id=%s language=%s",
            request_id,
            normalized_language,
        )
        raise TranscriptionFailedError("语音识别失败，请稍后重试。") from exc

    processing_seconds = round(time.perf_counter() - started, 3)
    response_language = (
        result.language if normalized_language == "auto" else normalized_language
    )
    logger.info(
        "transcribe_complete outcome=success request_id=%s language=%s "
        "response_language=%s duration_seconds=%.3f processing_seconds=%.3f "
        "text_chars=%d",
        request_id,
        normalized_language,
        response_language,
        audio.duration_seconds,
        processing_seconds,
        len(result.text),
    )

    return TranscriptionResponse(
        text=result.text,
        language=response_language,
        duration_seconds=round(audio.duration_seconds, 3),
        processing_seconds=processing_seconds,
    )

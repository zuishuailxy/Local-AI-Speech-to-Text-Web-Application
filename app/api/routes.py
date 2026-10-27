from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.errors import (
    ApiError,
    ModelUnavailableError,
    TranscriptionFailedError,
)
from app.schemas import TranscriptionResponse
from app.services.audio import process_audio_upload, validate_language

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
    normalized_language = validate_language(language, settings.supported_languages)

    # Decoding and temporary-file cleanup happen before the model call.  All
    # file/language errors therefore remain 4xx even when no model is loaded.
    audio = await process_audio_upload(
        file,
        normalized_language,
        settings,
    )

    transcriber: Any = getattr(request.app.state, "transcriber", None)
    if transcriber is None:
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
        raise TranscriptionFailedError("语音识别失败，请稍后重试。") from exc

    return TranscriptionResponse(
        text=result.text,
        language=normalized_language,
        duration_seconds=round(audio.duration_seconds, 3),
        processing_seconds=round(time.perf_counter() - started, 3),
    )

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.api.ws import router as ws_router
from app.config import PROJECT_ROOT, Settings
from app.errors import FileTooLargeError, register_exception_handlers
from app.logging_config import configure_logging
from app.services.audio import validate_content_length
from app.services.transcriber import Transcriber, WhisperTranscriber

logger = logging.getLogger(__name__)

STATIC_DIR = PROJECT_ROOT / "static"


def create_app(
    transcriber: Transcriber | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Create the FastAPI application.

    ``transcriber`` is injected for tests and for a future ASR engine.  It is
    intentionally stored as-is: this module must never load a model at import
    time, so ``pytest`` and ``/health`` stay fast and offline.
    """

    resolved_settings = settings or Settings.from_env()
    configure_logging(resolved_settings)
    logger.info(
        "app_configured model_path=%s device=%s compute_type=%s "
        "cpu_threads=%d beam_size=%d vad_filter=%s max_upload_mb=%d "
        "max_audio_seconds=%d log_level=%s",
        resolved_settings.asr_model_path,
        resolved_settings.asr_device,
        resolved_settings.asr_compute_type,
        resolved_settings.asr_cpu_threads,
        resolved_settings.asr_beam_size,
        resolved_settings.asr_vad_filter,
        resolved_settings.max_upload_mb,
        resolved_settings.max_audio_seconds,
        resolved_settings.log_level,
    )
    app = FastAPI(
        title="Local AI Speech-to-Text",
        version="0.1.0",
        description="Local CPU speech-to-text web application",
    )
    app.state.transcriber = transcriber
    app.state.settings = resolved_settings

    register_exception_handlers(app)

    @app.middleware("http")
    async def limit_upload_size(request, call_next):
        if request.method == "POST" and request.url.path == "/api/transcribe":
            try:
                validate_content_length(
                    request.headers.get("content-length"),
                    resolved_settings.max_upload_bytes,
                )
            except FileTooLargeError as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content=exc.to_payload(),
                )
        return await call_next(request)

    @app.middleware("http")
    async def log_requests(request, call_next):
        raw_request_id = request.headers.get("x-request-id", "")
        request_id = (
            "".join(
                char
                for char in raw_request_id
                if char.isalnum() or char in {"-", "_", "."}
            )[:64]
            or uuid.uuid4().hex[:12]
        )
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "http_request_failed method=%s path=%s error=%s request_id=%s",
                request.method,
                request.url.path,
                type(exc).__name__,
                request_id,
            )
            raise
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "http_request method=%s path=%s status=%d duration_ms=%.1f "
            "request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(router)
    app.include_router(ws_router)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


_production_settings = Settings.from_env()
app = create_app(
    transcriber=WhisperTranscriber(_production_settings),
    settings=_production_settings,
)

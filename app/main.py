from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import PROJECT_ROOT, Settings
from app.errors import FileTooLargeError, register_exception_handlers
from app.services.audio import validate_content_length
from app.services.transcriber import Transcriber, WhisperTranscriber

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

    app.include_router(router)

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

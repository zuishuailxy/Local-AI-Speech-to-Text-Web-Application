from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import PROJECT_ROOT

STATIC_DIR = PROJECT_ROOT / "static"


def create_app(transcriber: object | None = None) -> FastAPI:
    """Create the FastAPI application.

    ``transcriber`` is injected for tests and for a future ASR engine.  It is
    intentionally stored as-is: this module must never load a model at import
    time, so ``pytest`` and ``/health`` stay fast and offline.
    """

    app = FastAPI(
        title="Local AI Speech-to-Text",
        version="0.1.0",
        description="Local CPU speech-to-text web application",
    )
    app.state.transcriber = transcriber

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()

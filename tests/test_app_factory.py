from fastapi.testclient import TestClient

from app.main import app as production_app
from app.main import create_app
from app.services.transcriber import WhisperTranscriber


def test_factory_injects_transcriber() -> None:
    sentinel = object()
    app = create_app(transcriber=sentinel)

    assert app.state.transcriber is sentinel


def test_factory_defaults_to_no_transcriber() -> None:
    app = create_app()

    assert app.state.transcriber is None


def test_factory_creates_independent_apps() -> None:
    first = create_app()
    second = create_app()

    assert first is not second
    assert first.state.transcriber is None
    assert second.state.transcriber is None


def test_factory_serves_health_without_model() -> None:
    app = create_app(transcriber=object())

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_production_app_has_lazy_whisper_engine() -> None:
    assert isinstance(production_app.state.transcriber, WhisperTranscriber)
    assert production_app.state.transcriber.is_loaded is False

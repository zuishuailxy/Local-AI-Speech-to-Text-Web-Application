from fastapi.testclient import TestClient

from app.main import create_app


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

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_exact_contract() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_html_placeholder() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Local AI Speech-to-Text" in response.text


def test_static_index_is_mounted() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Local AI Speech-to-Text" in response.text


def test_missing_static_file_returns_404() -> None:
    response = client.get("/static/does-not-exist.js")

    assert response.status_code == 404

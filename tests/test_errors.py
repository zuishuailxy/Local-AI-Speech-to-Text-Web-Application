import pytest
from fastapi.testclient import TestClient

from app.errors import (
    ApiError,
    InvalidAudioError,
    ModelUnavailableError,
    TranscriptionFailedError,
)
from app.main import create_app


def build_test_app():
    app = create_app()

    @app.get("/__test/api-error")
    def raise_api_error(
        status_code: int = 400,
        code: str = "bad_request",
        message: str = "bad request",
    ) -> None:
        raise ApiError(status_code, code, message)

    @app.get("/__test/model-unavailable")
    def raise_model_unavailable() -> None:
        raise ModelUnavailableError()

    @app.get("/__test/transcription-failed")
    def raise_transcription_failed() -> None:
        raise TranscriptionFailedError()

    @app.get("/__test/invalid-audio")
    def raise_invalid_audio() -> None:
        raise InvalidAudioError()

    @app.get("/__test/validation")
    def validation_route(count: int) -> dict[str, int]:
        return {"count": count}

    @app.get("/__test/unhandled")
    def unhandled_route() -> None:
        raise RuntimeError("boom: secret details")

    return app


@pytest.mark.parametrize(
    ("status_code", "code"),
    [
        (400, "invalid_language"),
        (413, "file_too_large"),
        (415, "unsupported_format"),
        (503, "model_unavailable"),
    ],
)
def test_api_error_returns_status_and_code(status_code: int, code: str) -> None:
    client = TestClient(build_test_app())

    response = client.get(
        "/__test/api-error",
        params={"status_code": status_code, "code": code, "message": "expected message"},
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": "expected message", "code": code}


def test_domain_errors_have_stable_contract() -> None:
    client = TestClient(build_test_app())

    unavailable = client.get("/__test/model-unavailable")
    failed = client.get("/__test/transcription-failed")
    invalid = client.get("/__test/invalid-audio")

    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "model_unavailable"
    assert failed.status_code == 500
    assert failed.json()["code"] == "transcription_failed"
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "invalid_audio"


def test_validation_error_is_readable_and_has_code() -> None:
    client = TestClient(build_test_app())

    response = client.get("/__test/validation")

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert isinstance(payload["detail"], str)
    assert "count" in payload["detail"]


def test_unknown_route_returns_json_404() -> None:
    client = TestClient(build_test_app())

    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_wrong_method_returns_json_405() -> None:
    client = TestClient(build_test_app())

    response = client.post("/health")

    assert response.status_code == 405
    assert response.json()["code"] == "method_not_allowed"


def test_unhandled_exception_returns_generic_500() -> None:
    client = TestClient(build_test_app(), raise_server_exceptions=False)

    response = client.get("/__test/unhandled")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "服务器内部错误，请稍后重试。",
        "code": "internal_error",
    }
    assert "secret" not in response.text
    assert "RuntimeError" not in response.text


def test_health_is_not_affected_by_error_handlers() -> None:
    client = TestClient(build_test_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

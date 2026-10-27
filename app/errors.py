"""Application errors and consistent JSON error responses."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_HTTP_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "file_too_large",
    415: "unsupported_format",
    422: "validation_error",
    429: "too_many_requests",
    500: "internal_error",
    503: "service_unavailable",
}


class ApiError(Exception):
    """An expected application error with a stable machine-readable code."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message

    def to_payload(self) -> dict[str, str]:
        return {"detail": self.message, "code": self.code}


class EmptyFileError(ApiError):
    """The uploaded file is empty."""

    def __init__(self, message: str = "上传文件为空，请选择包含语音的音频文件。") -> None:
        super().__init__(400, "empty_file", message)


class UnsupportedFormatError(ApiError):
    """The file extension is not in the supported audio whitelist."""

    def __init__(self, message: str = "不支持该文件格式，请上传 WAV、WebM、OGG、MP3、M4A、MP4 或 FLAC。") -> None:
        super().__init__(415, "unsupported_format", message)


class FileTooLargeError(ApiError):
    """The uploaded file exceeds the configured size limit."""

    def __init__(self, limit_mb: int = 10) -> None:
        super().__init__(
            413,
            "file_too_large",
            f"上传文件超过 {limit_mb} MB 限制，请选择更短的音频。",
        )


class InvalidLanguageError(ApiError):
    """The requested language is not supported."""

    def __init__(self, message: str = "language 仅支持 zh 或 en。") -> None:
        super().__init__(400, "invalid_language", message)


class ModelUnavailableError(ApiError):
    """The ASR model is missing or failed to initialize."""

    def __init__(self, message: str = "本地识别模型不可用，请先初始化模型或检查模型路径。") -> None:
        super().__init__(503, "model_unavailable", message)


class TranscriptionFailedError(ApiError):
    """The model ran but transcription failed."""

    def __init__(self, message: str = "语音识别失败，请稍后重试。") -> None:
        super().__init__(500, "transcription_failed", message)


class InvalidAudioError(ApiError):
    """The uploaded bytes cannot be decoded as supported audio."""

    def __init__(self, message: str = "无法解码该音频文件，请检查文件是否损坏。") -> None:
        super().__init__(400, "invalid_audio", message)


def _validation_detail(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "请求参数校验失败"

    first = errors[0]
    location = ".".join(
        str(part) for part in first.get("loc", ()) if part not in {"body", "query", "path"}
    )
    message = str(first.get("msg", "请求参数无效"))
    return f"{location}: {message}" if location else message


def _http_detail(exc: StarletteHTTPException) -> str:
    detail: Any = exc.detail
    if isinstance(detail, str) and detail.strip():
        return detail
    return f"HTTP {exc.status_code}"


def register_exception_handlers(app: FastAPI) -> None:
    """Register JSON handlers used by both the API and the browser client."""

    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": _validation_detail(exc), "code": "validation_error"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": _http_detail(exc),
                "code": _HTTP_CODES.get(exc.status_code, "http_error"),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Do not log request bodies/audio; only the route and exception type.
        logger.exception(
            "Unhandled error on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试。", "code": "internal_error"},
        )


__all__ = [
    "ApiError",
    "EmptyFileError",
    "FileTooLargeError",
    "InvalidAudioError",
    "InvalidLanguageError",
    "ModelUnavailableError",
    "TranscriptionFailedError",
    "UnsupportedFormatError",
    "register_exception_handlers",
]

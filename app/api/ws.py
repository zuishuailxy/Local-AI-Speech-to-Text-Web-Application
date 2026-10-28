"""Optional realtime WebSocket endpoint (F6).

Protocol (text frames are JSON):

    ws://127.0.0.1:8000/ws/transcribe?language=zh

    client -> server: binary PCM16LE mono 16 kHz chunks
    server -> client: {"type": "partial", "text": "...", "duration_seconds": 2.0}
    client -> server: {"type": "stop"} (or the plain text "stop")
    server -> client: {"type": "final", "text": "...", "language": "zh",
                      "duration_seconds": 8.0, "processing_seconds": 1.2}
    errors: {"type": "error", "detail": "...", "code": "..."} then close
"""

from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.errors import ApiError, AudioTooLongError, ModelUnavailableError
from app.services.audio import validate_language
from app.services.streaming import StreamingBuffer, StreamingConfig, transcribe_pcm
from app.services.transcriber import Transcriber

logger = logging.getLogger(__name__)

router = APIRouter()


def _error_payload(exc: ApiError) -> dict[str, str]:
    return {"type": "error", "detail": exc.message, "code": exc.code}


async def _send_error(websocket: WebSocket, exc: ApiError) -> None:
    await websocket.send_json(_error_payload(exc))
    await websocket.close(code=1008 if exc.status_code < 500 else 1011)


@router.websocket("/ws/transcribe")
async def transcribe_stream(websocket: WebSocket, language: str | None = None) -> None:
    await websocket.accept()
    connection_id = uuid.uuid4().hex[:12]
    settings = websocket.app.state.settings
    try:
        normalized_language = validate_language(
            language or "", settings.supported_languages
        )
    except ApiError as exc:
        logger.info(
            "ws_rejected connection_id=%s reason=%s", connection_id, exc.code
        )
        await _send_error(websocket, exc)
        return

    transcriber: Transcriber | None = getattr(
        websocket.app.state, "transcriber", None
    )
    if transcriber is None:
        await _send_error(
            websocket,
            ModelUnavailableError("识别引擎尚未配置，请先初始化本地模型。"),
        )
        return

    buffer = StreamingBuffer(StreamingConfig())
    partial_count = 0
    logger.info(
        "ws_open connection_id=%s language=%s", connection_id, normalized_language
    )

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            if message.get("bytes") is not None:
                try:
                    buffer.append(message["bytes"])
                except ValueError as exc:
                    await _send_error(
                        websocket,
                        ApiError(400, "invalid_pcm", str(exc)),
                    )
                    return
                except AudioTooLongError as exc:
                    await _send_error(websocket, exc)
                    return

                if buffer.should_emit_partial():
                    started = time.perf_counter()
                    result = await run_in_threadpool(
                        transcribe_pcm,
                        transcriber,
                        buffer.partial_pcm(),
                        normalized_language,
                    )
                    buffer.mark_partial()
                    partial_count += 1
                    await websocket.send_json(
                        {
                            "type": "partial",
                            "text": result.text,
                            "duration_seconds": round(buffer.duration_seconds, 3),
                            "partial_index": partial_count,
                            "processing_seconds": round(
                                time.perf_counter() - started, 3
                            ),
                        }
                    )
                continue

            text = (message.get("text") or "").strip()
            if not text:
                continue
            if text == "stop" or text == '{"type":"stop"}':
                break
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                await _send_error(
                    websocket,
                    ApiError(400, "invalid_message", "只接受 stop 或 JSON 消息。"),
                )
                return
            if payload.get("type") == "stop":
                break
            await _send_error(
                websocket,
                ApiError(400, "invalid_message", "只接受 stop 或 PCM 二进制分片。"),
            )
            return
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected connection_id=%s", connection_id)
        return
    except Exception:
        logger.exception("ws_stream_failed connection_id=%s", connection_id)
        try:
            await _send_error(websocket, ModelUnavailableError("实时识别失败，请重试。"))
        except Exception:
            pass
        return

    started = time.perf_counter()
    try:
        if buffer.samples:
            result = await run_in_threadpool(
                transcribe_pcm,
                transcriber,
                buffer.full_pcm(),
                normalized_language,
            )
            text = result.text
        else:
            text = ""
        processing_seconds = round(time.perf_counter() - started, 3)
        logger.info(
            "ws_final connection_id=%s language=%s duration_seconds=%.3f "
            "processing_seconds=%.3f text_chars=%d partials=%d",
            connection_id,
            normalized_language,
            buffer.duration_seconds,
            processing_seconds,
            len(text),
            partial_count,
        )
        await websocket.send_json(
            {
                "type": "final",
                "text": text,
                "language": normalized_language,
                "duration_seconds": round(buffer.duration_seconds, 3),
                "processing_seconds": processing_seconds,
            }
        )
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
    except Exception:
        logger.exception("ws_final_failed connection_id=%s", connection_id)
        try:
            await _send_error(websocket, ModelUnavailableError("最终识别失败，请重试。"))
        except Exception:
            pass

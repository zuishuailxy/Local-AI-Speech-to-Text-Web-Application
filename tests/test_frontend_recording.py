from __future__ import annotations

from pathlib import Path

JS = (Path(__file__).resolve().parent.parent / "static" / "app.js").read_text(
    encoding="utf-8"
)


def test_media_recorder_mime_candidates_are_declared() -> None:
    for mime in (
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
    ):
        assert mime in JS
    assert "MediaRecorder.isTypeSupported" in JS


def test_get_user_media_constraints() -> None:
    assert "navigator.mediaDevices.getUserMedia" in JS
    assert "channelCount: 1" in JS
    assert "echoCancellation: true" in JS
    assert "noiseSuppression: true" in JS


def test_recorder_collects_chunks_and_releases_tracks() -> None:
    assert 'addEventListener("dataavailable"' in JS
    assert "recorder.start(1000)" in JS
    assert "state.chunks.push(event.data)" in JS
    assert "getTracks().forEach" in JS
    assert "track.stop()" in JS


def test_actual_mime_and_blob_are_kept_for_upload() -> None:
    assert "recorder.mimeType" in JS
    assert "new Blob(state.chunks" in JS
    assert "window.__lastRecording" in JS
    assert "state.lastRecording" in JS


def test_permission_error_names_are_mapped() -> None:
    for name in ("NotAllowedError", "NotFoundError", "NotReadableError", "SecurityError"):
        assert name in JS

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


def test_timer_and_sixty_second_limit_contract() -> None:
    assert "MAX_RECORDING_MS = 60_000" in JS
    assert "TIMER_INTERVAL_MS = 200" in JS
    assert "setInterval(updateRecordingTimer, TIMER_INTERVAL_MS)" in JS
    assert "formatElapsed" in JS
    assert 'document.addEventListener("visibilitychange"' in JS
    assert "stoppedByLimit" in JS
    assert "recordedMs" in JS
    assert "recorder.start(1000)" in JS


def test_error_recovery_hooks_and_guards() -> None:
    assert 'getElementById("retry-button")' in JS
    assert 'getElementById("dismiss-error-button")' in JS
    assert 'addEventListener("click", retryRecording)' in JS
    assert 'addEventListener("click", dismissError)' in JS
    assert "recordingFailed" in JS
    assert "window.isSecureContext" in JS
    assert "OverconstrainedError" in JS
    assert "AbortError" in JS
    assert "没有录到音频" in JS


def test_file_selection_validation_contract() -> None:
    assert "MAX_UPLOAD_BYTES = 10 * 1024 * 1024" in JS
    assert '".wav"' in JS and '".webm"' in JS and '".m4a"' in JS
    assert 'getElementById("file-input")' in JS
    assert 'addEventListener("change", handleFileSelection)' in JS
    assert "file.size === 0" in JS
    assert "file.size > MAX_UPLOAD_BYTES" in JS
    assert "不支持的" in JS or "不支持该文件格式" in JS
    assert "上传文件超过 10 MB" in JS

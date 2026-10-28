from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


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
    assert 'addEventListener("click", retryLastAction)' in JS
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


def test_transcribe_request_and_result_contract() -> None:
    assert 'fetch("/api/transcribe"' in JS
    assert "new FormData()" in JS
    assert 'formData.append("file"' in JS
    assert 'formData.append("language"' in JS
    assert "requestInFlight" in JS
    assert "startProcessingTimer" in JS
    assert "stopProcessingTimer" in JS
    assert "showResult(payload, blob)" in JS
    assert "processing_seconds" in JS
    assert "duration_seconds" in JS
    assert "lastSubmission" in JS
    assert "submitAudio(blob, filename" in JS


def test_copy_contract() -> None:
    assert 'getElementById("copy-button")' in JS
    assert 'addEventListener("click", copyResult)' in JS
    assert "navigator.clipboard" in JS
    assert "writeText(text)" in JS
    assert 'document.execCommand("copy")' in JS
    assert "fallbackCopy" in JS
    assert "已复制" in JS
    assert "复制失败" in JS
    assert 'elements.copyButton.disabled = true' in JS


def test_request_error_and_retry_contract() -> None:
    assert "parseApiError" in JS
    assert "describeRequestError" in JS
    assert "无法连接后端" in JS
    assert "retryLastAction" in JS
    assert "state.selectedFile" in JS
    assert "state.lastSubmission" in JS
    assert "dismissError" in JS
    assert "识别失败：" in JS


def test_realtime_contract() -> None:
    assert 'getElementById("realtime-toggle")' in JS
    assert "async function startRealtime" in JS
    assert "function stopRealtime" in JS
    assert "createScriptProcessor(" in JS
    assert "/ws/transcribe" in JS
    assert 'type: "stop"' in JS
    assert "resampleTo16k" in JS
    assert "floatToPcm16" in JS
    assert "audioWorklet" in JS
    assert "AudioWorkletNode" in JS
    assert "pcm-worklet.js" in JS
    assert 'payload.type === "partial"' in JS
    assert 'payload.type === "final"' in JS


def test_auto_language_option_contract() -> None:
    assert '<option value="auto">' in HTML
    assert '"auto"' in JS
    assert "自动检测" in JS
    assert 'language === "auto"' in JS

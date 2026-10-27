(function () {
  "use strict";

  const MIME_CANDIDATES = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
  ];

  const MAX_RECORDING_MS = 60_000;
  const TIMER_INTERVAL_MS = 200;
  const ACTIVE_PHASES = new Set(["requesting", "recording", "transcribing"]);

  const elements = {
    app: document.getElementById("app"),
    startButton: document.getElementById("start-button"),
    stopButton: document.getElementById("stop-button"),
    statusBadge: document.getElementById("status-badge"),
    statusText: document.getElementById("status-text"),
    recordingTimer: document.getElementById("recording-timer"),
    pipelineState: document.getElementById("pipeline-state"),
    stepCapture: document.getElementById("step-capture"),
    permissionNote: document.getElementById("permission-note"),
    errorPanel: document.getElementById("error-panel"),
    errorMessage: document.getElementById("error-message"),
  };

  const state = {
    phase: "idle",
    recording: false,
    stream: null,
    recorder: null,
    chunks: [],
    mimeType: null,
    lastRecording: null,
    startTimeMs: 0,
    timerId: null,
    stoppedByLimit: false,
    recordedMs: 0,
  };

  function chooseMimeType() {
    if (typeof MediaRecorder === "undefined") {
      return "";
    }
    if (typeof MediaRecorder.isTypeSupported !== "function") {
      return "";
    }
    return (
      MIME_CANDIDATES.find((candidate) =>
        MediaRecorder.isTypeSupported(candidate)
      ) || ""
    );
  }

  function extensionForMime(mimeType) {
    if (mimeType.includes("ogg")) {
      return "ogg";
    }
    if (mimeType.includes("mp4") || mimeType.includes("m4a")) {
      return "m4a";
    }
    return "webm";
  }

  function formatBytes(bytes) {
    if (bytes < 1024) {
      return `${bytes} B`;
    }
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatElapsed(milliseconds) {
    const totalTenths = Math.floor(Math.max(0, milliseconds) / 100);
    const minutes = Math.floor(totalTenths / 600);
    const secondsTenths = totalTenths % 600;
    const seconds = Math.floor(secondsTenths / 10);
    const tenths = secondsTenths % 10;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${tenths}`;
  }

  function setStatus(text, tone) {
    if (elements.statusText) {
      elements.statusText.textContent = text;
    }
    if (elements.statusBadge) {
      elements.statusBadge.textContent =
        tone === "recording"
          ? "Recording"
          : tone === "working"
            ? "Working"
            : tone === "success"
              ? "Ready"
              : tone === "error"
                ? "Error"
                : "Idle";
      elements.statusBadge.dataset.tone = tone || "idle";
    }
  }

  function setAppState(nextState) {
    if (elements.app) {
      elements.app.dataset.state = nextState;
    }
    const busy = ACTIVE_PHASES.has(nextState);
    if (elements.startButton) {
      elements.startButton.disabled = busy;
    }
    if (elements.stopButton) {
      elements.stopButton.disabled = nextState !== "recording";
    }
    if (elements.pipelineState) {
      elements.pipelineState.textContent =
        nextState === "requesting"
          ? "请求权限"
          : nextState === "recording"
            ? "录音中"
            : nextState === "transcribing"
              ? "识别中"
              : nextState === "success"
                ? "完成"
                : nextState === "error"
                  ? "失败"
                  : "等待操作";
    }
    if (elements.stepCapture) {
      elements.stepCapture.dataset.state =
        nextState === "recording"
          ? "active"
          : nextState === "success" || nextState === "transcribing"
            ? "done"
            : nextState === "error"
              ? "error"
              : "";
    }
  }

  function setPhase(nextPhase) {
    state.phase = nextPhase;
    state.recording = nextPhase === "recording";
    setAppState(nextPhase);
  }

  function showError(message) {
    if (elements.errorMessage) {
      elements.errorMessage.textContent = message;
    }
    if (elements.errorPanel) {
      elements.errorPanel.hidden = false;
    }
    setPhase("error");
  }

  function clearError() {
    if (elements.errorPanel) {
      elements.errorPanel.hidden = true;
    }
    if (elements.errorMessage) {
      elements.errorMessage.textContent = "";
    }
    if (elements.permissionNote) {
      elements.permissionNote.hidden = true;
    }
  }

  function describeMediaError(error) {
    const name = error && error.name ? error.name : "UnknownError";
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      return "麦克风权限被拒绝。请允许本站访问麦克风后重试。";
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return "未检测到可用麦克风，请连接麦克风后重试。";
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return "麦克风无法读取，可能被其他程序占用。";
    }
    if (name === "SecurityError") {
      return "当前页面不是安全上下文，请通过 localhost 访问。";
    }
    return `录音失败：${error && error.message ? error.message : name}`;
  }

  function releaseStream() {
    if (state.stream) {
      state.stream.getTracks().forEach((track) => track.stop());
      state.stream = null;
    }
  }

  function stopTimer() {
    if (state.timerId !== null) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function updateRecordingTimer() {
    if (state.phase !== "recording" || !state.startTimeMs) {
      return;
    }
    const elapsed = Date.now() - state.startTimeMs;
    const capped = Math.min(elapsed, MAX_RECORDING_MS);
    state.recordedMs = capped;
    if (elements.recordingTimer) {
      elements.recordingTimer.textContent = formatElapsed(capped);
    }
    if (elapsed >= MAX_RECORDING_MS) {
      state.stoppedByLimit = true;
      stopRecording("limit");
    }
  }

  function startTimer() {
    stopTimer();
    state.startTimeMs = Date.now();
    updateRecordingTimer();
    state.timerId = setInterval(updateRecordingTimer, TIMER_INTERVAL_MS);
  }

  function handleRecorderStop() {
    stopTimer();
    state.recording = false;
    const mimeType = state.mimeType || "audio/webm";
    const blob = new Blob(state.chunks, { type: mimeType });
    state.chunks = [];
    releaseStream();

    if (!state.recordedMs && state.startTimeMs) {
      state.recordedMs = Math.min(
        Date.now() - state.startTimeMs,
        MAX_RECORDING_MS
      );
    }
    if (elements.recordingTimer) {
      elements.recordingTimer.textContent = formatElapsed(state.recordedMs);
    }

    if (blob.size === 0) {
      setStatus("没有录到音频", "error");
      showError("没有录到音频，请检查麦克风后重试。");
      return;
    }

    state.lastRecording = {
      blob,
      mimeType,
      extension: extensionForMime(mimeType),
      size: blob.size,
      durationMs: state.recordedMs,
      stoppedByLimit: state.stoppedByLimit,
    };
    window.__lastRecording = state.lastRecording;
    setPhase("success");
    setStatus(
      state.stoppedByLimit
        ? `已达到 60 秒上限并自动停止；录音 ${formatElapsed(state.recordedMs)}，等待识别。`
        : `录音完成（${formatElapsed(state.recordedMs)}，${formatBytes(blob.size)}），等待识别。`,
      "success"
    );
  }

  async function startRecording() {
    if (ACTIVE_PHASES.has(state.phase)) {
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("当前浏览器不支持麦克风录音。");
      setStatus("浏览器不支持录音", "error");
      return;
    }
    if (typeof MediaRecorder === "undefined") {
      showError("当前浏览器不支持 MediaRecorder。");
      setStatus("浏览器不支持录音", "error");
      return;
    }

    clearError();
    state.stoppedByLimit = false;
    state.recordedMs = 0;
    state.startTimeMs = 0;
    if (elements.recordingTimer) {
      elements.recordingTimer.textContent = formatElapsed(0);
    }
    setPhase("requesting");
    setStatus("正在请求麦克风权限…", "working");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      state.stream = stream;
      state.chunks = [];

      const selectedMimeType = chooseMimeType();
      const recorder = selectedMimeType
        ? new MediaRecorder(stream, { mimeType: selectedMimeType })
        : new MediaRecorder(stream);
      state.recorder = recorder;
      state.mimeType =
        recorder.mimeType || selectedMimeType || "audio/webm";

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data && event.data.size > 0) {
          state.chunks.push(event.data);
        }
      });
      recorder.addEventListener("stop", handleRecorderStop);
      recorder.addEventListener("error", (event) => {
        stopTimer();
        releaseStream();
        const error = event.error || new Error("MediaRecorder error");
        setStatus("录音失败", "error");
        showError(describeMediaError(error));
      });

      recorder.start(1000);
      setPhase("recording");
      startTimer();
      setStatus("录音中…点击 Stop Recording 结束。", "recording");
    } catch (error) {
      stopTimer();
      releaseStream();
      setStatus("麦克风启动失败", "error");
      if (
        error &&
        (error.name === "NotAllowedError" ||
          error.name === "PermissionDeniedError") &&
        elements.permissionNote
      ) {
        elements.permissionNote.hidden = false;
      }
      showError(describeMediaError(error));
    }
  }

  function stopRecording(reason) {
    if (!state.recorder || state.recorder.state === "inactive") {
      return;
    }
    if (reason !== "limit") {
      updateRecordingTimer();
    }
    if (reason === "limit") {
      state.stoppedByLimit = true;
      state.recordedMs = MAX_RECORDING_MS;
      if (elements.recordingTimer) {
        elements.recordingTimer.textContent = formatElapsed(MAX_RECORDING_MS);
      }
      setStatus("已达到 60 秒上限，正在结束录音…", "working");
    } else {
      setStatus("正在结束录音…", "working");
    }
    stopTimer();
    setPhase("transcribing");
    try {
      state.recorder.stop();
    } catch (error) {
      releaseStream();
      setStatus("录音结束失败", "error");
      showError(describeMediaError(error));
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (state.phase !== "recording") {
      return;
    }
    updateRecordingTimer();
    if (
      state.phase === "recording" &&
      state.startTimeMs &&
      Date.now() - state.startTimeMs >= MAX_RECORDING_MS
    ) {
      state.stoppedByLimit = true;
      stopRecording("limit");
    }
  });

  window.addEventListener("pagehide", stopTimer);

  if (elements.startButton) {
    elements.startButton.addEventListener("click", startRecording);
  }
  if (elements.stopButton) {
    elements.stopButton.addEventListener("click", () => stopRecording("manual"));
  }

  // Exposed for upload/timer tasks and browser smoke tests.
  window.recordingApp = {
    chooseMimeType,
    formatElapsed,
    startRecording,
    stopRecording,
    maxRecordingMs: MAX_RECORDING_MS,
    getState: () => ({
      phase: state.phase,
      recording: state.recording,
      mimeType: state.mimeType,
      lastRecording: state.lastRecording,
      recorderState: state.recorder ? state.recorder.state : "inactive",
      elapsedMs: state.startTimeMs ? Date.now() - state.startTimeMs : 0,
      recordedMs: state.recordedMs,
      stoppedByLimit: state.stoppedByLimit,
    }),
  };
})();

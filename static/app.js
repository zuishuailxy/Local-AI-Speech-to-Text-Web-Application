(function () {
  "use strict";

  const MIME_CANDIDATES = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
  ];

  const elements = {
    app: document.getElementById("app"),
    startButton: document.getElementById("start-button"),
    stopButton: document.getElementById("stop-button"),
    statusBadge: document.getElementById("status-badge"),
    statusText: document.getElementById("status-text"),
    permissionNote: document.getElementById("permission-note"),
    errorPanel: document.getElementById("error-panel"),
    errorMessage: document.getElementById("error-message"),
  };

  const state = {
    recording: false,
    stream: null,
    recorder: null,
    chunks: [],
    mimeType: null,
    lastRecording: null,
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
  }

  function showError(message) {
    if (elements.errorMessage) {
      elements.errorMessage.textContent = message;
    }
    if (elements.errorPanel) {
      elements.errorPanel.hidden = false;
    }
    setAppState("error");
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

  function resetRecordingControls() {
    state.recording = false;
    if (elements.startButton) {
      elements.startButton.disabled = false;
    }
    if (elements.stopButton) {
      elements.stopButton.disabled = true;
    }
  }

  function handleRecorderStop() {
    state.recording = false;
    const mimeType = state.mimeType || "audio/webm";
    const blob = new Blob(state.chunks, { type: mimeType });
    state.chunks = [];
    releaseStream();
    resetRecordingControls();

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
    };
    window.__lastRecording = state.lastRecording;
    setAppState("idle");
    setStatus(`录音完成（${formatBytes(blob.size)}），等待识别。`, "success");
  }

  async function startRecording() {
    if (state.recording) {
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
    setStatus("正在请求麦克风权限…", "working");
    if (elements.startButton) {
      elements.startButton.disabled = true;
    }

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
        releaseStream();
        resetRecordingControls();
        const error = event.error || new Error("MediaRecorder error");
        showError(describeMediaError(error));
        setStatus("录音失败", "error");
      });

      recorder.start(1000);
      state.recording = true;
      setAppState("recording");
      setStatus("录音中…点击 Stop Recording 结束。", "recording");
      if (elements.stopButton) {
        elements.stopButton.disabled = false;
      }
    } catch (error) {
      releaseStream();
      resetRecordingControls();
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

  function stopRecording() {
    if (!state.recorder || state.recorder.state === "inactive") {
      return;
    }
    setStatus("正在结束录音…", "working");
    if (elements.stopButton) {
      elements.stopButton.disabled = true;
    }
    state.recorder.stop();
    setAppState("transcribing");
  }

  if (elements.startButton) {
    elements.startButton.addEventListener("click", startRecording);
  }
  if (elements.stopButton) {
    elements.stopButton.addEventListener("click", stopRecording);
  }

  // Exposed for the upload/timer tasks and for browser smoke tests.
  window.recordingApp = {
    chooseMimeType,
    startRecording,
    stopRecording,
    getState: () => ({
      recording: state.recording,
      mimeType: state.mimeType,
      lastRecording: state.lastRecording,
      recorderState: state.recorder ? state.recorder.state : "inactive",
    }),
  };
})();

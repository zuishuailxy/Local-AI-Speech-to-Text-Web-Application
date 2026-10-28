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
  const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
  const ALLOWED_UPLOAD_EXTENSIONS = new Set([
    ".wav",
    ".webm",
    ".ogg",
    ".oga",
    ".mp3",
    ".m4a",
    ".mp4",
    ".flac",
  ]);
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
    fileInput: document.getElementById("file-input"),
    uploadButton: document.getElementById("upload-button"),
    fileName: document.getElementById("file-name"),
    languageSelect: document.getElementById("language-select"),
    processingTimer: document.getElementById("processing-timer"),
    permissionNote: document.getElementById("permission-note"),
    errorPanel: document.getElementById("error-panel"),
    errorMessage: document.getElementById("error-message"),
    retryButton: document.getElementById("retry-button"),
    dismissErrorButton: document.getElementById("dismiss-error-button"),
    resultPanel: document.getElementById("result-panel"),
    resultPlaceholder: document.getElementById("result-placeholder"),
    resultText: document.getElementById("result-text"),
    resultLanguage: document.getElementById("result-language"),
    resultDuration: document.getElementById("result-duration"),
    resultProcessing: document.getElementById("result-processing"),
    copyButton: document.getElementById("copy-button"),
    audioPreview: document.getElementById("audio-preview"),
    stepUpload: document.getElementById("step-upload"),
    stepDecode: document.getElementById("step-decode"),
    stepInfer: document.getElementById("step-infer"),
    stepResult: document.getElementById("step-result"),
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
    recordingFailed: false,
    selectedFile: null,
    lastSubmission: null,
    requestInFlight: false,
    processingTimerId: null,
    processingStartMs: 0,
    lastResult: null,
    previewUrl: null,
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
    if (elements.fileInput) {
      elements.fileInput.disabled = busy;
    }
    if (elements.uploadButton) {
      elements.uploadButton.disabled = busy || !state.selectedFile;
    }
    if (elements.languageSelect) {
      elements.languageSelect.disabled = busy;
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
    if (name === "OverconstrainedError" || name === "ConstraintNotSatisfiedError") {
      return "麦克风不支持所需的音频参数，请更换设备或浏览器后重试。";
    }
    if (name === "AbortError") {
      return "麦克风启动被中止，请关闭占用设备的程序后重试。";
    }
    return `录音失败：${error && error.message ? error.message : name}`;
  }

  function extensionForName(name) {
    const dot = name.lastIndexOf(".");
    return dot >= 0 ? name.slice(dot).toLowerCase() : "";
  }

  function setFileMessage(text) {
    if (elements.fileName) {
      elements.fileName.textContent = text;
    }
  }

  function selectFile(file) {
    if (!file) {
      state.selectedFile = null;
      if (elements.uploadButton) {
        elements.uploadButton.disabled = true;
      }
      setFileMessage("尚未选择文件。");
      return false;
    }

    const extension = extensionForName(file.name);
    if (!ALLOWED_UPLOAD_EXTENSIONS.has(extension)) {
      state.selectedFile = null;
      if (elements.uploadButton) {
        elements.uploadButton.disabled = true;
      }
      setFileMessage("未选择有效文件。");
      setStatus("文件格式不支持", "error");
      showError("不支持该文件格式，请上传 WAV、WebM、OGG、MP3、M4A、MP4 或 FLAC。");
      return false;
    }
    if (file.size === 0) {
      state.selectedFile = null;
      if (elements.uploadButton) {
        elements.uploadButton.disabled = true;
      }
      setFileMessage("未选择有效文件。");
      setStatus("文件为空", "error");
      showError("上传文件为空，请选择包含语音的音频文件。");
      return false;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      state.selectedFile = null;
      if (elements.uploadButton) {
        elements.uploadButton.disabled = true;
      }
      setFileMessage("未选择有效文件。");
      setStatus("文件超过大小限制", "error");
      showError("上传文件超过 10 MB 限制，请选择更短的音频。");
      return false;
    }

    state.selectedFile = file;
    clearError();
    if (state.phase === "error") {
      setPhase("idle");
    }
    if (elements.uploadButton) {
      elements.uploadButton.disabled = false;
    }
    setFileMessage(`${file.name} · ${formatBytes(file.size)}`);
    setStatus("已选择音频文件，点击 Upload & Transcribe 开始识别。", "idle");
    return true;
  }

  function handleFileSelection(event) {
    const file = event.target.files && event.target.files[0];
    const accepted = selectFile(file);
    if (!accepted && elements.fileInput) {
      elements.fileInput.value = "";
    }
  }

  function formatSeconds(milliseconds) {
    return `${(Math.max(0, milliseconds) / 1000).toFixed(1)} s`;
  }

  function setPipelineStep(element, stateName) {
    if (element) {
      element.dataset.state = stateName || "";
    }
  }

  function resetPipeline() {
    [
      elements.stepCapture,
      elements.stepUpload,
      elements.stepDecode,
      elements.stepInfer,
      elements.stepResult,
    ].forEach((element) => setPipelineStep(element, ""));
  }

  function updateProcessingTimer() {
    if (!state.processingStartMs) {
      return;
    }
    if (elements.processingTimer) {
      elements.processingTimer.textContent = formatSeconds(
        Date.now() - state.processingStartMs
      );
    }
  }

  function startProcessingTimer() {
    stopProcessingTimer();
    state.processingStartMs = Date.now();
    updateProcessingTimer();
    state.processingTimerId = setInterval(updateProcessingTimer, 100);
  }

  function stopProcessingTimer() {
    if (state.processingTimerId !== null) {
      clearInterval(state.processingTimerId);
      state.processingTimerId = null;
    }
  }

  function revokePreview() {
    if (state.previewUrl) {
      URL.revokeObjectURL(state.previewUrl);
      state.previewUrl = null;
    }
    if (elements.audioPreview) {
      elements.audioPreview.pause();
      elements.audioPreview.removeAttribute("src");
      elements.audioPreview.hidden = true;
    }
  }

  function resetResult() {
    revokePreview();
    if (elements.resultPanel) {
      elements.resultPanel.dataset.resultState = "empty";
    }
    if (elements.resultPlaceholder) {
      elements.resultPlaceholder.hidden = false;
      elements.resultPlaceholder.textContent = "识别完成后，文本会显示在这里。";
    }
    if (elements.resultText) {
      elements.resultText.hidden = true;
      elements.resultText.textContent = "";
    }
    if (elements.resultLanguage) {
      elements.resultLanguage.textContent = "—";
    }
    if (elements.resultDuration) {
      elements.resultDuration.textContent = "—";
    }
    if (elements.resultProcessing) {
      elements.resultProcessing.textContent = "—";
    }
    if (elements.copyButton) {
      elements.copyButton.disabled = true;
    }
    state.lastResult = null;
  }

  function languageLabel(language) {
    return language === "zh" ? "中文（zh）" : language === "en" ? "English（en）" : language || "—";
  }

  function showResult(payload, blob) {
    stopProcessingTimer();
    if (
      !payload ||
      typeof payload.text !== "string" ||
      typeof payload.language !== "string" ||
      typeof payload.duration_seconds !== "number" ||
      typeof payload.processing_seconds !== "number"
    ) {
      throw new Error("后端返回了无法识别的响应格式。");
    }

    state.lastResult = payload;
    window.__lastResult = payload;
    if (elements.resultPanel) {
      elements.resultPanel.dataset.resultState = payload.text ? "success" : "empty";
    }
    if (elements.resultLanguage) {
      elements.resultLanguage.textContent = languageLabel(payload.language);
    }
    if (elements.resultDuration) {
      elements.resultDuration.textContent = `${payload.duration_seconds.toFixed(1)} s`;
    }
    if (elements.resultProcessing) {
      elements.resultProcessing.textContent = `${payload.processing_seconds.toFixed(2)} s`;
    }
    if (elements.processingTimer) {
      elements.processingTimer.textContent = `${payload.processing_seconds.toFixed(1)} s`;
    }

    if (payload.text) {
      if (elements.resultPlaceholder) {
        elements.resultPlaceholder.hidden = true;
      }
      if (elements.resultText) {
        elements.resultText.hidden = false;
        elements.resultText.textContent = payload.text;
      }
    } else {
      if (elements.resultText) {
        elements.resultText.hidden = true;
        elements.resultText.textContent = "";
      }
      if (elements.resultPlaceholder) {
        elements.resultPlaceholder.hidden = false;
        elements.resultPlaceholder.textContent =
          "未检测到可识别语音，请换一段更清晰、包含说话的音频。";
      }
    }

    if (blob && elements.audioPreview) {
      revokePreview();
      state.previewUrl = URL.createObjectURL(blob);
      elements.audioPreview.src = state.previewUrl;
      elements.audioPreview.hidden = false;
    }

    resetPipeline();
    [
      elements.stepCapture,
      elements.stepUpload,
      elements.stepDecode,
      elements.stepInfer,
      elements.stepResult,
    ].forEach((element) => setPipelineStep(element, "done"));
    setPhase("success");
    setStatus(
      payload.text ? "识别完成。" : "识别完成，未检测到可识别语音。",
      "success"
    );
  }

  async function parseApiError(response) {
    let payload = null;
    try {
      payload = await response.json();
    } catch (_) {
      // Fall back to the HTTP status below.
    }
    const detail = payload && payload.detail ? payload.detail : `HTTP ${response.status}`;
    const code = payload && payload.code ? ` (${payload.code})` : "";
    return `${detail}${code}`;
  }

  async function submitAudio(blob, filename, note = "") {
    if (state.requestInFlight) {
      return;
    }
    if (!blob || blob.size === 0) {
      showError("没有可识别的音频，请重新录音或选择文件。");
      setStatus("没有可识别的音频", "error");
      return;
    }
    if (blob.size > MAX_UPLOAD_BYTES) {
      showError("上传文件超过 10 MB 限制，请选择更短的音频。");
      setStatus("文件超过大小限制", "error");
      return;
    }

    state.requestInFlight = true;
    state.lastSubmission = { blob, filename, note };
    clearError();
    resetResult();
    resetPipeline();
    setPipelineStep(elements.stepCapture, "done");
    setPipelineStep(elements.stepUpload, "active");
    setPhase("transcribing");
    setStatus(`${note}正在上传并识别…`, "working");
    startProcessingTimer();

    const formData = new FormData();
    formData.append("file", blob, filename);
    formData.append("language", elements.languageSelect ? elements.languageSelect.value : "zh");

    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await parseApiError(response));
      }
      const payload = await response.json();
      setPipelineStep(elements.stepUpload, "done");
      setPipelineStep(elements.stepDecode, "done");
      setPipelineStep(elements.stepInfer, "done");
      setPipelineStep(elements.stepResult, "active");
      showResult(payload, blob);
      if (note) {
        setStatus(`${note}识别完成。`, "success");
      }
    } catch (error) {
      stopProcessingTimer();
      setPipelineStep(elements.stepUpload, "error");
      setStatus("识别失败", "error");
      showError(
        `识别失败：${error && error.message ? error.message : "无法连接后端，请确认服务仍在运行。"}`
      );
    } finally {
      state.requestInFlight = false;
      if (state.phase !== "error") {
        // Re-enable the actions that were disabled for the request.
        setAppState(state.phase);
      }
    }
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
    if (state.recordingFailed) {
      state.chunks = [];
      state.recordingFailed = false;
      releaseStream();
      return;
    }
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

    const filename = `recording-${Date.now()}.${state.lastRecording.extension}`;
    const note = state.stoppedByLimit ? "已达到 60 秒上限；" : "";
    void submitAudio(blob, filename, note);
  }

  async function startRecording() {
    if (ACTIVE_PHASES.has(state.phase)) {
      return;
    }
    if (typeof window.isSecureContext === "boolean" && !window.isSecureContext) {
      showError("当前页面不是安全上下文，请通过 http://127.0.0.1:8000 或 localhost 访问。");
      setStatus("非安全上下文，无法录音", "error");
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("当前浏览器不支持麦克风录音，请使用最新 Chrome 或 Edge。");
      setStatus("浏览器不支持录音", "error");
      return;
    }
    if (typeof MediaRecorder === "undefined") {
      showError("当前浏览器不支持 MediaRecorder，请使用最新 Chrome 或 Edge。");
      setStatus("浏览器不支持录音", "error");
      return;
    }

    clearError();
    state.lastSubmission = null;
    state.selectedFile = null;
    if (elements.fileInput) {
      elements.fileInput.value = "";
    }
    if (elements.uploadButton) {
      elements.uploadButton.disabled = true;
    }
    if (elements.fileName) {
      elements.fileName.textContent = "尚未选择文件。";
    }
    state.stoppedByLimit = false;
    state.recordingFailed = false;
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
        state.recordingFailed = true;
        state.chunks = [];
        releaseStream();
        const error = event.error || new Error("MediaRecorder error");
        setStatus("录音失败", "error");
        showError(describeMediaError(error));
        try {
          if (recorder.state !== "inactive") {
            recorder.stop();
          }
        } catch (_) {
          // The error is already surfaced; stop is best-effort.
        }
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
      state.recordingFailed = true;
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

  function dismissError() {
    clearError();
    if (state.phase === "error") {
      setPhase("idle");
      setStatus("准备就绪，可以开始录音或上传音频。", "idle");
    }
  }

  function retryLastAction() {
    clearError();
    if (state.lastSubmission) {
      void submitAudio(
        state.lastSubmission.blob,
        state.lastSubmission.filename,
        state.lastSubmission.note || ""
      );
      return;
    }
    startRecording();
  }

  if (elements.startButton) {
    elements.startButton.addEventListener("click", startRecording);
  }
  if (elements.stopButton) {
    elements.stopButton.addEventListener("click", () => stopRecording("manual"));
  }
  if (elements.retryButton) {
    elements.retryButton.addEventListener("click", retryLastAction);
  }
  if (elements.uploadButton) {
    elements.uploadButton.addEventListener("click", () => {
      if (state.selectedFile) {
        void submitAudio(state.selectedFile, state.selectedFile.name);
      }
    });
  }
  if (elements.dismissErrorButton) {
    elements.dismissErrorButton.addEventListener("click", dismissError);
  }
  if (elements.fileInput) {
    elements.fileInput.addEventListener("change", handleFileSelection);
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
      requestInFlight: state.requestInFlight,
      lastResult: state.lastResult,
      selectedFile: state.selectedFile
        ? {
            name: state.selectedFile.name,
            size: state.selectedFile.size,
            type: state.selectedFile.type,
          }
        : null,
    }),
    getSelectedFile: () => state.selectedFile,
    selectFile,
  };
})();

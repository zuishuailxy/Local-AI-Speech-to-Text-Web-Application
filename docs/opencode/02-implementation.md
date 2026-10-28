# 阶段二：功能开发与集成

> 状态：P1/P2/P3/P4/P5 已完成；P6 待进行。
> 本文是 OpenCode 实现阶段的关键步骤记录，不是完整对话；会随 P6 继续补充。
> 会话：`ses_e838f4101ffet1mEwSYEGuuSMK`（OpenCode Desktop，`deepseek-flash` high）
> 日期：2026-10-27

## 1. 阶段范围

本阶段从“只有计划和任务清单”推进到可启动、可上传、可走通识别接口的 FastAPI 应用：

- Python 3.12 虚拟环境与依赖锁定；
- 目录骨架与 `.gitignore`；
- 配置模块；
- 应用工厂、`GET /health`、`GET /`、静态资源挂载；
- 统一错误模型与异常处理器；
- pytest 标记、FakeTranscriber、WAV/WebM fixture、测试隔离；
- GitHub Actions `windows-latest` CI 骨架；
- 上传格式/大小/时长校验、PyAV 解码、临时文件清理；
- `POST /api/transcribe` 契约与 FakeTranscriber 联调。

## 2. 关键用户指令

> 你只需要提交，我手动来 push。现在开始实施 T0.5，T0.6

> 已经 push，验证 T1.8。先做配置模块

> Windows job 为绿色了，继续开发 T1.4 。注意完成一个核心模块之后都要写单测

> 没问题 继续推进 T1.5 和 1.6

> 我现在把仓库修改为 public 了。你能读取到结果吗？

这些指令确定了三个工作方式：

1. 每个核心模块必须同时提交单测；
2. Windows 实机不可用，以 GitHub Actions 作为兼容性验证；
3. 代理可以提交和推送，但默认尊重“先本地验证、再推送”的节奏。

## 3. 实施步骤与结果

### 3.1 T1.1 目录骨架

- 创建 `app/`、`static/`、`scripts/`、`tests/`、`samples/`、`docs/evidence/`、`.github/workflows/`。
- 添加 `app/__init__.py`、`app/api/__init__.py`、`app/services/__init__.py`。
- `.gitignore` 排除 `.venv/`、`models/`、`.wheelhouse-check/`、缓存、日志、`.DS_Store`。
- 添加 `.python-version` = 3.12。

### 3.2 T1.2 Python 3.12 与依赖锁定

问题：本机系统 `python3` 是 3.9，Homebrew 当前不可用；直接用系统 Python 会偏离题目要求。

处理：

- 使用 uv 管理的 CPython 3.12.13 创建 `.venv`；
- 安装并冻结 41 个精确版本到 `requirements.txt`；
- `pip download --platform win_amd64 --python-version 3.12 --abi cp312 --only-binary=:all:` 成功下载 41 个 Windows wheel；
- 在全新临时 venv 中按 requirements 复装并导入关键模块；
- `pip check` 无冲突。

关键版本：

```text
fastapi 0.162.0
uvicorn 0.54.0
faster-whisper 1.2.1
ctranslate2 4.8.4
av 19.0.2
onnxruntime 1.31.1
websockets 17.3
pytest 9.1.1
httpx 0.28.1
```

证据：`docs/evidence/t1.2-environment.txt`、`windows-wheels.txt`。

### 3.3 T1.3 配置模块

- 新增 `app/config.py`，frozen dataclass `Settings`。
- 路径解析基于项目根，兼容 Windows/POSIX。
- 校验布尔值和正整数，非法值 fail fast 并指出环境变量名。
- 支持 `environ`/`project_root` 注入，测试不污染真实环境。
- 新增 `tests/test_config.py`：21 个测试。

### 3.4 T1.4 应用工厂与健康检查

- `app/main.py` 提供 `create_app(transcriber=None)`。
- `app.state.transcriber` 注入，导入时不加载模型。
- `GET /health` 精确返回 `{"status":"ok"}`。
- `GET /` 返回 `static/index.html`，`/static` 挂载。
- 新增 `tests/test_health.py`、`tests/test_app_factory.py`；实际 uvicorn 启动验证 `/health` 与 `/` 均为 200。
- 新增 `static/index.html` 占位页。

### 3.5 T1.5 统一错误模型

- `app/errors.py`：
  - `ApiError`；
  - `ModelUnavailableError` (503)；
  - `TranscriptionFailedError` (500)；
  - `InvalidAudioError` (400)。
- 统一 JSON：`{"detail": "...", "code": "..."}`。
- 处理 400/404/405/413/415/422/500/503。
- 未捕获异常返回通用 `internal_error`，不泄漏堆栈或请求内容。
- `tests/test_errors.py`：10 个测试。

### 3.6 T1.6 pytest 与测试隔离

- `pytest.ini` 注册 `real_model`、`e2e`，默认排除。
- `tests/conftest.py` 提供：
  - `FakeTranscriber` / `failing_transcriber`；
  - 1 秒 16 kHz WAV、静音 WAV、损坏音频；
  - `TestClient` 与 app fixture。
- `tests/test_fixtures.py` 验证 fixture 与隔离。
- 临时 probe 验证：
  - 默认 `pytest -q`：47 passed，probe deselected；
  - `pytest -q -m real_model`：probe 单独运行。
- 未加载模型、未下载权重、未访问麦克风。

### 3.7 T1.8 Windows CI

- `.github/workflows/windows.yml`：`windows-latest` + Python 3.12；安装依赖、`pip check`、导入检查、`pytest -q`。
- 初次 green run（用户确认）；公开仓库后 API 复核 run `40483713787`：
  - commit `fc8e7f9`；
  - 所有 step success；
  - run URL 记录在 `docs/evidence/t1.8-windows-ci.txt`。
- CI 只证明 Windows Server 上的安装/测试，不代表 Windows 11 实机麦克风已通过；该限制继续保留。

## 4. P2 音频处理与识别接口

### 4.1 T2.1 上传参数与格式校验

- 新增 `app/services/audio.py`：语言归一化、扩展名白名单、空文件、WAV 头校验。
- 扩展名：`wav/webm/ogg/oga/mp3/m4a/mp4/flac`；MIME 不作为可信依据。
- 新增 `EmptyFileError`、`UnsupportedFormatError`、`InvalidLanguageError`。
- 伪 WAV（无 RIFF/WAVE 头）在进入解码前返回 400 `invalid_audio`；其他容器由解码器验证。

### 4.2 T2.2 流式写入与 10 MB 上限

- `save_upload_to_temp` 以 1 MiB 分块写入 `TemporaryDirectory`，不在内存中拼完整文件。
- 声明大小预检 + 实际字节计数双重限制。
- `Content-Length` 中间件在 `/api/transcribe` 路由前拒绝明显超大请求，允许 1 MiB multipart overhead。
- `FileTooLargeError` → 413 `file_too_large`；失败路径清理临时目录。

### 4.3 T2.3 PyAV 解码与时长上限

- `decode_audio` 使用 PyAV `AudioResampler(format="flt", layout="mono", rate=16000)`。
- 先检查容器 duration，再按实际样本数执行 `MAX_AUDIO_SECONDS` 二次限制。
- 1 秒/5 秒 WAV、静音 WAV、损坏字节、0 帧、超长 WAV 均有测试。
- WebM/Opus fixture 解码通过；系统 ffmpeg 存在但不可执行，PyAV wheel 不依赖它。
- `AudioTooLongError` → 400 `audio_too_long`。

### 4.4 T2.4 清理边界与错误码

- `process_audio_upload` 统一 `save → decode → finally cleanup`。
- 成功、解码失败、超时长、超大小路径均验证临时目录为空。
- 容器与临时文件均通过 `with` 关闭；为 Windows 删除句柄提供保证。

### 4.5 T2.5 音频验收矩阵

- 参数化覆盖 normal/silent/empty/corrupt/too_long，每条路径检查临时目录。
- 静音 = 16000 个零采样，不是空文件；后续 VAD/ASR 返回空文本。
- G1（测试隔离 + 音频矩阵）通过。

### 4.6 T2.6 浏览器录音格式

- `tests/fixtures/sample.webm`：1 秒 WebM/Opus，由项目生成的 WAV 经 PyAV/libopus 转码。
- 断言容器、codec=opus、时长约 1s、解码为 16 kHz mono float32。
- `PATH` 排除系统 ffmpeg 后仍通过，证明运行期只需 PyAV wheel。
- 真实 Chrome/Edge 录音仍待 T6.8/T6.11 手动验证。

### 4.7 T2.7 识别接口与 FakeTranscriber

- `app/services/transcriber.py`：`Transcriber` Protocol、`TranscriptionResult`、`FakeTranscriber`。
- `app/schemas.py`：四字段响应模型。
- `POST /api/transcribe`：语言校验 → `process_audio_upload` → `run_in_threadpool` 调用引擎。
- 成功响应：

```json
{"text":"...","language":"zh","duration_seconds":1.0,"processing_seconds":0.02}
```

- `duration_seconds` 来自实际解码；`processing_seconds` 从路由开始计时，包含解码与模型调用。
- 无 transcriber 时返回 503；真实 faster-whisper 尚未接入（P3）。

### 4.8 T2.8 错误路径与重试

- Fake 抛 `ModelUnavailableError` → 503；普通异常 → 500 `transcription_failed`；空文本 → 200。
- 500/503/400 后同一客户端再次请求均成功，验证 API 无状态、可重试。
- 普通异常原文不外泄；错误响应保持 `{detail, code}`。

## 5. P3 真实模型集成

### 5.1 T3.1 协议、结果对象与 Fake

- `Transcriber` Protocol、`TranscriptionResult(text, language)`。
- FakeTranscriber 支持文本、持久异常、异常序列恢复、`delay_seconds`、调用记录。
- 7 个测试；导入模块不加载 faster-whisper。

### 5.2 T3.2 faster-whisper 适配器

- `WhisperTranscriber`：惰性加载、本地 ASR_MODEL_PATH、CPU/int8、threads/beam/VAD 来自 Settings。
- 单锁串行化加载与推理；并发首请求只加载一次。
- 缺失路径/加载失败 → `ModelUnavailableError`；推理失败 → `TranscriptionFailedError`。
- 9 个单元测试，含 `model_load_seconds=` 日志断言。

### 5.3 T3.3 模型下载脚本

- `scripts/download_model.py` 支持 HuggingFace 与 ModelScope。
- 校验 `model.bin/config.json/tokenizer.json/vocabulary.*`；
- 下载失败提供镜像/手动放置提示；`models/` 不入 Git。
- 10 个脚本测试。

### 5.4 T3.4 CLI 冒烟

- `scripts/verify_asr.py` 支持中文/英文、`--model-path`、模型缺失提示。
- 修复从 `scripts/` 启动时 `app` 不在 sys.path 的问题。
- 6 个测试；真实中英文 CLI 运行已执行。

### 5.5 T3.5 模型准备

- 因 HuggingFace/hf-mirror 超时，使用 ModelScope 公共源下载 `Systran/faster-whisper-small`。
- 约 468 MB；强制复测下载 25.60 s；M1/16 GB。
- `model.bin` 483,546,902 bytes；SHA-256 `3e3059...d671`。
- 首次真实加载和中英文识别成功；权重未提交。

### 5.6 T3.6 真实基线（G2）

- 中文 12s：推理中位数 3.430s，RTF 0.286，CER 0.231。
- 英文 9s：推理中位数 1.608s，RTF 0.179，WER 0.000。
- 模型加载 0.987s；英文准确，中文有同音错误但可辨认。
- 决策：维持 small，不触发 T3.11 SenseVoice 评估。G2 通过。

### 5.7 T3.7 真实 API 接线

- 生产 `app.main:app` 创建 `WhisperTranscriber`，但不加载。
- 首次中文请求 4.456s，第二次 3.484s，英文 1.674s；均 200，文本与 CLI 一致。
- `processing_seconds` 包含解码、首次加载、推理，不含下载。
- 149 tests；`model_load_seconds` 日志由 caplog 覆盖。

### 5.8 T3.8 真实异常与恢复

- 模型缺失：503 `model_unavailable`，`/health` 200。
- 模型损坏：503，服务存活。
- 恢复目录后再次请求 200，失败状态未永久缓存。
- 真实引擎适配器推理异常 → 500，不泄漏原文。
- 150 tests。

### 5.9 T3.9 Mock API 矩阵

- 补齐损坏 WebM、10 MB+1 API 测试。
- 覆盖健康、正常中英文、缺参、非法语言、空/损坏、超大小、不支持格式、超时长、503、500、空文本、重试。
- 152 tests。

### T3.11 状态

未触发：G2 已通过，small 的中英文结果可辨认、RTF 可接受；不进行 SenseVoice 时间盒评估。

## 6. P4 前端页面与浏览器交互

### 6.1 T4.1 页面结构与视觉

- 新增完整 `static/index.html` / `styles.css`。
- 语言、录音、上传、pipeline、结果、错误、本地说明分区。
- 状态样式：idle/requesting/recording/transcribing/success/error。
- 无外部字体/CDN；桌面优先响应式。
- 5 个结构测试；截图 `docs/evidence/t4.1-page.png`。

### 6.2 T4.2 麦克风采集

- Start 点击后才 `getUserMedia`。
- MIME 能力检测：webm/opus → webm → ogg/opus → ogg → mp4。
- `MediaRecorder.start(1000)` 分片；stop 合并 Blob。
- 记录实际 MIME/扩展名/大小；释放 MediaStreamTrack。
- 浏览器实测 `chooseMimeType() = audio/webm;codecs=opus`。
- 自动化环境未完成真实麦克风授权，真实录音待 T6。

### 6.3 T4.3 计时与状态机

- 200ms 计时；60 秒自动 stop；`visibilitychange` 补检。
- `idle → requesting → recording → transcribing → success/error`。
- Start/Stop/文件选择统一由 phase 控制。
- 假 MediaRecorder + 加速虚拟时钟验证 60 秒：recordedMs=60000、timer=01:00.0、stoppedByLimit=true、track 已停止。
- 截图 `docs/evidence/t4.3-auto-stop.png`。

### 6.4 T4.4 录音异常

- 权限拒绝、无设备、设备占用、安全上下文、约束错误、Abort、空 Blob、浏览器不支持均有中文提示。
- 错误面板 + 关闭/重试；错误后 Start 可用。
- `recordingFailed` 防止 error 后 stop 事件覆盖为 success。
- 截图 `docs/evidence/t4.4-error-state.png`。

### 6.5 T4.5 文件选择

- 扩展名/空文件/10 MB 客户端预检。
- 合法文件显示名称+大小并启用 Upload；非法文件清空并禁用。
- Upload 按钮默认 disabled。
- 客户端校验不替代服务端校验。

### 6.6 T4.6 请求与结果

- 录音停止自动提交；文件上传复用 `submitAudio`。
- FormData：file + language；`fetch('/api/transcribe')`。
- 请求期间禁用相关控件，防重复提交；processing timer 100ms。
- 成功展示四字段、音频预览、pipeline 完成、空文本提示。
- 真实浏览器上传中文/英文样本成功：
  - 中文 12s，processing 4.38s；
  - 英文 9s，processing 1.70s。
- 截图 `docs/evidence/t4.6-real-result.png`。

### 6.7 T4.7 复制

- Clipboard API 优先；失败回退 textarea + execCommand。
- “已复制”1.6s 反馈；“复制失败”提示。
- 空文本 disabled；新结果重置。
- 真实浏览器捕获复制文本；强制 Clipboard 失败回退成功。

### 6.8 T4.8 错误重试

- 后端 `detail/code` 展示；fetch TypeError 转为“无法连接后端”。
- 失败保留语言/文件/最近提交；重试优先当前文件，否则最近录音。
- 关闭提示回 idle；成功后 Start/Upload 恢复。
- 浏览器 503→retry 200、网络失败均验证。

### 6.9 T4.9 P4 收尾与可用性

- 5 个可访问性测试：按钮 type、label/for、aria-live、role=alert、音频 aria-label。
- 键盘 Tab 顺序：language select → Start → file input；隐藏控件不参与。
- 页面加载控制台无 error；`getUserMedia` 调用次数：点击前 0、点击后 1。
- 用户修改的 CSS 保留，未被覆盖。
- 证据：`docs/evidence/frontend-smoke.txt`。

## 7. 测试矩阵（P1 + P2 + P3 + P4）

| 模块 | 文件 | 测试数 |
| --- | --- | --- |
| 配置 | `tests/test_config.py` | 22 |
| 错误处理 | `tests/test_errors.py` | 10 |
| fixture/隔离 | `tests/test_fixtures.py` | 8 |
| 健康检查/静态页 | `tests/test_health.py` | 4 |
| 应用工厂 | `tests/test_app_factory.py` | 5 |
| 音频校验/流式/解码/清理 | `tests/test_audio.py` | 42 |
| 语言 | `tests/test_language.py` | 10 |
| `/api/transcribe` 契约/错误/重试 | `tests/test_transcribe_api.py` | 20 |
| Transcriber 协议/Fake | `tests/test_transcriber.py` | 7 |
| WhisperTranscriber 单元 | `tests/test_transcriber_unit.py` | 13 |
| 模型下载脚本 | `tests/test_download_model.py` | 10 |
| CLI 冒烟 | `tests/test_verify_asr.py` | 6 |
| 前端结构 | `tests/test_frontend_structure.py` | 5 |
| 前端录音/上传/请求/复制 | `tests/test_frontend_recording.py` | 11 |
| 前端可访问性 | `tests/test_frontend_accessibility.py` | 5 |
| 质量指标 | `tests/test_metrics.py` | 10 |
| 样本完整性 | `tests/test_samples.py` | 5 |
| 日志/可观测性 | `tests/test_logging.py` | 5 |
| 中文繁转简 | `tests/test_text.py` | 5 |
| 合计 | | **203** |

命令：

```bash
python -m pytest -q
```

结果：`203 passed`。

另有 5 个 `real_model` 与 3 个 `e2e` 用例默认排除。浏览器 E2E 使用 Playwright + 假麦克风 + FakeTranscriber：

```bash
PLAYWRIGHT_CHANNEL=chrome python -m pytest -q -m e2e
```

```text
3 passed
```

Windows CI run `40633358118` 同时通过默认测试、Chromium 安装和浏览器 E2E。

P2/P3/P4 的 Windows CI：`2c55fe5`、`30991d7`、`8f31ebc`、`52b41d4`、`cc9587c`、`8722b7e`、`d5f97d4`、`46c75ed`、`02829b9`、`7c15d98`、`b0a402e`、`9038ef3`、`586da57`、`d90c04a`、`286d9e3`、`3d6d045`、`6565c68`、`4365d89`、`c426b7e`、`fb40bb1`、`a365144`、`b542b9c` 均有 green run；具体 run ID 见证据目录。

## 8. 遇到的问题与处理

1. **默认 Python 3.9**：改用 uv 管理的 CPython 3.12，避免依赖/类型差异。
2. **PyPI 下载超时**：pip 多次 retry 后成功；requirements 已完整锁定。
3. **Windows 实机缺失**：用 GitHub Actions 替代安装/测试验证，并明确记录“非 Windows 11 实机”。
4. **pytest marker 验证**：临时 probe 首次因文件名不符合 `test_*.py` 未被收集；改名后验证默认排除与 `-m real_model` 覆盖均正常。
5. **GitHub 网络间歇性超时**：push/fetch 偶发 `Empty reply from server`；以 `origin/main` 和 run 记录为准。
6. **T2.7 后测试路由冲突**：T2.2 原测试自行添加 `/api/transcribe`，生产路由加入后请求被生产路由处理；改为使用 FakeTranscriber 的合法 multipart 请求验证小请求通过 Content-Length 中间件。
7. **系统 ffmpeg 不可执行**：本机 `/usr/local/bin/ffmpeg` 报 bad CPU type；改用 PyAV 内置库，并在 `PATH=/usr/bin:/bin` 下复跑测试。
8. **WebM fixture 非真实录音**：明确标注为合成 1 秒 Opus，真实浏览器 MediaRecorder 仍在 T6 手动验证。
9. **无模型时的错误优先级**：`/api/transcribe` 先完成文件/语言校验与解码，再检查 transcriber；因此非法文件仍返回 4xx，合法音频在无模型时返回 503。
10. **HuggingFace/镜像不可达**：本机 HF 与 hf-mirror 超时，增加 ModelScope 下载源；实际 461 MiB 权重 25.6s 完成。
11. **faster-whisper 直接传文件与 PyAV 19 不兼容**：`WhisperModel.transcribe(path)` 内部 `av.open(metadata_errors=...)` 报 TypeError；应用统一先用自有 `decode_audio` 解码为 ndarray，再交给模型，因此主流程不受影响。CLI 走 ndarray 路径。
12. **faster-whisper 脚本路径问题**：`python scripts/verify_asr.py` 的 sys.path 默认是 scripts 目录，已显式插入项目根。
13. **中文同音错误**：small 对《再别康桥》片段有近音替换；CER 0.231 在阈值内，记录而不掩盖。
14. **浏览器自动化麦克风权限**：Review 浏览器中 `getUserMedia` 权限请求无法完成，导致页面停在 requesting；没有伪造真实录音。改用注入 MediaRecorder/假 stream 验证计时、状态和停止逻辑，真实麦克风留给 T6。
15. **T4.3 虚拟时钟首次不推进**：初版 Date.now 固定导致计时不动；改为基于 performance.now 的加速时钟后验证 60 秒自动停止。
16. **T4.4 错误后 stop 覆盖**：MediaRecorder error 后仍触发 stop，可能把空 Blob 当成功；增加 `recordingFailed` 守卫。
17. **T4.7 复制兼容性**：Clipboard API 可能被权限拒绝；增加 textarea + execCommand 回退并实测。
18. **用户修改 CSS**：保留用户对 header 宽度/格式的修改，不回退或重写。

## 9. 待补充

- P6 手动验证、断网、Windows 实机/云 VM；
- 交付文档（README 完整版、requirements/design/test-report/ai-development）；
- 条件项 F6 实时识别（受 G5 门禁）。

## 10. 备注

- P3 已下载并验证 small 模型；模型权重保留本地，`models/` 未进入 Git。
- 生产 `app.main:app` 已接入真实引擎；默认 `create_app()` 仍不注入引擎，测试不加载模型。
- P5 已完成：真实模型 5 项、浏览器 E2E 3 项、默认隔离/合规检查、全链路日志；下一步 P6 手动/离线/Windows 验证。

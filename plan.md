# Local AI Speech-to-Text Web Application 实施计划

- 文档版本：v0.2（用户决策已回填）
- 编制日期：2026-10-27
- 输入依据：`面试考核题-v1.md`（v1）
- 当前状态：需求分析与计划编制完成；用户已确认 D1–D5；尚未编写业务代码、未安装依赖、未下载模型
- 配套任务清单：`todo.md`

---

## 0. 结论摘要

1. 技术路线：**FastAPI（Python 3.12）+ 原生 HTML/CSS/JavaScript + faster-whisper（Whisper small，CTranslate2 CPU int8）+ PyAV 解码 + pytest**。
2. 交付策略：先用假模型打通接口、错误处理和前端流程，再接入真实模型并单独验证中英文；所有必做项、真实模型测试、离线验证、Windows 兼容性验证和文档完成后，才开始实时识别（F6）。
3. 时间策略：按 2 个自然日、约 18–22 小时有效工时安排，预留约 15–20% 缓冲。F6 已确认要做，但仍必须先通过 G4 门禁；若 G4 延迟，优先保必做与文档，F6 降级并书面说明。
4. 已确认决策：D1 无 Windows 11 实机；D2 模型 small；D3 本人录制样本；D4 Git 仓库；D5 要做实时识别。Windows 采用 **GitHub Actions `windows-latest` + 浏览器假麦克风**做部分替代验证，真实 Windows 11 桌面/麦克风仍是未验证项。详见 0.1 与 5.3。

### 0.1 决策记录（2026-10-27）

| 编号 | 决策 | 对计划的影响 |
| --- | --- | --- |
| D1 | 目前没有 Windows 11 实机 | 用 CI `windows-latest` 验证安装、启动、API、真实模型上传、浏览器假麦克风；真实 Windows 11 桌面/Edge/麦克风无法完全验证，作为残余风险明确披露 |
| D2 | 模型规模用 **small** | 默认 `faster-whisper` Whisper small，int8 CPU；若实测不达标，按 G2 规则评估备用方案 |
| D3 | 测试音频用**本人录音** | 录制中英文各 5–15 秒清晰语音；不使用 TTS 作为主方案；`reference.txt` 注明本人录制、授权与无敏感信息 |
| D4 | 交付 **Git 仓库** | 分阶段提交、`.gitignore`、tag；OpenCode 会话脱敏后入库；仓库托管平台待确认（影响 Windows CI） |
| D5 | **要做实时识别** | F6 从“可选”提升为“已确认交付目标”，但仍受 G4 门禁；预留约 3–4 小时，失败可回滚 |

> 新增待确认项 D6：Git 仓库托管在 GitHub、GitLab 还是仅本地？只有 GitHub 才能直接使用 `windows-latest` Actions 做 Windows 替代验证；若不能使用，Windows 项只能标为未验证。

---

## 1. 项目目标与验收标准

### 1.1 最终交付成果

| 类别 | 交付物 | 说明 |
| --- | --- | --- |
| 可运行系统 | 源码 + `requirements.txt` | 在 Windows 11 x64 + Python 3.12 下按题目给定命令安装并启动 |
| Web 前端 | `static/` | 麦克风录音、文件上传、语言选择、状态/时长/耗时/文本展示、复制 |
| 后端服务 | `app/` | `/health`、`/api/transcribe`、`/`，本地 ASR 推理 |
| 真实模型验证 | 测试命令 + 结果记录 | 中文、英文各至少一次真实模型识别，区分 Mock 与真实模型 |
| 测试音频 | `samples/chinese.wav`、`samples/english.wav`、`samples/reference.txt` | 每段 5–15 秒，合法授权、无敏感个人信息 |
| 自动化测试 | `tests/` | `python -m pytest -q` 可在无麦克风、无模型下载的情况下完成常规测试 |
| 文档 | `README.md`、`docs/requirements.md`、`docs/design.md`、`docs/test-report.md`、`docs/ai-development.md` | 覆盖安装、模型初始化、运行、测试、设计、实测结果与 AI 开发过程 |
| OpenCode 证据 | `docs/opencode/` | 需求设计、开发集成、测试修复三阶段关键会话导出（脱敏） |
| 版本记录 | Git 仓库或源码压缩包 | 分阶段提交，最终工作区干净、可复现 |

### 1.2 范围界定

#### 必做功能

- F1 浏览器麦克风录音：授权、开始/停止、状态与时长、60 秒上限、停止后提交、失败提示、可重复录音。
- F2 音频文件上传：至少 WAV + 浏览器实际录音格式，与录音共用识别逻辑，格式/解码错误提示。
- F3 本地中英文识别：本地开源模型、CPU 推理、页面选择 `zh`/`en`、返回文本、可连续识别、不做翻译、不调用云端 ASR、不使用浏览器 Web Speech API、模型准备后离线可运行。
- F4 结果展示：当前语言、录音/识别中/完成状态、文本、音频时长、处理耗时、过程反馈、复制。
- F5 异常处理：题目表格中的 8 类异常 + 上传大小上限 10 MB。
- 接口：`GET /health`、`POST /api/transcribe`、`GET /`，字段与状态码符合题目约定。
- 环境：B/S、Python 3.12、FastAPI、HTML/CSS/JS、Chrome/Edge、pip、Windows 11 x64 统一启动方式；不依赖 Docker、Node.js、数据库、CUDA、特殊原生编译依赖。
- 测试：pytest 自动化覆盖 API/音频/语言/模型集成/错误/前后端流程；真实模型中英文验证；6 项手动验证；测试报告。
- 文档与 OpenCode 三阶段过程证据。

#### 加分功能（已确认纳入交付目标，但仍受门禁）

- F6 实时语音识别（近实时分片即可）——D5 已确认要做；只在 G4 通过后开始。
- 中英文混合语音自动语言检测（题目明确列为加分项）——F6 完成后再评估，不作为必做。
- 自动化浏览器端到端测试（非题目要求，但可作为“前后端流程”的补充证据，默认不纳入 `pytest -q`）。

#### 明确不做

- 用户登录、权限管理、数据库、识别历史、说话人识别、声纹、降噪算法、翻译、TTS、模型训练/微调、分布式部署、多用户并发、手机端适配、商业级实时字幕。
- 不以 Docker、Node.js、MySQL/PostgreSQL/Redis、云数据库/对象存储、云端 ASR、CUDA/GPU、需要面试官编译的原生依赖作为运行前提。
- 不为展示技术能力引入前端框架、构建工具、消息队列、缓存、ORM 等非必要基础设施。

### 1.3 验收标准

以题目第 9 节为准，逐条对应：

| 编号 | 完成标准 | 验收方式 |
| --- | --- | --- |
| A1 | 按 README 在约定环境启动 | 在干净虚拟环境执行题目给定的两条命令，访问 `http://127.0.0.1:8000` |
| A2 | 浏览器可访问麦克风、录制并停止 | Chrome/Edge 手动录音，观察授权、计时、停止 |
| A3 | 录制音频可提交后端 | 浏览器 Network 观察 `/api/transcribe` 返回 200；后端日志确认处理 |
| A4 | 真实本地模型分别识别中英文 | 真实模型测试 + 手动麦克风/上传，记录原始文本与耗时 |
| A5 | 结果正确返回并展示 | 页面显示文本、语言、音频时长、处理耗时 |
| A6 | 可通过上传音频独立验证 | 上传 `samples/chinese.wav`、`samples/english.wav` 成功；上传 webm 成功 |
| A7 | 常见错误不崩溃 | 自动化异常测试 + 浏览器手动异常场景 |
| A8 | 有实际执行过的自动化测试与真实模型验证 | 保存 `pytest -q` 与 `pytest -m real_model` 的实际输出到测试报告/证据目录 |
| A9 | 完整源码、文档、测试结果、OpenCode 证据 | 交付清单逐项核对，仓库/压缩包可复现 |

> D1 说明：没有 Windows 11 实机时，A1/A2 的 Windows 部分用 GitHub Actions `windows-latest`（Python 3.12 + 启动 + API + Playwright 假麦克风）做替代验证，并在报告中明确区分“CI 通过”与“真实 Windows 11 桌面通过”。真实 Windows 11 上的 Chrome/Edge 麦克风录音仍是已知未验证项，不能用 CI 结果冒充实机通过。

### 1.4 核心需求到实现模块（摘要）

详细逐项映射见第 3 节。

| 需求 | 主要实现模块 | 主要验收 | 任务编号 |
| --- | --- | --- | --- |
| F1 麦克风录音 | `static/app.js`、`app/api/routes.py` | 手动录音 + 状态/时长/60 秒 + 再次录音 | T4.1–T4.4、T6.1–T6.2 |
| F2 文件上传 | `static/index.html`、`static/app.js`、`app/services/audio.py` | WAV/webm 上传 + 错误提示 | T2.1–T2.6、T4.5、T6.3–T6.4 |
| F3 本地中英文 ASR | `app/services/transcriber.py`、`scripts/download_model.py` | 真实模型中英文 + 离线 | T3.1–T3.8、T5.2–T5.3、T6.9 |
| F4 结果展示 | `static/index.html`、`static/app.js`、`static/styles.css` | 页面字段齐全、复制 | T4.1、T4.6–T4.8、T6.8 |
| F5 异常处理 | `app/errors.py`、`app/services/audio.py`、前端错误态 | 8 类异常 + 10 MB + 4xx/5xx | T1.5、T2.1–T2.4、T4.4、T4.8、T6.5–T6.7 |
| F6 实时识别（已确认） | WebSocket + PCM 分片 + 滚动识别 | 门禁通过后手动演示 | T8.0–T8.5 |
| 接口 | `app/main.py`、`app/api/routes.py` | 契约测试 + curl | T1.4、T3.7 |
| 环境/启动 | `requirements.txt`、`README.md`、`.gitignore`、`.github/workflows/windows.yml` | Windows CI + 干净环境复现 | T1.1–T1.2、T1.8、T6.10、T9.1 |
| 自动化测试 | `tests/` | `pytest -q` 全绿；真实模型单独命令 | T1.6、T2.5–T2.6、T3.9、T5.2–T5.6 |
| 手动/离线验证 | 测试报告 + 证据 | 6 项手动验证全部执行 | T6.1–T6.12 |
| 文档/OpenCode | `docs/` | 文档齐全、三阶段证据、Git 记录 | T7.1–T7.9 |

---

## 2. 技术方案

### 2.1 系统架构

```text
┌──────────────────────────── Browser (Chrome / Edge) ────────────────────────────┐
│ static/index.html + app.js + styles.css                                         │
│  - getUserMedia / MediaRecorder（webm/opus，必要时 ogg/mp4）                     │
│  - 60 秒计时与自动停止                                                          │
│  - 文件选择与客户端大小/扩展名校验                                              │
│  - fetch multipart/form-data → POST /api/transcribe                             │
│  - 状态机、结果展示、复制、错误提示                                             │
└───────────────────────────────────┬─────────────────────────────────────────────┘
                                    │ HTTP (localhost, 同源)
┌───────────────────────────────────▼─────────────────────────────────────────────┐
│ FastAPI app (127.0.0.1:8000)                                                    │
│  GET  /                  → static/index.html                                    │
│  GET  /health            → {"status":"ok"}                                      │
│  POST /api/transcribe    → UploadFile(file) + language(zh|en)                   │
│                                                                                 │
│  路由层：参数校验、语言校验、计时、错误映射                                      │
│  音频层：大小限制 → 临时文件 → PyAV 探测/解码 → 16 kHz 单声道 float32 → 时长     │
│  ASR 层：惰性单例 Transcriber + 互斥锁 → faster-whisper（CTranslate2 int8 CPU）  │
│  错误层：400/413/415/422/500/503 + 可理解的中文错误信息                          │
└───────────────────────────────────┬─────────────────────────────────────────────┘
                                    │ 本地文件（首次下载，之后离线）
                          models/faster-whisper-small/
```

部署边界：单进程、单机、单用户；不引入数据库、任务队列、反向代理或容器。前端与后端同源，不需要 CORS。

### 2.2 推荐目录结构

```text
local-speech-to-text/
├── app/
│   ├── __init__.py
│   ├── main.py                # create_app()、静态资源挂载、GET /、启动预热
│   ├── config.py              # 环境变量/默认配置（模型路径、大小与时长限制）
│   ├── schemas.py             # 响应模型（TranscriptionResponse 等）
│   ├── errors.py              # ApiError、异常处理器、错误码
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # /health、/api/transcribe
│   └── services/
│       ├── __init__.py
│       ├── audio.py           # 上传校验、临时文件、PyAV 解码、时长
│       └── transcriber.py     # 协议、假实现、faster-whisper 实现、惰性加载
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── scripts/
│   ├── download_model.py      # 一次性下载模型到 models/
│   └── verify_asr.py          # 命令行真实模型冒烟验证
├── tests/
│   ├── conftest.py            # 测试 app、生成 WAV、假 Transcriber
│   ├── test_health.py
│   ├── test_audio.py
│   ├── test_transcribe_api.py
│   ├── test_errors.py
│   ├── test_language.py
│   ├── test_transcriber_unit.py
│   ├── test_real_model.py     # @pytest.mark.real_model，默认不执行
│   ├── test_e2e_upload.py     # 真实模型上传流程，默认不执行
│   ├── e2e/
│   │   └── test_browser.py    # Playwright E2E，CI 使用，默认不执行
│   └── fixtures/
│       └── sample.webm        # 浏览器录音格式样本
├── samples/
│   ├── chinese.wav
│   ├── english.wav
│   └── reference.txt
├── docs/
│   ├── requirements.md
│   ├── design.md
│   ├── test-report.md
│   ├── ai-development.md
│   ├── issue-log.md
│   ├── evidence/              # 截图、测试输出、性能记录
│   └── opencode/              # 三阶段会话导出（脱敏）
├── models/                    # 本地模型权重，.gitignore 排除
├── .github/
│   └── workflows/
│       └── windows.yml        # GitHub Actions Windows 兼容性验证
├── pytest.ini
├── requirements.txt
├── requirements-e2e.txt       # 可选 Playwright 依赖，不参与主安装
├── .gitignore
└── README.md
```

说明：题目建议的 `app/main.py`、`static/`、`tests/`、`samples/`、`docs/`、`requirements.txt`、`README.md`、`.gitignore` 均保留；仅在 `app/` 内部按职责拆分，不改变启动命令和接口。

### 2.3 后端方案

#### 2.3.1 应用工厂与依赖注入

- `app/main.py` 提供 `create_app(transcriber: Transcriber | None = None) -> FastAPI`。
- 生产入口 `app = create_app()`，保持 `python -m uvicorn app.main:app ...` 不变。
- 测试传入 `FakeTranscriber`，避免导入时加载模型、避免下载、避免网络。
- 真实引擎在首次识别时惰性创建；可选启动后台预热（模型文件存在时），健康检查不因模型未加载而失败。
- 推理是同步阻塞操作，路由中用 `run_in_threadpool` 调用，避免阻塞事件循环。
- 单进程内用互斥锁限制同时 1 个推理任务；本系统面向单用户，不做并发优化。
- 依赖策略：使用 plain `uvicorn`（不加 `[standard]`），避免 `uvloop/watchfiles/httptools` 等非必要原生扩展；F6 已确认要做，显式加入 `websockets`；`python-multipart` 用于表单上传。

#### 2.3.2 接口契约

| Method | Endpoint | 请求 | 成功响应 | 失败 |
| --- | --- | --- | --- | --- |
| GET | `/health` | 无 | `200 {"status":"ok"}` | — |
| POST | `/api/transcribe` | `multipart/form-data`：`file`（File）、`language`（`zh`/`en`） | `200 {"text","language","duration_seconds","processing_seconds"}` | `400/413/415/422/500/503` |
| GET | `/` | 无 | `200 text/html` | — |
| GET | `/static/*` | 无 | 静态资源 | `404` |

约定：

- `duration_seconds`：解码后实际采样点数 / 采样率，保留 1–2 位小数。
- `processing_seconds`：从路由开始处理到推理结束的单调时钟耗时，包含解码、模型加载（若首次请求触发）与推理；**不含**首次下载（本项目不在请求内自动下载，下载由脚本完成）。模型加载耗时另记 `model_load_seconds` 日志，正常预热后该值接近 0。实现与文档统一此口径。
- `language`：原样回显请求语言；若后续实现自动检测扩展，`zh`/`en` 请求仍原样回显。
- 错误响应统一为 `{"detail": "<可读信息>", "code": "<机器码>"}`；不返回堆栈。
- 额外可选接口（如 `/api/status`、WebSocket `/ws/transcribe`）只能新增，不能改变上述必做接口。

#### 2.3.3 错误码映射

| 场景 | HTTP | code | 说明 |
| --- | --- | --- | --- |
| 缺少 `file`/`language` | 422 | `validation_error` | FastAPI 默认校验，保持可读 |
| 语言不是 `zh`/`en` | 400 | `invalid_language` | 明确列出支持值 |
| 空文件（0 字节） | 400 | `empty_file` | 不进入解码 |
| 扩展名不在白名单 | 415 | `unsupported_format` | 至少支持 wav、webm |
| 扩展名合法但无法解码 | 400 | `invalid_audio` | 损坏/伪造文件 |
| 文件超过 10 MB | 413 | `file_too_large` | 客户端预检 + 服务端流式计数 |
| 音频超过服务端上限 | 400 | `audio_too_long` | 默认 120 秒（假设，见 5.2） |
| 无可识别语音 | 200 | — | `text: ""`，前端提示“未检测到可识别语音” |
| 模型文件缺失/加载失败 | 503 | `model_unavailable` | 提示运行模型下载脚本/检查路径 |
| 推理过程异常 | 500 | `transcription_failed` | 记录日志，返回通用可读信息 |
| 其他未捕获异常 | 500 | `internal_error` | 全局处理器兜底 |

#### 2.3.4 配置项（环境变量，带默认值）

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `ASR_MODEL_PATH` | `models/faster-whisper-small` | 本地模型目录；存在则完全离线加载 |
| `ASR_MODEL_SIZE` | `small` | 下载脚本/回退使用的模型规格 |
| `ASR_DEVICE` | `cpu` | 固定 CPU，GPU 仅为可选扩展 |
| `ASR_COMPUTE_TYPE` | `int8` | CPU 量化，控制内存与速度 |
| `ASR_CPU_THREADS` | `4` | CTranslate2 线程数，可调 |
| `ASR_BEAM_SIZE` | `5` | 精度/速度权衡 |
| `ASR_VAD_FILTER` | `true` | 静音过滤，降低空音频幻觉 |
| `MAX_UPLOAD_MB` | `10` | 上传文件上限 |
| `MAX_AUDIO_SECONDS` | `120` | 服务端解码时长上限（录音端仍为 60 秒） |
| `ASR_WARMUP` | `true` | 启动时若模型存在则后台预热 |

所有配置集中在 `app/config.py`，不散落魔法数字；测试可覆盖配置。

#### 2.3.5 模型生命周期

1. 首次安装：用户执行 `python scripts/download_model.py`，通过互联网下载权重到 `models/faster-whisper-small/`。
2. 启动：若本地模型存在且 `ASR_WARMUP=true`，后台线程加载；失败只记录状态，不阻止服务启动。
3. 首次识别：若未预热，惰性加载（加锁，避免并发重复加载）；加载失败返回 503。
4. 后续识别：复用单例，离线运行；不访问 HuggingFace。
5. 不把模型权重提交 Git；`.gitignore` 排除 `models/`。

### 2.4 前端方案

- 纯原生 HTML/CSS/JS，单页，无构建步骤、无 npm、无 CDN（离线可用）。
- 状态机：`idle → requesting_permission → recording → stopping → transcribing → success/error → idle`。
- 录音：
  - `navigator.mediaDevices.getUserMedia({audio: {channelCount: 1, echoCancellation: true, noiseSuppression: true}})`。
  - 通过 `MediaRecorder.isTypeSupported` 依次选择 `audio/webm;codecs=opus`、`audio/webm`、`audio/ogg;codecs=opus`、`audio/mp4`，记录实际 MIME 并据此生成上传文件名后缀。
  - `MediaRecorder` 使用 `timeslice`（如 1000 ms）收集分片；停止后合并为 Blob。
  - 计时使用 `Date.now()` 差值，每 200 ms 刷新；达到 60 秒自动调用停止，并在状态区明确提示“已达到 60 秒上限”。
  - 停止后释放 `MediaStreamTrack`，避免麦克风占用。
- 文件上传：
  - `accept=".wav,.webm,.ogg,.oga,.mp3,.m4a,.mp4,.flac,audio/*"`，客户端检查非空与 ≤10 MB。
  - 与服务端共用同一 `/api/transcribe`。
- 展示：当前语言、录音状态、计时、识别中已耗时、音频时长、处理耗时、识别文本、复制按钮、重试/重新录音。
- 错误：
  - `NotAllowedError` → 明确提示麦克风权限被拒绝及恢复方法；
  - `NotFoundError` / `DevicesNotFoundError` → 未检测到麦克风；
  - `NotReadableError` → 设备被占用或不可读；
  - `SecurityError` → 非安全上下文（localhost 除外）；
  - `MediaRecorder.onerror` 或无数据 → 明确提示录音失败，提示重试；
  - 后端 4xx/5xx → 展示 `detail`，保留重试按钮。
- 复制：优先 `navigator.clipboard.writeText`，失败回退到隐藏 textarea + `document.execCommand('copy')`。
- 无外部字体/图标依赖；桌面端布局，不做手机适配（题目不要求）。

### 2.5 音频处理方案

1. 接收上传：校验字段、扩展名、空文件；以块读取写入 `tempfile.TemporaryDirectory()` 下的临时文件，同时累计字节数，超过 10 MB 立即中止并返回 413。
2. 解码：使用 **PyAV**（faster-whisper 的依赖，wheel 内含 FFmpeg 库，预期无需系统安装 ffmpeg；此项需实测确认）。解码为 16 kHz、单声道、float32。
3. 时长：以实际解码采样点数计算；同时设置最大解码样本数，超过 `MAX_AUDIO_SECONDS` 立即停止并返回 400，避免超大压缩文件造成内存/CPU 风险。
4. 空音频：解码 0 帧 → 400 `invalid_audio`；有音频但无语音 → 交给 VAD/模型，返回空文本。
5. 清理：`finally` 中删除临时目录；Windows 下先关闭文件句柄再删除。
6. 格式策略：白名单扩展名 `.wav/.webm/.ogg/.oga/.mp3/.m4a/.mp4/.flac`，实际以解码结果为准；至少保证题目要求的 WAV 与浏览器录音 webm。
7. 重采样与声道：统一由 PyAV 重采样，避免依赖浏览器端格式假设。

### 2.6 ASR 模型候选对比

| 方案 | 模型/运行方式 | 中文 | 英文 | CPU | Windows 11 / pip | 离线 | 流式/实时 | 主要风险 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **faster-whisper** | Whisper small（244M），CTranslate2 int8 | 良好（清晰语音）；标点/简繁需实测 | 良好 | 支持，int8 量化 | PyPI 已有 `ctranslate2` cp312 win_amd64 wheel；纯 pip | 本地目录加载，完全离线 | 非原生流式，可用分片滚动近似 | 老 CPU 速度、中文标点/简繁、静音幻觉 | **推荐** |
| sherpa-onnx + SenseVoiceSmall | ONNX Runtime，非自回归 | 很强 | 良好 | 很快 | PyPI 有 cp312 win_amd64 wheel | 本地 onnx，完全离线 | 可另配 streaming zipformer | 两套模型/生态较小、文本规范化差异 | 备选（中文精度优先时） |
| Vosk | 小型 Kaldi 模型 | 一般 | 一般 | 很快 | 有 Windows wheel | 完全离线 | 原生流式 | 中文准确率与标点较弱，演示风险高 | 不推荐 |
| whisper.cpp | C++ 推理 | 同 Whisper | 同 Whisper | 很好 | 需预编译二进制/自行编译 | 完全离线 | 可分片 | 不满足“无需特殊原生编译”的低风险要求 | 不推荐 |
| FunASR / SenseVoice（PyTorch） | PyTorch | 很强 | 良好 | 支持但依赖重 | torch 体积大、Windows 安装链长 | 离线 | 可流式 | 安装体积/兼容性风险高，2 天周期不划算 | 不推荐 |
| 云端 ASR / Web Speech API | — | — | — | — | — | 不满足 | — | 题目明令禁止 | 排除 |

#### 推荐：faster-whisper + Whisper small（int8, CPU）

理由：

1. **单模型覆盖中英文**：Whisper 为多语言模型，通过 `language="zh"/"en"` 指定，不需要维护两套模型；符合页面语言选择。
2. **纯 pip 依赖**：`faster-whisper` 为纯 Python 包，核心 wheel 为 `ctranslate2`、`av`、`onnxruntime`；2026-10-27 查询 PyPI 元数据确认存在 `ctranslate2 4.8.4 cp312 win_amd64`、`av 19.0.2 cp312 win_amd64`、`onnxruntime 1.31.1 cp312 win_amd64` wheel。实际 Windows 运行仍需实测。
3. **CPU 友好**：CTranslate2 支持 int8 量化；模型规模适中（small 约 244M 参数，转换后权重约数百 MB），普通开发电脑可运行。实际 RTF 必须实测，不能预先承诺。
4. **离线简单**：将模型下载到本地目录后，以本地路径构造 `WhisperModel`，运行期不访问网络；便于断网验收。
5. **解码省事**：faster-whisper 自带基于 PyAV 的音频解码与 Silero VAD（onnxruntime），可处理 wav/webm/ogg 等容器，减少自研解码代码。
6. **资料与可维护性**：使用广泛、文档充分，出问题更容易定位；相比 whisper.cpp 不需要编译，相比 FunASR 不引入 PyTorch 重依赖。
7. **许可证**：Whisper 权重与 faster-whisper 均为 MIT 系许可证，便于分发源码（不提交权重）；最终以仓库 LICENSE 为准并在文档注明。

模型规模默认 **small**：base 约 141 MB、速度更快但中文准确率通常偏弱；small 在清晰语音下更稳妥。medium 体积/CPU 成本过高，不作为默认。若实测 small 在目标机器上过慢，则回退 base；若中文准确率不达标且时间允许，再实验 SenseVoiceSmall（需重新评估依赖与集成成本）。

#### 为什么没有直接选择 sherpa-onnx + SenseVoiceSmall

SenseVoiceSmall 是本次选型的**主要备选**，不是被排除的方案。它的优势很明确：

- 非自回归端到端结构，官方宣称在相近参数量下比 Whisper-small 快 5 倍以上；中文/粤语识别是官方重点优势。
- 单模型支持中文、英文、粤语、日语、韩语，并自带语种识别（LID）、逆文本归一化/标点（ITN）等能力，理论上很适合中英文和自动语种加分项。
- sherpa-onnx 官方支持 Windows x64；2026-10-27 查询 PyPI 可见 `sherpa-onnx 2.0.1` 与 `sherpa-onnx-core 2.0.1` 均提供 win_amd64 wheel；运行期不依赖 PyTorch。
- 官方文档也给出了“VAD + SenseVoice”的麦克风近实时示例，因此它同样可以做 F6。

没有把它作为默认主方案，原因不是“能力不够”，而是**交付风险与约束匹配**：

1. **它不是原生流式模型**。官方直接推理限制约 30 秒，长音频/实时需要 VAD 或固定窗口切分；要真正低延迟流式，通常还要另配 streaming zipformer 模型。也就是说，选它并不能自动消除 F6 的分片/拼接复杂度，只是单次推理更快。
2. **许可证不同**。SenseVoice 仓库代码是 MIT，但官方 SenseVoiceSmall 权重走 FunASR Model Open Source License（有署名/模型名称等条件，商业使用需遵守该协议）；Whisper 权重是 MIT。用于面试演示两者都可，但 Whisper 的分发与文档负担更小。
3. **模型分发与转换链更长**。sherpa-onnx 需要其转换后的 ONNX 模型（通常从 GitHub Releases/HuggingFace 获取，或自行从 FunASR 转换）；自行转换会引入 PyTorch，直接违背“轻依赖”目标。本机当前访问 HuggingFace/GitHub Release 均出现过超时，模型获取风险需要实测；Whisper 也有下载风险，但有成熟的镜像/手动放置路径。
4. **未知数更多**。faster-whisper 的 CPU int8、VAD、30 秒窗口、60 秒音频处理、语言参数都有成熟文档和大量实践；SenseVoice + sherpa-onnx 的 Python API、ITN 输出、长音频切分、WebM 解码组合需要额外验证。当前没有 Windows 11 实机，减少未知数比追求理论最优更重要。
5. **英文稳健性与生态**。Whisper 的英文/多语言生态更成熟；SenseVoice 的公开优势主要集中在中文/粤语，英文虽然支持，但在本次“必须中英文都稳”的验收下，Whisper 的确定性更高。
6. **时间与回滚成本**。2 天周期里，主引擎一旦集成失败，换模型的成本很高；先把 Whisper 做成可交付基线，再在抽象层后评估 SenseVoice，风险更可控。

因此当前策略是：**Whisper small 作为必做基线；SenseVoice 作为条件触发的备选**。触发条件：
- T3.6 实测中文 CER 明显不达标，或 15 秒音频处理时间超过可接受范围；
- F6 实测滚动转写延迟不可接受；
- 模型下载与 Windows CI 验证均顺利，且时间剩余 ≥2 小时。

若触发，执行 60–90 分钟时间盒 spike（T3.11）：安装 sherpa-onnx、下载 int8 ONNX 模型、跑中英文样本、测 RTF/CER、验证 WebM 解码与 Windows CI；只有“中文/速度明显更好且许可证可接受”才替换主引擎，否则保留 Whisper 并把结果写入 `docs/design.md`。识别层已抽象为 `Transcriber`，替换不需要改 API/前端。

> 需要强调：以上 SenseVoice 的速度/准确率为官方资料与公开基准，**不是本机实测**；Whisper 的实际速度/准确率同样待 T3.6 验证。两者都不能在规划阶段写成确定事实。

#### 已核实与未核实

- 已核实（2026-10-27，PyPI JSON）：`faster-whisper 1.2.1` 依赖 `ctranslate2>=4,<5`、`av>=11`、`onnxruntime>=1.14,<2`；上述三包存在 cp312 win_amd64 wheel。
- 已核实（官方 README，2026-10-27 查阅）：faster-whisper 支持 CPU int8（`WhisperModel(..., device="cpu", compute_type="int8")`）、Silero VAD、指定 `language`、直接从本地目录加载模型；官方还给出 CPU int8 的基准数据（具体硬件不同，不能直接外推到目标机器）。
- 已核实（PyPI/官方文档，2026-10-27）：`sherpa-onnx 2.0.1` 依赖 `sherpa-onnx-core 2.0.1`，两者均提供 win_amd64 wheel；官方文档称支持 Windows x64、SenseVoice 是非自回归模型，并宣称同参数量下比 Whisper-small 快 5 倍以上（官方基准，非本机实测）。
- 未核实（SenseVoice）：本地实际中文/英文 CER、WebM 解码组合、ITN 输出清洗、Windows CI 运行、模型下载可达性；若触发 T3.11 再验证。
- **未核实，必须实验**：目标 Windows 11 机器上的实际安装/启动；CPU 推理速度；中文识别准确率与简繁/标点表现；PyAV 在无系统 ffmpeg 情况下对 webm/opus 的解码；HuggingFace 网络可达性；10 MB 文件解码耗时与内存。

### 2.7 模型准备与离线方案

1. `scripts/download_model.py`：
   - 参数：`--model small`、`--output models/faster-whisper-small`；
   - 使用 `faster_whisper` / `huggingface_hub` 下载 `Systran/faster-whisper-small` 到指定目录；
   - 下载后校验关键文件（`model.bin`、`config.json`、`tokenizer.json`、`vocabulary.txt` 等）并打印体积；
   - 支持 `HF_ENDPOINT` 环境变量/镜像；失败时给出可操作提示，不自动反复重试。
2. 运行期只使用本地目录：`WhisperModel(local_path, device="cpu", compute_type="int8")`；不传模型名，避免隐式联网。
3. 离线验证：
   - 先在线完成下载并成功识别一次；
   - 设置 `HF_HUB_OFFLINE=1`（可选），断开网络/禁用网卡，重启服务；
   - 再次执行中英文真实识别，记录结果与耗时；
   - 代码审查确认无云端 ASR SDK、无 Web Speech API。
4. README 明确：模型权重不提交 Git；首次安装需要互联网；下载失败时的镜像/手动放置方法；离线启动步骤。

### 2.8 测试方案

#### 分层

| 层级 | 是否默认执行 | 是否用真实模型 | 内容 |
| --- | --- | --- | --- |
| 单元测试（音频） | 是 | 否 | 生成 WAV、损坏文件、空文件、时长上限、webm fixture 解码 |
| API 契约测试 | 是 | 否（注入 FakeTranscriber） | 健康检查、中英文、非法语言、缺参、空文件、超限、格式错误、模型异常 |
| 前端静态冒烟 | 是 | 否 | `GET /` 200、关键元素/脚本存在、静态资源 200 |
| 真实模型集成 | 否（`-m real_model`） | 是 | 真实加载本地模型，识别两份样本，校验非空/语言/阈值/CER/WER/耗时 |
| 真实 API 上传流程 | 否（`-m real_model`） | 是 | 通过 TestClient 上传真实 WAV，走完整路由/解码/推理 |
| 浏览器 E2E（CI 使用） | 否（`-m e2e`） | 可选（CI 可跑真实模型） | Playwright + Chromium/Edge 假麦克风，验证页面加载、上传、录音流程 |
| 手动验证 | 人工 | 是 | 6 项指定场景 + Edge + 异常场景 |

#### 关键约束

- 默认 `python -m pytest -q`：不依赖麦克风、不下载模型、不访问外网。通过 `create_app(FakeTranscriber)` 注入实现，杜绝导入即加载模型。
- 真实模型测试单独命令，例如 `python -m pytest -q -m real_model`；若模型目录不存在，明确 skip 并提示先运行下载脚本，不能静默通过。
- `pytest.ini` 配置 `markers`，默认通过 `addopts = -m "not real_model and not e2e"` 排除重测试；实现时验证命令行 `-m real_model` 与 addopts 的覆盖行为，如有冲突改用环境变量 `ASR_RUN_REAL=1` 门控。
- 阈值不拍脑袋：先跑一遍记录原始 CER/WER 与耗时，再设定宽松阈值（如中文 CER ≤ 0.3、英文 WER ≤ 0.3，最终以实测校准），并在测试中输出实际值。
- Mock 测试只证明接口/错误处理/数据流，不替代真实模型验证；文档和报告中必须分开统计。

### 2.9 OpenCode 开发留痕

- 三阶段各保存一份关键会话导出：
  1. `docs/opencode/01-requirements-and-design.md`：需求理解、技术选型、计划（含本次规划会话）；
  2. `docs/opencode/02-implementation.md`：后端/前端/模型集成关键对话；
  3. `docs/opencode/03-testing-and-fixes.md`：测试失败、定位、修复、复测。
- 导出前脱敏：绝对路径、用户名、密钥、无关个人信息；保留模型/工具名与关键命令。
- `docs/ai-development.md` 回答题目 5 个问题，并说明哪些决策由人做出、AI 生成代码如何验证。
- Git 按阶段提交（脚手架、后端、前端、测试、文档、修复），提交信息可读；最终打 tag（如 `v1.0-submission`）。
- `docs/issue-log.md` 记录问题、复现、定位、修复、验证。

---

## 3. 需求与验收映射

### 3.1 F1 浏览器麦克风录音

| 编号 | 要求 | 实现 | 验收 |
| --- | --- | --- | --- |
| F1-1 | 请求麦克风权限 | `getUserMedia`，点击开始时请求 | Chrome/Edge 弹窗；拒绝有提示 |
| F1-2 | Start Recording | 按钮触发采集与 `MediaRecorder.start(1000)` | 状态变为录音中，计时开始 |
| F1-3 | Stop Recording | 按钮停止，触发 `onstop` 后上传 | 停止后生成 Blob 并请求接口 |
| F1-4 | 状态与录音时长 | 状态机 + 200 ms 计时器 | 页面实时显示状态与 mm:ss.s |
| F1-5 | 停止后提交完整识别 | 仅在 `onstop` 后调用 API | Network 仅一次完整请求 |
| F1-6 | 最长 60 秒 | 计时到 60 秒自动 stop + 后端 120 秒兜底 | 手动录满 60 秒自动结束并提示 |
| F1-7 | 录音过程明确提示 | 状态文案、按钮禁用、录音指示 | 录音中不可重复开始 |
| F1-8 | 停止后才能识别 | 录音中禁用上传/识别按钮 | 按钮状态检查 |
| F1-9 | 失败原因提示 | DOMException 分类映射 | 拒绝权限/无设备/占用分别提示 |
| F1-10 | 可再次录音 | 成功后重置状态、释放轨道 | 连续两次录音成功 |

### 3.2 F2 音频文件上传

| 编号 | 要求 | 实现 | 验收 |
| --- | --- | --- | --- |
| F2-1 | 至少 WAV | 扩展名白名单 + PyAV 解码 | 上传 `samples/chinese.wav` 成功 |
| F2-2 | 浏览器录音格式 | 支持 webm/ogg（按实际 MIME）；提交 `tests/fixtures/sample.webm` | 上传 webm 成功，文本非空 |
| F2-3 | 共用后端逻辑 | 录音与上传都调用 `/api/transcribe` | 两条路径均走同一路由/服务 |
| F2-4 | 不支持/无法解码提示 | 415/400 + 前端展示 | 上传 `.txt`、伪造 wav 均有明确提示 |

### 3.3 F3 本地中英文识别

| 编号 | 要求 | 实现 | 验收 |
| --- | --- | --- | --- |
| F3-1 | 中文普通话 | Whisper small，`language=zh` | 真实模型测试 + 手动中文 |
| F3-2 | 英语 | `language=en` | 真实模型测试 + 手动英文 |
| F3-3 | 页面选择语言 | 单选/分段控件，默认 zh | 切换后请求参数正确 |
| F3-4 | 返回文本 | 响应 `text` + 页面展示 | 页面可见文本 |
| F3-5 | 连续识别 | 每次请求无状态；前端重置 | 连续两次识别成功 |
| F3-6 | 不做翻译 | 仅转写；中文输出中文、英文输出英文 | 人工检查输出语言 |
| F3-7 | 本地开源模型 | faster-whisper + Whisper 权重，本地路径 | 代码/依赖审查 |
| F3-8 | CPU 推理 | `device=cpu`、`compute_type=int8` | 任务管理器无 GPU 依赖；CPU 实测 |
| F3-9 | 首次可联网下载 | `scripts/download_model.py` | 下载脚本成功并校验文件 |
| F3-10 | 准备后离线 | 本地目录加载；断网复测 | 断网后中英文识别成功 |
| F3-11 | 禁止云端 ASR | 依赖与代码中无云端 SDK/API | `grep` 审查 + 离线测试 |
| F3-12 | 禁止 Web Speech API | 前端只用 MediaRecorder，不调用 `webkitSpeechRecognition` | 代码审查 + 断网仍可识别 |
| F3-13 | 普通 CPU 可运行 | small 默认、int8、线程可调、VAD | 目标机器实测耗时记录 |

### 3.4 F4 结果展示

| 编号 | 要求 | 实现 | 验收 |
| --- | --- | --- | --- |
| F4-1 | 当前语言 | 控件 + 结果区显示 | 页面可见 |
| F4-2 | 录音/识别中/完成状态 | 状态机文案 | 全流程观察 |
| F4-3 | 识别文字 | 结果区 `<pre>`/可换行文本 | 中英文均显示 |
| F4-4 | 音频时长 | 后端 `duration_seconds` | 与样本时长误差合理 |
| F4-5 | 处理耗时 | 后端 `processing_seconds` | 页面显示秒数 |
| F4-6 | 过程反馈 | 录音计时；识别中计时/“识别中…”；按钮禁用 | 不出现无提示等待 |
| F4-7 | 直接复制 | 复制按钮 + Clipboard API 回退 | 粘贴验证一致 |

### 3.5 F5 异常处理

| 场景 | 后端行为 | 前端行为 | 验收 |
| --- | --- | --- | --- |
| 拒绝麦克风权限 | —（请求不发出） | `NotAllowedError` 明确提示，页面不崩 | 手动阻止权限 |
| 无可用麦克风 | — | `NotFoundError` 提示未检测到设备 | 手动禁用/无设备 |
| 空文件/损坏音频 | 400 `empty_file` / `invalid_audio` | 展示原因，允许重试 | 自动化 + 手动 |
| 不支持格式 | 415 `unsupported_format` | 展示支持格式 | 上传 `.txt` |
| 录音超过 60 秒 | 前端自动停；后端 120 秒兜底 | 提示已达上限并正常识别 | 手动录满 60 秒 |
| 模型加载失败 | 503 `model_unavailable` | 展示“模型不可用”及处理建议 | 临时改名模型目录测试 |
| 识别中后端出错 | 500 `transcription_failed` | 展示失败，保留重试 | Fake 抛错测试 + 手动 |
| 无可识别语音 | 200 `text: ""` | 提示未检测到语音，不崩溃 | 静音 WAV 测试 |
| 上传超过 10 MB | 413 `file_too_large` | 客户端预检 + 服务端兜底 | 生成大文件测试 |

### 3.6 F6 实时识别（D5 已确认要做，仍受 G5 门禁）

| 编号 | 要求 | 候选实现 | 验收（仅在门禁通过后） |
| --- | --- | --- | --- |
| F6-1 | 持续采集 | Web Audio API（AudioWorklet/ScriptProcessor）采集 PCM 16 kHz 单声道 | 说话时持续有数据 |
| F6-2 | 分片/流式发送 | WebSocket 发送 PCM 分片（如 1–2 秒） | 服务端持续收到 |
| F6-3 | 本地模型处理 | 复用当前主引擎（默认 faster-whisper），对滚动窗口重转写 | 本地模型，无云端 |
| F6-4 | 持续更新文本 | 页面增量/覆盖显示中间结果 | 停止前即可看到文本 |
| F6-5 | 停止输出最终文本 | 停止时对完整音频做一次最终识别 | 最终文本完整 |

说明：不要求原生流式模型；推荐“PCM 分片 + 累积/滑动窗口重转写”，明确中间结果可能重复/回退，最终以停止后的完整识别为准。F6 不影响必做接口。自动语言检测依赖整段语言判定，混合语句可能只按一种语言输出，作为实验性加分项，不承诺逐词混杂识别。

### 3.7 环境与启动约束

| 要求 | 方案 | 验收 |
| --- | --- | --- |
| B/S 架构 | 浏览器 + FastAPI | 浏览器访问 |
| Python 3.12 | 代码与依赖按 3.12 验证 | `python --version` |
| FastAPI | 后端框架 | 启动日志/依赖 |
| HTML/CSS/JS | 原生静态文件 | 无构建步骤 |
| Chrome/Edge | 主流桌面浏览器 | 两者手动验证 |
| 本地开源 ASR | faster-whisper | 真实模型测试 |
| CPU 必须支持 | int8 CPU | 无 GPU 机器验证 |
| pytest | 测试框架 | `pytest -q` |
| pip/requirements.txt | 唯一依赖入口 | 干净环境安装 |
| Windows 11 x64 | 统一复现环境 | 无实机：GitHub Actions `windows-latest` 安装/启动/API/真实模型/假麦克风；真实 Windows 11 桌面/麦克风明确标注未验证 |
| 统一启动 | `python -m pip install -r requirements.txt`；`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | 逐字执行 |
| localhost 访问 | 绑定 127.0.0.1，无需 HTTPS | `http://127.0.0.1:8000` |
| 禁止组件 | 无 Docker/Node/DB/云 ASR/CUDA/编译依赖 | 依赖树审查 |

### 3.8 测试要求

| 要求 | 实现 | 验收 |
| --- | --- | --- |
| HTTP API：健康/正常/非法 | `test_health.py`、`test_transcribe_api.py`、`test_errors.py` | 断言状态码/字段 |
| 音频处理：正常/空/损坏 | `test_audio.py` + 生成 WAV | 断言时长/异常 |
| 语言：中/英/非法 | `test_language.py` | zh/en 200，其他 400 |
| 模型集成：调用/结果/异常 | Fake + `test_real_model.py` | 正常与异常路径 |
| 错误处理：格式/模型失败 | `test_errors.py` | 415/503 等 |
| 前后端流程 | 真实上传集成测试 + 手动浏览器 + Windows CI Playwright | 至少一条真实流程 |
| Mock/真实区分 | 默认 fake；`real_model` marker | 报告分开记录 |
| `pytest -q` 约束 | 无麦克风、无模型下载、无外网 | 干净环境/断网执行 |
| 真实测试单独命令 | `pytest -m real_model` | README 说明并实际执行 |
| 样本 | `samples/*.wav` + `reference.txt` | 5–15 秒、可播放、本人录制授权说明 |
| 手动 6 项 | 测试报告逐项记录 | 见 T6.1–T6.9 |
| Windows CI | `windows-latest` 安装/启动/API/真实模型/Playwright | 与真实 Windows 11 未验证项分开记录 |
| 测试报告 | `docs/test-report.md` | 用例、结果、耗时、已知问题 |

### 3.9 文档与过程要求

| 成果 | 必须包含 | 验收 |
| --- | --- | --- |
| `README.md` | 介绍、环境、安装、模型初始化、启动、使用、测试、离线、故障排查 | 新人按文档可复现 |
| `docs/requirements.md` | 需求理解、拆分、假设、边界 | 与本题逐项对应 |
| `docs/design.md` | 架构、模块、音频流程、ASR 选型理由、错误码、限制 | 与代码一致 |
| `docs/test-report.md` | 用例、实际结果、真实模型、手动验证、已知问题 | 有实际命令输出/数据 |
| `docs/ai-development.md` | OpenCode 任务、人工决策、问题与修复、验证方式、后续优化 | 回答题目 5 问 |
| OpenCode 证据 | 三阶段会话导出（脱敏） | 文件存在且可读 |
| Git | 分阶段提交、最终干净 | `git log`/`git status` |

### 3.10 功能范围护栏

- 不新增登录、数据库、历史记录、说话人识别、降噪、翻译、TTS、训练、分布式、多用户、手机适配。
- 不为 F6 引入第二套重型框架；F6 使用与必做项相同的本地模型/同一服务进程，独立提交、可回滚。
- 任何额外接口/参数都必须向后兼容必做契约。

---

## 4. 开发阶段与执行顺序

### 4.1 阶段总览

| 阶段 | 目标 | 前置条件 | 交付成果 | 退出条件 | 主要风险 |
| --- | --- | --- | --- | --- | --- |
| P0 规划确认 | 冻结范围、假设、验收 | 题目已读 | `plan.md`、`todo.md` | D1–D5 已确认；（D6 Git 托管）确认 | 需求理解偏差 |
| P1 脚手架 | 可启动空服务、测试框架、Windows CI 骨架 | P0 | 目录、配置、`/health`、`/`、pytest 配置、`windows.yml` | `pytest -q` 通过健康检查 | 依赖/Windows 兼容 |
| P2 音频与接口 | 上传/解码/错误处理/假模型全链路 | P1 | `/api/transcribe` + 假引擎 + Mock 测试 | 接口契约与异常测试全绿 | 格式/大小/时长边界 |
| P3 真实模型 | 本地模型加载、中英文真实识别 | P2、模型下载 | 下载脚本、CLI 验证、真实结果 | 中英文非空且耗时记录 | 下载失败、CPU 慢、准确率 |
| P4 前端 | 录音/上传/展示/错误/复制 | P2（可并行 P3） | 完整页面 | Chrome 手动全流程通过 | 浏览器格式/权限/计时 |
| P5 测试完善 | 样本、真实集成、Playwright E2E | P3、P4 | 测试与样本 | `pytest -q` + `real_model` 通过 | 阈值/环境差异 |
| P6 验收验证 | 手动 6 项、Edge、离线、Windows CI | P5 | 测试报告、证据 | 所有必做验收通过（Windows 实机未验证需披露） | Windows/离线环境 |
| P7 文档交付 | 文档、OpenCode 证据、Git | P6 | 完整交付包 | A1–A9 核对通过（注明残余项） | 证据缺失、文档不一致 |
| P8 加分功能（已确认，门禁） | 实时识别 F6；自动语种后置 | **G4 + 文档基线 + ≥3.5 小时缓冲** | 实时功能、独立提交 | 可演示且不破坏必做回归 | 时间挤占、引入回归 |
| P9 终验 | 干净环境复现、清单核对 | P7（P8 若做） | 最终提交 | 可复现、无遗漏 | 环境差异 |

### 4.2 两天执行顺序（按有效工时）

**第 1 天（约 9–10 小时）**

1. 0–1h：初始化 Git/目录/依赖，搭 `/health` 与静态首页（P1）；确认 D6 仓库托管与 CI 可用性。
2. 1–3.5h：音频校验/解码/时长/大小限制，假引擎与 `/api/transcribe`，错误码（P2）。
3. 3.5–5h：下载 small 模型，CLI 真实识别中英文，记录首轮耗时/准确率（P3 关键去风险）。
4. 5–8h：前端界面、录音、上传、状态、结果、复制、错误（P4）。
5. 8–10h：Mock 测试补齐、Chrome 首轮手动联调、修复、提交（P2/P4/P5）。

**第 2 天（约 9–11 小时）**

1. 0–2h：样本定稿（本人录音）、真实模型集成测试、真实上传 API 测试（P5）。
2. 2–4h：6 项手动验证、Edge、异常场景、离线验证（P6）。
3. 4–5h：GitHub Actions `windows-latest` 运行安装/启动/API/真实模型上传/Playwright 假麦克风（P6；无 Windows 实机的替代验证）。
4. 5–7h：README/requirements/design/测试报告初稿/OpenCode 证据/问题记录（P7 基线）。
5. 7–10h：仅在 G4 已通过且文档基线完成后，进入 F6 实时识别（3 小时时间盒）。
6. 10–11h：全量回归、F6 成功则补文档，失败则回滚；交付清单核对（P9）。

> D5 已确认要做 F6，但它仍然排在必做项之后。若第 2 天 7 点前 G4 未通过，或 F6 3 小时未能达到可演示状态，立即冻结必做版本、记录 F6 未完成原因，不用 F6 挤压 Windows/离线/文档。真实 Windows 11 桌面/麦克风因 D1 无法验证，报告中单独列为残余风险。

### 4.3 关键门禁

- **G0**：D1–D5 已确认；Git 托管与 Windows CI 方式（D6）确认；`plan.md`/`todo.md` 一致。
- **G1**：`pytest -q` 在未下载模型的环境通过，且不触发下载/麦克风。
- **G2**：真实 small 模型在开发机完成中文、英文识别，记录原始文本、耗时、CER/WER；决定是否维持 small。若触发条件成立，执行 T3.11 的 SenseVoice 时间盒评估。
- **G3**：Chrome 中完成麦克风中文/英文、WAV/webm 上传、复制、错误提示、再次录音。
- **G4**：6 项手动验证 + 离线 + Windows CI 兼容性验证 + 真实模型测试 + 测试报告基线完成；所有必做项通过（真实 Windows 11 桌面/麦克风未验证需明确披露）。
- **G5**：G4 通过、文档基线完成且剩余 ≥3.5 小时，才启动 F6；否则不做 F6 并书面说明。

---

## 5. 风险与技术决策

### 5.1 高风险清单

| 编号 | 风险 | 影响 | 概率 | 预防 | 验证 |
| --- | --- | --- | --- | --- | --- |
| R1 | Windows 11 上依赖安装/运行失败（wheel、VC++ 运行库、路径） | 直接不满足统一环境，验收失败 | 中 | 只用有 win_amd64 wheel 的包并锁版本；避免编译型依赖；路径全部 `pathlib`；临时文件先关闭再删除；GitHub Actions `windows-latest` 替代验证 | `pip download --platform win_amd64 --python-version 3.12 --only-binary=:all:` 预检 + Windows CI 干净安装/启动/API |
| R2 | HuggingFace/模型源下载慢或被阻断 | 模型准备失败，无法真实识别 | 中 | 下载脚本支持 `HF_ENDPOINT` 镜像/手动放置；文档给出离线拷贝方案；模型不提交 Git；备选 ModelScope/手动下载 | 实际下载 + 断网加载 |
| R3 | CPU 推理过慢（60 秒音频等待过久） | 体验差，可能被判定不实用 | 中 | small + int8 + 4 线程 + VAD + 前端识别中计时；保留 `ASR_MODEL_SIZE=base` 回退 | 目标机器 5/15/60 秒音频基准，记录 RTF |
| R4 | 中文准确率/标点/简繁不理想 | 演示文本质量差 | 中 | 使用清晰样本；可试用 prompt 引导简体与标点；必要时评估 SenseVoiceSmall | 真实样本 CER + 人工检查 |
| R5 | 浏览器录音格式在 Edge/Chrome 不一致或无法解码 | 录音主流程失败 | 中 | MIME 能力检测；后端统一 PyAV 解码；保留 WAV 上传兜底；记录实际 MIME | Chrome/Edge 手动录音 + webm 解码测试 |
| R6 | 麦克风权限/设备异常提示不准确 | F5 验收扣分 | 中 | 按 DOMException.name 分类；给出恢复步骤；页面不崩 | 阻止权限、禁用设备、占用设备 |
| R7 | 60 秒自动停止受后台标签页节流影响 | 超时/录音过长 | 低 | 200 ms 计时 + `Date.now()` 校正；后端 120 秒兜底；`visibilitychange` 检查 | 切后台录满 60 秒测试 |
| R8 | 静音/噪声导致幻觉文本 | 空音频结果异常 | 中 | `vad_filter=True`；空 segments 返回空文本；必要时 no_speech 阈值 | 静音 WAV 测试 |
| R9 | 默认测试触发模型下载或依赖麦克风 | 违反测试要求 | 中 | 应用工厂注入 Fake；导入不加载模型；marker 排除；clean env 验证 | 删除/改名 `models/` 后跑 `pytest -q`，监控网络 |
| R10 | 超大/损坏文件造成内存或长时间占用 | 服务卡死/崩溃 | 中 | 10 MB 流式上限；容器时长探测 + 解码样本上限 120 秒；异常兜底 | 构造 10 MB+/超长/损坏文件测试 |
| R11 | Windows 临时文件句柄未释放导致删除失败 | 识别偶发失败/磁盘残留 | 低 | 用 `TemporaryDirectory`，解码/读取后显式关闭；`finally` 清理 | Windows 连续多次识别 |
| R12 | 并发请求同时加载/推理导致内存翻倍 | 卡顿/崩溃 | 低 | 单例 + 互斥锁；单用户定位；文档声明不支持并发 | 并发请求冒烟 |
| R13 | 依赖版本漂移导致新环境装不上 | 复现失败 | 中 | `requirements.txt` 精确锁版本；提交前干净环境重装 | 新 venv 完整安装 |
| R14 | 时间不足，F6 挤占必做项 | 必做未完成，得不偿失 | 高 | 严格 G4/G5 门禁；F6 独立分支/提交；3 小时时间盒；可整体回滚 | 每日门禁检查 |
| R15 | OpenCode 证据不足或事后补造 | 过程分丢失 | 中 | 每阶段结束立即导出并提交；保留失败/修复记录 | 三阶段文件与 Git 时间线核对 |
| R16 | 样本版权/隐私问题 | 合规风险 | 低 | 自录或使用明确授权素材；reference 注明来源/许可；不含个人信息 | 文档审查 |
| R17 | 端口占用/静态路径在 Windows 下异常 | 无法访问页面 | 低 | 绑定 127.0.0.1:8000；`pathlib` 绝对路径；README 给换端口方法 | Windows 启动 + 浏览器访问 |
| R18 | 开发机默认 Python 3.9，与目标 3.12 不一致 | 本地通过但目标环境失败；或依赖版本不可用 | 中 | 统一用 CPython 3.12 创建虚拟环境；CI/本地测试均锁定 3.12；依赖锁版本 | `python --version` + 干净 3.12 venv 安装/测试 |
| R19 | **没有 Windows 11 实机**，无法验证真实桌面 Chrome/Edge 麦克风 | A1/A2 的 Windows 验收无法 100% 证明 | 高 | GitHub Actions `windows-latest` 验证安装/启动/API/真实模型/Playwright 假麦克风；如能借用 Windows 11 或云 VM，补做 T6.13 | CI 运行记录 + 明确披露“未在真实 Windows 11 上手动录音” |
| R20 | F6 已确认要做，但时间不足或性能不达标 | 加分项失败或挤压必做 | 高 | 严格 G5 门禁；3 小时时间盒；独立提交/feature flag；失败回滚 | 每次提交后跑必做回归；F6 演示与回滚记录 |

### 5.2 需要实验才能确定的问题

1. small 模型在目标 CPU 上的实际 RTF 与内存占用；是否需要回退 base。
2. 两份样本上的真实 CER/WER，测试阈值需据此校准。
3. PyAV 是否确实无需系统 ffmpeg 即可解码 webm/opus（预期是，需实测）。
4. Chrome/Edge 在 Windows 上 `MediaRecorder` 实际选择的 MIME 与后端解码兼容性。
5. Whisper 中文输出的简繁、标点、空音频幻觉表现；prompt 是否有效。
6. HuggingFace/镜像在目标网络下的下载速度与稳定性。
7. Windows CI（`windows-latest`）上 `pip install` 的总时长、体积、VC++ 运行库依赖，以及 Playwright 假麦克风能否启动。
8. 10 MB 压缩音频的探测/解码耗时与内存峰值。
9. Playwright 在 Windows CI 的安装/浏览器下载耗时；若不可用，保留 HTTP 上传流程并明确记录 E2E 未跑。
10. 只有在 T3.11 触发时才需要：SenseVoiceSmall 的实际 CER/RTF、ITN 输出、WebM 解码与 Windows CI 兼容性。

### 5.3 决策分类

#### A. 决策记录（含待确认项）

| 编号 | 决策 | 结论 | 影响与残余风险 |
| --- | --- | --- | --- |
| D1 | Windows 11 实机 | **没有** | 用 GitHub Actions `windows-latest` 做安装/启动/API/真实模型/Playwright 假麦克风验证；真实 Windows 11 桌面/麦克风仍未验证，报告中披露 |
| D2 | 模型规模 | **small** | 默认 faster-whisper Whisper small（int8 CPU）；若 G2 不达标按规则评估备选 |
| D3 | 样本来源 | **本人录音** | 录制中英文各 5–15 秒；不使用 TTS 作为主方案；注明本人授权、无敏感信息 |
| D4 | 交付方式 | **Git 仓库** | 分阶段提交、tag、脱敏 OpenCode 证据；模型权重不入库 |
| D5 | 实时识别 F6 | **要做** | 排在必做之后，G5 门禁 + 3 小时时间盒；失败回滚并说明 |
| D6 | Git 托管平台 / Actions 可用性 | **待确认** | 若为 GitHub，可直接用 `windows-latest`；若 GitLab/仅本地，Windows CI 需另找 Runner 或接受未验证 |

#### B. 可自行采用默认方案（不阻塞，已写入计划）

| 事项 | 默认 | 说明 |
| --- | --- | --- |
| ASR 引擎 | faster-whisper small / int8 / CPU / beam 5 / VAD on | 实测不达标再按 T3.11 评估 SenseVoice |
| 上传格式白名单 | wav、webm、ogg、oga、mp3、m4a、mp4、flac | 题目只强制 wav + 浏览器格式；其余为兼容性 |
| 录音上限/服务端上限 | 前端 60 秒；后端 120 秒 | 题目只规定录音 60 秒；上传仅限 10 MB，120 秒为保护性假设 |
| 10 MB 限制实现 | 客户端预检 + 服务端流式计数 + Content-Length 预检 | 防止内存放大 |
| 模型加载 | 惰性 + 可选启动预热；失败 503 | 不阻止服务启动，错误可理解 |
| 并发 | 单进程单推理锁，不做队列 | 题目不要求多用户 |
| 错误格式 | `detail` + `code` | 前端可展示，测试可断言 |
| 前端语言 | 中文说明 + 英文按钮（Start/Stop Recording） | 贴合题目用词，便于面试官操作 |
| 测试依赖 | pytest/httpx 放入 `requirements.txt` | 保证仅按 README 安装即可跑测试 |
| Windows CI | GitHub Actions `windows-latest` + Playwright 假麦克风 | 无实机时的替代验证；不冒充实机通过 |
| E2E | Playwright 默认不执行 | 避免额外浏览器下载影响主流程；CI 中单独跑 |
| 自动语言检测 | F6 完成后再可选实现 `language=auto` | 题目加分项；不得破坏 zh/en 契约 |

#### C. 需通过实验确定（不先写死结论）

- 模型最终规格与真实速度/准确率（Whisper 与可选的 SenseVoice）。
- 是否需要中文 prompt、简繁转换或文本后处理。
- 浏览器录音的实际容器/编码及是否需要额外格式兜底。
- Windows CI 的依赖安装细节与镜像方案。
- 测试阈值与性能目标。
- F6 的滚动窗口大小、延迟与重复文本处理策略。

### 5.4 假设与边界（已按确认结果更新）

1. 目标机器为 Windows 11 x64、Python 3.12、普通 CPU、内存 ≥8 GB、磁盘可用 ≥2 GB；可访问互联网完成首次模型下载。
2. 开发机为 macOS arm64，系统默认 `python3` 为 3.9；开发与测试必须显式使用 CPython 3.12 虚拟环境（当前可用 uv 管理的 3.12），不得用系统 3.9 代替目标环境。
3. 当前没有 Windows 11 实机；Windows 验证以 GitHub Actions `windows-latest` 为主，真实桌面/麦克风作为未验证项披露。
4. 面试官使用 Chrome 或 Edge 最新稳定版，通过 `http://127.0.0.1:8000` 访问；localhost 视为安全上下文。
5. 模型权重不进入 Git；首次运行前需执行下载脚本（README 显著说明）。
6. 录音上限 60 秒；上传上限 10 MB；服务端音频时长上限 120 秒。
7. 单用户、单进程；不做并发/多用户优化。
8. 不要求识别标点绝对准确、不要求说话人分离、不要求翻译。
9. 测试音频为本人录制，须注明授权且不含敏感个人信息。
10. F6 已确认要做，但仍受 G4/G5 门禁；未能完成时必须在报告中说明，不能虚报。

---

## 6. 计划自检

- [x] 题目 F1–F6、接口、环境、测试、手册、文档均已映射到模块与验收方式（第 3 节）。
- [x] 异常处理 8 类、浏览器录音格式、10 MB 限制、真实模型测试、断网验证均有独立任务（`todo.md` T2、T4、T5、T6）。
- [x] Mock 与真实模型测试分离，默认 `pytest -q` 不依赖模型/麦克风/外网。
- [x] F6 已确认要做，但仍设置 G4/G5 门禁与 3 小时时间盒；失败可回滚。
- [x] 无 Windows 11 实机的风险已披露，并安排 GitHub Actions 替代验证。
- [x] 未引入 Docker、Node.js、数据库等非必要基础设施。
- [x] 技术决策区分“已核实 / 未核实假设 / 需实验”，未把推测写成事实。
- [x] 计划与 `todo.md` 的任务编号、阶段、门禁一致（详见 `todo.md` 末尾核对项）。

---

## 7. 参考与核实记录

- 题目原文：`面试考核题-v1.md`。
- PyPI 元数据查询（2026-10-27）：
  - `faster-whisper 1.2.1`：要求 Python ≥3.9；依赖 `ctranslate2>=4,<5`、`av>=11`、`onnxruntime>=1.14,<2`、`huggingface-hub>=0.21`、`tokenizers>=0.13,<1`。
  - `ctranslate2 4.8.4`：存在 `cp312-cp312-win_amd64` wheel。
  - `av 19.0.2`：存在 `cp312-abi3-win_amd64` wheel，要求 Python ≥3.12。
  - `onnxruntime 1.31.1`：存在 `cp312-cp312-win_amd64` wheel。
  - `sherpa-onnx 2.0.1`（依赖 `sherpa-onnx-core 2.0.1`）：两者均存在 win_amd64 wheel（备选方案，未默认安装）。
- 说明：以上仅证明 PyPI 提供对应平台 wheel，**不代表**已在 Windows 11 实机完成安装与运行验证；Windows 兼容性列入 T6.10（GitHub Actions 替代）与 R1，真实 Windows 11 桌面/麦克风列入 R19。
- faster-whisper 官方仓库（SYSTRAN/faster-whisper）：CPU int8、VAD、语言参数与本地模型加载能力的依据；实现时在 `docs/design.md` 补充具体链接与版本。
- SenseVoice 官方 README：非自回归、同参数量下宣称比 Whisper-small 快 5 倍以上、支持中英粤日韩、自带 LID/ITN；权重使用 FunASR Model Open Source License（与 Whisper 的 MIT 不同）。上述为官方资料，非本机实测。
- sherpa-onnx 官方文档：支持 Windows x64 与 SenseVoice Python API；官方提供 VAD + SenseVoice 的近实时示例。若触发 T3.11，再补充实测记录。

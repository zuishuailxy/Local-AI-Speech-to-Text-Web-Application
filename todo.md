# Local AI Speech-to-Text Web Application 实施任务清单

- 对应计划：`plan.md` v0.1
- 编制日期：2026-10-27
- 状态说明：`[x]` 表示已完成；`[ ]` 表示待执行。**只有实际执行并通过验证后才勾选。**
- 使用方式：按编号顺序执行；每个阶段结束做一次提交与留痕；门禁未通过不得进入下一阶段或 F6 加分功能。
- 时间基线：2 个自然日、约 18–22 小时有效工时；F6 已确认要做，但仅在 G4 通过、文档基线完成且剩余 ≥3.5 小时时启动。

---

## 阶段 P0：规划与基线

- [x] **T0.1 完整读取并拆解考核题**
  - 目标：提取 F1–F6、接口、环境、测试、文档与提交要求，识别范围边界。
  - 文件：`面试考核题-v1.md`（只读）、`plan.md`。
  - 前置：无。
  - 完成标准：F1–F5、F6、三个接口、Windows 启动、pytest、6 项手动验证、5 份文档全部有对应条目。
  - 验证：对照题目第 2–9 节逐项检查，无遗漏。

- [x] **T0.2 编制实施计划与任务清单**
  - 目标：形成技术方案、验收映射、两天排期、风险与任务拆解。
  - 文件：`plan.md`、`todo.md`。
  - 前置：T0.1。
  - 完成标准：计划包含模型选型对比、事实/假设区分、必做/加分/不做范围、风险与决策分类；任务含目标/文件/前置/完成标准/验证。
  - 验证：交叉检查 `plan.md` 与 `todo.md` 的阶段、编号、门禁一致。

- [x] **T0.3 确认关键决策（用户）**
  - 目标：确认 D1 Windows 验证条件、D2 模型规模、D3 样本来源、D4 交付/脱敏范围、D5 是否预留 F6。
  - 文件：`plan.md`（已更新 0.1/5.3）、`docs/issue-log.md`。
  - 前置：T0.2。
  - 完成标准：D1–D7 均有明确结论；未决项标注默认方案与影响。
  - 验证：D1 无 Windows 11 实机；D2 small；D3 本人录音；D4 Git 仓库；D5 做实时识别；D6 GitHub；D7 模型路线 A；已回填计划。
  - 结论：已完成（2026-10-27）。D6 的本地提交见 T0.6，push 后 remote/Actions 验证见 T0.7；D7 见 T3.11。

- [x] **T0.4 冻结规划基线并初始化版本管理**
  - 目标：建立可追溯的起点。
  - 文件：`.gitignore`（在 T1.1 补齐）、`README.md`（用户已有占位）、`docs/opencode/` 目录。
  - 前置：T0.3。
  - 完成标准：`git init` 完成；首个提交包含题目、计划、任务清单；`.gitignore` 由 T1.1 补齐。
  - 验证：用户已执行 `git init` 并完成 initial commit（`42485f6`）；当前 `main` 干净。
  - 备注：`.gitignore` 与目录骨架仍由 T1.1 完成；`.DS_Store` 当前未跟踪，需在 T1.1 忽略。

- [x] **T0.5 导出规划阶段 OpenCode 会话**
  - 目标：保存“需求理解与技术设计”阶段证据。
  - 文件：`docs/opencode/01-requirements-and-design.md`、`docs/opencode/README.md`。
  - 前置：T0.3（脱敏规则确定）。
  - 完成标准：包含需求拆解、模型对比、方案选择、计划生成的关键对话；已移除绝对路径/用户名/密钥；包含 D1–D7 决策与 SenseVoice 对比。
  - 验证：文件可读；人工检查无敏感信息；与 `docs/ai-development.md` 的阶段一描述一致。
  - 结果：已完成（2026-10-27），使用会话 `ses_e838f4101ffet1mEwSYEGuuSMK` 的关键消息摘录；未包含内部推理/工具原始输出。

- [x] **T0.6 本地提交规划阶段产物（push 由用户手动执行）**
  - 目标：把计划、任务清单与阶段一证据提交到本地 Git，不执行 push。
  - 文件：`plan.md`、`todo.md`、`docs/opencode/README.md`、`docs/opencode/01-requirements-and-design.md`。
  - 前置：T0.5。
  - 完成标准：上述文件全部进入本地提交；`models/`、`.venv/`、缓存、密钥、`.DS_Store` 未进入提交；不配置 remote、不 push。
  - 验证：`git log --oneline -3` 可见本阶段提交；`git status` 干净（除未跟踪的本地文件）。
  - 备注：用户明确要求“只提交，手动 push”；remote/Actions 验证见 T0.7。

- [x] **T0.7 用户 push 后确认 GitHub remote**
  - 目标：确认本地提交已到达 GitHub，为 T1.8 创建 Actions 做准备。
  - 文件：Git remote 配置、`docs/evidence/t0.7-git.txt`。
  - 前置：T0.6；用户已手动 push。
  - 完成标准：`git remote -v` 显示 GitHub `origin`；本地 `main` 与 `origin/main` 一致；GitHub 页面可见提交。
  - 验证：`git fetch origin` 后 `git rev-parse HEAD origin/main` 均为 `421e460`；`git status -sb` 显示 `## main...origin/main`。
  - 备注：Actions 的实际运行验证并入 T1.8（当前尚无 workflow）；T0.7 只确认 remote/push。

---

## 阶段 P1：项目脚手架与可启动空服务（门禁 G1 准备）

- [x] **T1.1 建立目录结构与基础文件**
  - 目标：按计划创建 `app/`、`static/`、`scripts/`、`tests/`、`samples/`、`docs/` 等骨架。
  - 文件：目录、`app/__init__.py`、`app/api/__init__.py`、`app/services/__init__.py`、`.gitignore`、`.python-version`、各空目录 `.gitkeep`。
  - 前置：T0.4。
  - 完成标准：目录与 `plan.md` 2.2 一致；`.gitignore` 排除 `models/`、`.venv/`、`__pycache__/`、`.pytest_cache/`、`.wheelhouse-check/`、`*.log`、`.DS_Store` 等。
  - 验证：`find` 输出归档到 `docs/evidence/t1.1-skeleton.txt`；`git check-ignore` 抽查通过。
  - 结果：已完成（2026-10-27）；`.github/workflows/` 目录已预留，workflow 文件由 T1.8 创建。

- [x] **T1.2 创建 Python 3.12 虚拟环境、锁定依赖并预检 Windows wheel**
  - 目标：保证开发与目标环境一致（Python 3.12），并验证 Windows 11 可仅用 pip 安装。
  - 文件：`.venv/`（不提交）、`requirements.txt`、`.python-version`、`docs/evidence/windows-wheels.txt`、`docs/evidence/t1.2-environment.txt`。
  - 前置：T1.1。
  - 完成标准：使用 CPython 3.12 创建 `.venv`（本机系统 `python3` 为 3.9，禁止直接使用）；`python --version` 为 3.12.x；包含 fastapi、uvicorn、python-multipart、faster-whisper、pytest、httpx、websockets（F6 用）等运行/测试依赖并锁定可兼容版本；无 Docker/Node/DB/云 SDK；交叉下载检查所有包存在 cp312/abi3 win_amd64 wheel。
  - 验证：`.venv/bin/python --version` 输出 3.12.13；`pip download --only-binary=:all: --platform win_amd64 --python-version 3.12 --implementation cp --abi cp312 -r requirements.txt` 成功（41 个 wheel）；干净临时 venv 按 requirements 复装并导入关键模块成功；`pip check` 无冲突。
  - 结果：已完成（2026-10-27）；`requirements.txt` 为 41 个精确锁版本；模型权重未下载。

- [x] **T1.3 实现配置模块**
  - 目标：集中管理模型路径、设备、线程、大小/时长限制、预热开关。
  - 文件：`app/config.py`、`tests/test_config.py`、`docs/evidence/t1.3-config.txt`。
  - 前置：T1.1。
  - 完成标准：`plan.md` 2.3.4 的环境变量均有默认值；路径使用 `pathlib.Path`；可从测试覆盖；非法布尔/整数 fail fast；相对模型路径按项目根解析。
  - 验证：`python -m pytest -q tests/test_config.py`（21 passed）；默认值、环境变量覆盖、相对/绝对路径、布尔/整数校验均覆盖。
  - 结果：已完成（2026-10-27）；`Settings` 为 frozen dataclass，提供 `max_upload_bytes` 与 `supported_languages`。

- [x] **T1.4 实现应用工厂、静态页面与健康检查**
  - 目标：`create_app()` 可注入假引擎；`GET /health` 与 `GET /` 可用。
  - 文件：`app/main.py`、`app/api/routes.py`、`static/index.html`、`tests/test_health.py`、`tests/test_app_factory.py`、`docs/evidence/t1.4-app-health.txt`。
  - 前置：T1.2、T1.3。
  - 完成标准：`GET /health` 返回 200 且 JSON 为 `{"status":"ok"}`；`GET /` 返回 HTML；静态资源可访问；生产入口仍为 `app.main:app`；导入不加载模型。
  - 验证：`python -m pytest -q`（29 passed）；实际 uvicorn 启动后 `/health` 200、`/` 200。
  - 结果：已完成（2026-10-27）；transcriber 通过 `app.state.transcriber` 注入，默认 None。

- [x] **T1.5 实现统一错误模型与异常处理器**
  - 目标：所有可预期错误返回 `{"detail","code"}`，不泄漏堆栈。
  - 文件：`app/errors.py`、`app/main.py`、`tests/test_errors.py`、`docs/evidence/t1.5-errors.txt`。
  - 前置：T1.4。
  - 完成标准：覆盖 400/413/415/422/500/503 映射；未捕获异常返回 `internal_error`；日志记录异常类型。
  - 验证：触发各错误码的测试；响应 JSON 结构与状态码断言；10 passed。
  - 结果：已完成（2026-10-27）；定义 ApiError、ModelUnavailableError、TranscriptionFailedError、InvalidAudioError，并统一处理 404/405/422。

- [x] **T1.6 配置 pytest（Mock/真实模型隔离）**
  - 目标：`python -m pytest -q` 默认不加载模型、不下载、不依赖麦克风。
  - 文件：`pytest.ini`、`tests/conftest.py`、`tests/test_fixtures.py`、`docs/evidence/t1.6-pytest.txt`。
  - 前置：T1.4、T1.5。
  - 完成标准：注册 `real_model`、`e2e` 标记；默认排除两者；提供 `FakeTranscriber` 与生成 WAV 的 fixture；`pythonpath` 指向仓库根。
  - 验证：`python -m pytest -q`（47 passed，无模型/麦克风/下载）；临时 real_model probe 默认被排除，`pytest -q -m real_model` 可单独运行（1 passed）；probe 已删除。
  - 结果：已完成（2026-10-27）；G1 已在 T2.5 完成后通过。

- [x] **T1.7 P1 阶段收尾**
  - 目标：提交脚手架并留痕。
  - 文件：Git 提交、`docs/opencode/02-implementation.md`、`docs/evidence/t1.7-p1-summary.txt`、`docs/opencode/README.md`。
  - 前置：T1.1–T1.6。
  - 完成标准：`git status` 干净；提交信息说明脚手架/配置/健康检查；记录本阶段命令与问题。
  - 验证：`git log --oneline -5`；`python -m pytest -q`（47 passed）；阶段二记录与证据已归档。
  - 结果：已完成（2026-10-27）；G1 已在 T2.5 完成后通过。

- [x] **T1.8 建立 GitHub Actions Windows CI 骨架**
  - 目标：在无 Windows 实机条件下尽早发现 Windows 安装/导入问题。
  - 文件：`.github/workflows/windows.yml`、`docs/evidence/t1.8-windows-ci.txt`。
  - 前置：T0.7 确认 GitHub 可用；T1.2；用户 push。
  - 完成标准：workflow 使用 `windows-latest` + Python 3.12，执行 `pip install -r requirements.txt`、`pip check`、关键模块导入、`python -m pytest -q`；支持 push/PR/手动触发；失败日志可在 Actions 页面查看。
  - 验证：YAML 本地解析通过；本地等价步骤通过；GitHub Actions run `40483713787`（commit `fc8e7f9`）在 `windows-latest` / Python 3.12 上 success，全部 step success。
  - 结果：已完成（T1.8 骨架）。T1.4 的 uvicorn/health 与 T6.10 的真实模型/Playwright 步骤后续再加入 workflow。
  - 备注：公开 API 可读取 run/job/step 状态；完整日志下载需 admin，未伪造日志；run URL 见 `docs/evidence/t1.8-windows-ci.txt`。

---

## 阶段 P2：音频处理、识别接口与 Mock 测试

- [x] **T2.1 实现上传参数与格式校验**
  - 目标：校验 `file`、`language`、空文件、扩展名白名单。
  - 文件：`app/services/audio.py`、`app/errors.py`、`tests/test_audio.py`、`docs/evidence/t2.1-audio-validation.txt`。
  - 前置：T1.5。
  - 完成标准：`language` 仅接受 `zh`/`en`（扩展值另行门禁）；空文件 400；非白名单 415；缺失字段 422；错误信息可读。
  - 验证：pytest 覆盖 `.txt`、伪 wav、空文件、非法语言、缺字段；15 passed；全量 62 passed。
  - 结果：已完成（2026-10-27）；增加 EmptyFileError / UnsupportedFormatError / InvalidLanguageError；WAV 头早期校验，其他容器留给 T2.3 解码。
  - 备注：生产 `/api/transcribe` 路由在 T2.7 接线，当前用等价测试路由验证 FastAPI 缺失字段行为。

- [x] **T2.2 实现流式写入与 10 MB 上限**
  - 目标：避免一次性读入超大文件，服务端强制执行 10 MB。
  - 文件：`app/services/audio.py`、`app/main.py`、`app/errors.py`、`tests/test_audio.py`、`docs/evidence/t2.2-upload-limit.txt`。
  - 前置：T2.1。
  - 完成标准：分块读取并累计字节；超过 `MAX_UPLOAD_MB` 返回 413 并清理临时文件；Content-Length 预检作为第一道防线。
  - 验证：构造 10 MB+1 请求返回 413；临时目录无残留；24 passed；全量 71 passed。
  - 结果：已完成（2026-10-27）；`save_upload_to_temp` 使用 TemporaryDirectory + 1 MiB 分块；`StoredUpload.cleanup()`/上下文管理器负责清理；中间件只拦截 `/api/transcribe`。
  - 备注：允许 multipart 边界 1 MiB overhead，精确文件大小在复制时二次校验；生产路由 T2.7 接线。

- [x] **T2.3 实现 PyAV 解码、重采样与时长上限**
  - 目标：任意受支持容器统一解码为 16 kHz 单声道 float32，并计算实际时长。
  - 文件：`app/services/audio.py`、`app/errors.py`、`tests/test_audio.py`、`docs/evidence/t2.3-decode.txt`。
  - 前置：T2.2。
  - 完成标准：WAV/webm 可解码；时长为采样点数/16000；超过 `MAX_AUDIO_SECONDS` 提前中止并返回 400；损坏文件返回 400；0 帧返回 400；临时文件在 Windows 下可删除。
  - 验证：生成 1 秒/5 秒 WAV、静音 WAV、损坏字节、0 帧、超长 WAV、WebM/Opus fixture；32 passed；全量 79 passed；Windows CI 运行同一测试集。
  - 结果：已完成（2026-10-27）；`decode_audio` 使用 PyAV AudioResampler（flt/mono/16000），先检查容器 duration，再按实际样本数二次限制；静音保留采样，0 帧报 invalid_audio；WebM fixture 解码通过。
  - 备注：T2.6 将补充浏览器录音格式的完整验收记录；临时文件清理与全路径收口见 T2.4。

- [x] **T2.4 统一音频错误码与清理逻辑**
  - 目标：确保所有异常路径释放句柄、删除临时文件、返回一致错误。
  - 文件：`app/services/audio.py`、`app/errors.py`、`tests/test_audio.py`、`docs/evidence/t2.4-cleanup.txt`。
  - 前置：T2.3。
  - 完成标准：`finally` 清理；异常不泄漏堆栈；错误码与 `plan.md` 2.3.3 一致。
  - 验证：成功/解码失败/超时长/超大小四条路径后临时目录为空；36 passed；全量 83 passed；HTTP 路由返回 400 audio_too_long、400 invalid_audio、413 file_too_large。
  - 结果：已完成（2026-10-27）；新增 `process_audio_upload` 作为统一 save→decode→finally cleanup 边界；容器与临时文件均用 with 关闭。
  - 备注：Windows CI run `40504918267`（commit `8f31ebc`）为 success，已确认临时文件测试在 windows-latest 通过。

- [x] **T2.5 Mock 层音频单元测试**
  - 目标：覆盖正常/空/损坏/超长/静音。
  - 文件：`tests/conftest.py`、`tests/test_audio.py`、`docs/evidence/t2.5-audio-tests.txt`。
  - 前置：T2.1–T2.4。
  - 完成标准：测试不依赖样本文件/麦克风；生成 WAV 使用标准库；静音用例返回 0 帧或空文本路径明确。
  - 验证：`python -m pytest -q tests/test_audio.py`（41 passed）；全量 88 passed；矩阵覆盖 normal/silent/empty/corrupt/too_long，且每条路径临时目录为空。
  - 结果：已完成（2026-10-27）；静音 WAV 明确解码为 16000 个零采样（不是空文件），后续 VAD/ASR 返回空文本的路径由 T2.7/T3 验证；G1 通过。
  - 备注：WAV 全部由标准库生成；WebM fixture 仅用于容器格式测试，不依赖麦克风或 `samples/`。

- [x] **T2.6 浏览器录音格式（webm）解码测试**
  - 目标：证明后端可处理前端实际录音格式。
  - 文件：`tests/fixtures/sample.webm`、`tests/fixtures/README.md`、`tests/test_audio.py`、`docs/evidence/audio-format.txt`。
  - 前置：T2.3。
  - 完成标准：提交一个短 webm/opus fixture（由 WAV 转码或浏览器录制，注明来源）；解码成功且时长合理；不要求运行期安装 ffmpeg。
  - 验证：`pytest -q tests/test_audio.py`（42 passed）；WebM/Opus 容器、1s 时长、16 kHz mono float32 解码；`PATH=/usr/bin:/bin` 排除系统 ffmpeg 后仍通过；全量 89 passed。
  - 结果：已完成（2026-10-27）；fixture 为项目自生成 1 秒合成 Opus，SHA-256 记录在证据中；真实浏览器 MIME/上传仍由 T6.8/T6.11 手动验证。
  - 备注：系统 `/usr/local/bin/ffmpeg` 存在但不可执行（bad CPU type）；测试证明解码只依赖 PyAV wheel 自带库。

- [x] **T2.7 实现 Transcriber 协议、假引擎与 `POST /api/transcribe` 契约测试**
  - 目标：打通 multipart → 校验 → 解码 → 引擎 → JSON 全链路，并定义可注入的识别协议。
  - 文件：`app/services/transcriber.py`、`app/schemas.py`、`app/api/routes.py`、`tests/test_transcribe_api.py`、`tests/test_language.py`、`docs/evidence/t2.7-transcribe-api.txt`。
  - 前置：T2.5。
  - 完成标准：定义 `Transcriber.transcribe(...)` 与 `ModelUnavailableError`；成功响应含 `text/language/duration_seconds/processing_seconds`；`duration_seconds` 来自真实解码；`processing_seconds` 为服务端耗时；中英文均返回；非法语言 400。
  - 验证：24 个接口/语言测试通过；全量 113 passed；curl 上传 WebM 返回 200 与四字段；非法语言 400；缺字段 422；格式/空文件/伪 WAV/超时长/无模型/推理异常/空文本均有测试。
  - 结果：已完成（2026-10-27）；`Transcriber` 通过 `app.state.transcriber` 注入，`run_in_threadpool` 调用；临时文件在模型调用前已由 `process_audio_upload` 清理。
  - 备注：当前假引擎只验证契约；真实模型接入与真实文本在 T3.2/T3.6。

- [x] **T2.8 错误路径与重试语义测试**
  - 目标：模型加载失败 503、推理失败 500、空文本 200、请求可重试。
  - 文件：`app/services/transcriber.py`、`tests/test_errors.py`、`tests/test_transcribe_api.py`、`docs/evidence/t2.8-error-retry.txt`。
  - 前置：T2.7。
  - 完成标准：Fake 抛 `ModelUnavailableError` → 503 `model_unavailable`；抛其他异常 → 500 `transcription_failed`；空文本 → 200 且 `text == ""`；错误响应含可读 `detail`；失败后可重试。
  - 验证：37 passed（transcribe/language/errors）；全量 116 passed；500→200、503→200、400→200 三种重试路径通过；错误响应 detail 非空且不泄漏异常原文。
  - 结果：已完成（2026-10-27）；FakeTranscriber 支持 `errors` 序列模拟瞬时失败；API 无状态，重试不会污染下一请求。
  - 备注：前端错误展示与重试按钮在 T4.8 联调；真实模型失败恢复在 T3.2/T3.8。

- [x] **T2.9 P2 阶段收尾**
  - 目标：提交后端音频/接口/Mock 测试。
  - 文件：Git 提交、`docs/evidence/p2-test-output.txt`、`docs/opencode/02-implementation.md`、`docs/opencode/README.md`。
  - 前置：T2.1–T2.8。
  - 完成标准：`pytest -q` 全绿；无模型下载；阶段问题记录。
  - 验证：全量 116 passed；`models/` 文件数 0；P2 的 8 个 Windows CI run 均 success；阶段二记录已更新 P2。
  - 结果：已完成（2026-10-27）；G1 已通过；生产 `/api/transcribe` 仍需 P3 接入真实模型，默认无 transcriber 时返回 503。

---

## 阶段 P3：真实本地 ASR 集成（门禁 G2）

- [x] **T3.1 完善识别协议、结果对象与假实现**
  - 目标：业务层不依赖 faster-whisper 具体类，便于测试/替换。
  - 文件：`app/services/transcriber.py`、`tests/conftest.py`、`tests/test_transcriber.py`、`docs/evidence/t3.1-transcriber-protocol.txt`。
  - 前置：T2.7。
  - 完成标准：`Transcriber.transcribe(audio: np.ndarray, language: str) -> TranscriptionResult`（或等价签名）稳定；Fake 可配置文本/异常/延迟；真实实现独立。
  - 验证：7 个 transcriber 测试通过；全量 123 passed；Fake 满足 runtime_checkable Protocol；导入模块不会加载 faster-whisper。
  - 结果：已完成（2026-10-27）；Fake 支持固定文本、持久异常、异常序列恢复、delay_seconds、calls 记录；真实引擎留给 T3.2。

- [x] **T3.2 实现 faster-whisper 引擎**
  - 目标：本地目录加载、CPU int8、语言参数、VAD、线程与锁、惰性单例。
  - 文件：`app/services/transcriber.py`、`app/config.py`、`tests/test_transcriber_unit.py`、`docs/evidence/t3.2-whisper-engine.txt`。
  - 前置：T3.1、T1.3。
  - 完成标准：仅从 `ASR_MODEL_PATH` 加载；不传模型名；`device=cpu`、`compute_type=int8`；`language=zh/en`；`vad_filter` 可配置；并发加载只发生一次；加载失败转 `ModelUnavailableError`。
  - 验证：8 个单元测试通过；全量 131 passed；缺失路径/加载失败→503，推理失败→500，空文本保留，4 线程并发只加载一次；导入模块不加载 faster-whisper。
  - 结果：已完成（2026-10-27）；`WhisperTranscriber` 惰性加载、单锁串行化、本地路径、CPU/int8/threads/beam/VAD 从 Settings 读取；默认工厂内部延迟导入 WhisperModel。
  - 备注：真实模型推理尚未执行；下载/加载/中英文验证见 T3.5/T3.6。

- [x] **T3.3 实现模型下载脚本**
  - 目标：一次性下载到 `models/faster-whisper-small`，支持镜像与校验。
  - 文件：`scripts/download_model.py`、`README.md`、`tests/test_download_model.py`、`docs/evidence/t3.3-download-script.txt`。
  - 前置：T1.2。
  - 完成标准：`--model small`、`--output` 可用；下载后校验关键文件；失败给出 `HF_ENDPOINT`/手动放置提示；不把权重写入 Git。
  - 验证：10 个脚本单测通过；全量 147 passed；CLI help 正常；注入 fake downloader 验证参数与校验；README 模型章节已补；T3.5 增加 ModelScope 源。
  - 结果：已完成（2026-10-27）；支持 HuggingFace 与 ModelScope；校验 model.bin/config.json/tokenizer.json/vocabulary.*；下载失败给出镜像/手动放置提示。
  - 备注：实际网络下载、复用与体积记录在 T3.5；`.gitignore` 已排除 `models/`。

- [x] **T3.4 实现 CLI 冒烟验证脚本**
  - 目标：不启动 Web 也能验证真实模型中英文。
  - 文件：`scripts/verify_asr.py`、`tests/test_verify_asr.py`、`docs/evidence/t3.4-verify-cli.txt`。
  - 前置：T3.2、T3.3。
  - 完成标准：`python scripts/verify_asr.py samples/chinese.wav --language zh` 输出文本/时长/耗时；支持 en；模型缺失时给出可操作错误。
  - 验证：6 个脚本测试通过；全量 145 passed；CLI help、缺文件、非法语言、模型缺失提示、Fake 成功输出均验证。
  - 结果：脚本完成（2026-10-27）；修复 scripts 目录下 `app` 不在 sys.path 的启动问题（显式插入项目根）。
  - 备注：真实 `samples/chinese.wav` / `english.wav` 已用下载的 small 模型运行，输出见 `docs/evidence/model-download.txt` 与 `sample-audio-check.txt`。

- [x] **T3.5 下载 small 模型并记录实验数据**
  - 目标：完成首次模型准备，取得真实基线。
  - 文件：`models/`（不提交）、`docs/evidence/model-download.txt`、`docs/evidence/sample-audio-check.txt`。
  - 前置：T3.3、网络可用。
  - 完成标准：模型文件完整；记录下载耗时、体积、来源、日期；记录目标 CPU/内存。
  - 验证：ModelScope `Systran/faster-whisper-small` 下载完成；强制复测 real 25.60s；468 MB；M1/16 GB；中英文真实推理成功。
  - 结果：已完成（2026-10-27）；model.bin 483,546,902 bytes，SHA-256 `3e3059...d671`；文件完整，模型权重未进 Git；首次加载与中英文 CLI 输出已归档。
  - 备注：HuggingFace/hf-mirror 当前超时，使用 ModelScope 公共源；断网重启验证留给 T6.9。

- [x] **T3.6 真实模型中英文首轮验证与选型确认**
  - 目标：确认 small 的文本质量/速度，决定是否回退 base 或评估 SenseVoice。
  - 文件：`docs/evidence/asr-baseline.md`、`samples/chinese.wav`、`samples/english.wav`、`samples/reference.txt`。
  - 前置：T3.5、用户录音样本。
  - 完成标准：中文、英文各至少 1 条文本；记录耗时、RTF、明显错误（简繁/标点/幻觉）；给出“维持 small / 回退 base / 换模型”的结论。
  - 验证：真实模型 3 次推理中位数；中文 CER 0.231、RTF 0.286；英文 WER 0.000、RTF 0.179；模型加载 0.987s。
  - 结果：维持 **small / CPU int8 / beam 5 / VAD on**；英文准确，中文有同音错误但可辨认且在 CER ≤0.3 内；不触发 SenseVoice 评估。
  - 门禁：**G2 通过**（中英文均非空、可辨认，数据已记录）。

- [x] **T3.7 接入真实引擎到 `/api/transcribe`**
  - 目标：路由使用真实引擎，响应口径符合契约。
  - 文件：`app/api/routes.py`、`app/main.py`、`app/services/transcriber.py`、`tests/test_app_factory.py`、`tests/test_transcriber_unit.py`、`docs/evidence/t3.7-real-api.txt`。
  - 前置：T2.7、T3.2。
  - 完成标准：真实请求走本地模型；`processing_seconds` 含解码、模型加载（若首次请求触发）与推理，不含首次下载；模型加载耗时另记日志；请求间无状态。
  - 验证：真实 uvicorn 下中文 4.456s→3.484s（首次含加载）、英文 1.674s，均 200；文本与 CLI 一致；连续请求成功；149 passed。
  - 结果：已完成（2026-10-27）；生产 `app` 创建 `WhisperTranscriber` 但不在导入时加载；`create_app()` 默认仍不注入引擎；`model_load_seconds` 日志由 caplog 测试覆盖。
  - 备注：uvicorn 默认 INFO 日志级别可能不显示加载日志；不影响响应与计时。

- [x] **T3.8 真实模型异常路径**
  - 目标：模型缺失/损坏/推理失败均可理解。
  - 文件：`app/services/transcriber.py`、`tests/test_transcribe_api.py`、`docs/evidence/model-failure.txt`。
  - 前置：T3.7。
  - 完成标准：临时重命名模型目录 → 503 且提示下载脚本；推理异常 → 500；服务不崩溃，恢复目录后可继续识别。
  - 验证：真实服务缺失/损坏模型均 503，/health 仍 200；恢复目录后 POST 200；真实引擎适配器推理异常→500；全量 150 passed。
  - 结果：已完成（2026-10-27）；模型未缓存失败状态，恢复后重新加载成功；临时备份已还原。

- [x] **T3.9 完善 Mock API 测试矩阵**
  - 目标：在不依赖真实模型的情况下覆盖 API 契约与错误。
  - 文件：`tests/test_transcribe_api.py`、`tests/test_language.py`、`tests/test_errors.py`、`docs/evidence/t3.9-mock-api-matrix.txt`。
  - 前置：T3.7。
  - 完成标准：健康检查、正常中英文、缺 file、缺 language、非法 language、空文件、损坏、超 10 MB、不支持格式、超时长、模型 503、推理 500、空文本全部覆盖。
  - 验证：新增损坏 WebM 与 10 MB+1 API 测试；152 passed；矩阵逐项映射到测试文件。
  - 结果：已完成（2026-10-27）；Mock 测试不加载真实模型、不下载权重、不访问麦克风。

- [x] **T3.10 P3 阶段收尾**
  - 目标：提交真实模型集成与实验数据。
  - 文件：Git 提交、`docs/opencode/02-implementation.md`、`docs/opencode/README.md`、`docs/evidence/p3-test-output.txt`。
  - 前置：T3.1–T3.9。
  - 完成标准：真实模型不进入 Git；实验数据可追溯；`pytest -q` 仍不触发下载。
  - 验证：152 passed；`git ls-files models` 为空；模型目录 4 个文件约 468 MB；P3 7 个 Windows run 均 success；阶段二记录已更新 P3。
  - 结果：已完成（2026-10-27）；真实模型与样本数据完整，T3.11 未触发。

- [ ] **T3.11 条件触发：sherpa-onnx + SenseVoiceSmall 时间盒评估（非必做）**
  - 状态：**未触发**（G2 已通过、small 中英文可辨认、RTF 可接受；不占用时间）。
  - 目标：在 Whisper 中文/速度或 F6 延迟不达标时，用 60–90 分钟判断是否切换备选模型。
  - 文件：`scripts/spike_sensevoice.py`、`docs/evidence/model-bakeoff.md`、`docs/issue-log.md`。
  - 前置：T3.6 失败或 F6 实测延迟不可接受；G4 不因此延期；用户/时间允许。
  - 完成标准：安装 sherpa-onnx、获取 int8 ONNX 模型（sherpa-onnx 转换版）、跑中英文样本；记录 CER/WER、RTF、ITN 输出、WebM 解码；给出“切换/不切换”结论；若切换，只改 `Transcriber` 实现，API/前端不动；许可证与模型来源写入 `docs/design.md`。
  - 验证：对照 T3.6 的 Whisper 数据；时间盒内未完成则放弃并保留 Whisper；不提交模型权重。
  - 门禁：不阻塞 P4/P5；若切换，必须重跑 T5.2/T5.3/T6.x 相关验证。

---

## 阶段 P4：前端页面与交互

- [x] **T4.1 实现页面结构与视觉状态**
  - 目标：语言选择、录音区、上传区、状态区、结果区、错误区齐全。
  - 文件：`static/index.html`、`static/styles.css`、`tests/test_frontend_structure.py`、`docs/evidence/t4.1-frontend-structure.txt`。
  - 前置：T1.4。
  - 完成标准：桌面布局清晰；按钮含 Start/Stop Recording；显示当前语言、状态、计时、结果、复制；无外部字体/CDN。
  - 验证：5 个结构测试通过；全量 157 passed；`/` 与 `/static/styles.css` 200；必需 ID、hidden/disabled 初始状态、aria/label、无外链均断言。
  - 结果：已完成（2026-10-27）；响应式布局、录音脉冲、pipeline/状态样式已定义；交互逻辑留给 T4.2。

- [x] **T4.2 实现麦克风采集与 MediaRecorder**
  - 目标：授权后录音，停止后得到可上传 Blob。
  - 文件：`static/app.js`、`static/index.html`、`tests/test_frontend_recording.py`、`docs/evidence/t4.2-media-recorder.txt`、`docs/evidence/t4.1-page.png`。
  - 前置：T4.1。
  - 完成标准：`getUserMedia` 音频约束；按能力选择 webm/ogg/mp4；`timeslice` 收集分片；停止后合并 Blob；释放轨道；记录实际 MIME。
  - 验证：5 个 JS 静态契约测试 + 全量 162 passed；浏览器控制台无 error；`chooseMimeType()` = `audio/webm;codecs=opus`；Node 仅做语法检查。
  - 结果：已完成（2026-10-27）；`window.__lastRecording` 暴露 Blob/MIME/扩展名/大小；空 Blob 报错；Start/Stop 状态切换。
  - 备注：自动化环境未完成真实麦克风授权，实际录音与 Network multipart 验收待 T4.6/T6.1；不伪造录音结果。

- [x] **T4.3 实现计时、60 秒自动停止与状态机**
  - 目标：状态与时长准确，超限自动结束。
  - 文件：`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.3-timer-state.txt`、`docs/evidence/t4.3-auto-stop.png`。
  - 前置：T4.2。
  - 完成标准：`idle/requesting/recording/transcribing/success/error` 文案与按钮禁用正确；每 200 ms 更新；60 秒自动 stop 并提示；`visibilitychange` 校正。
  - 验证：假麦克风+虚拟时钟模拟 60 秒，phase=success、recordedMs=60000、timer=01:00.0、stoppedByLimit=true、track 已 stop；6 个前端录音测试/全量 163 passed。
  - 结果：已完成（2026-10-27）；Start/Stop 按钮由状态机统一控制；计时使用 Date.now 差值；后台节流回前台会补检 60 秒上限。
  - 备注：真实 5 秒/60 秒/切后台手动录音待 T6.1/T6.7；本轮不伪造真实麦克风音频。

- [x] **T4.4 实现麦克风与录音异常提示**
  - 目标：权限拒绝、无设备、设备占用、非安全上下文、MediaRecorder 错误均有明确提示。
  - 文件：`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.4-error-handling.txt`、`docs/evidence/t4.4-error-state.png`。
  - 前置：T4.2。
  - 完成标准：按 `DOMException.name` 映射中文提示与恢复建议；处理 `MediaRecorder.onerror`、空 Blob/无数据；页面不崩溃；可重试。
  - 验证：模拟权限拒绝/无设备/占用/空 Blob/记录器错误均进入 error 状态且 Start 可用；关闭提示回 idle；重试可再次触发；7 前端测试/全量 164 passed。
  - 结果：已完成（2026-10-27）；新增 retry/dismiss 事件、recordingFailed 防覆盖、安全上下文检查。
  - 备注：真实 Chrome 权限/设备异常手动验收在 T6.5/T6.6；模拟不替代真实硬件。

- [x] **T4.5 实现文件上传**
  - 目标：选择 WAV/webm 等文件并提交，客户端预检。
  - 文件：`static/index.html`、`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.5-file-selection.txt`。
  - 前置：T4.1。
  - 完成标准：`accept` 覆盖格式；空文件/超 10 MB 前端提示；显示文件名/大小；上传复用 `/api/transcribe`；不因扩展名误判而绕过服务端校验。
  - 验证：浏览器模拟 wav/webm 选择成功；.txt/空文件/10MB+1 均被拒绝并可恢复；8 前端测试/全量 165 passed。
  - 结果：已完成（2026-10-27）；Upload 按钮默认 disabled，选中合法文件后启用；客户端校验仅作提示，服务端仍独立校验。
  - 备注：实际 `/api/transcribe` 请求/结果显示在 T4.6；本轮不发送网络请求。

- [x] **T4.6 实现请求、状态与结果展示**
  - 目标：调用 API 并展示全部必填字段。
  - 文件：`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.6-request-result.txt`、`docs/evidence/t4.6-real-result.png`。
  - 前置：T3.7、T4.5。
  - 完成标准：正确构造 `FormData`（file、language）；识别中显示已耗时；成功后展示文本、语言、音频时长、处理耗时；请求期间禁止重复提交。
  - 验证：真实浏览器上传中文/英文 WAV，均 200 并显示四字段；中文 4.38s/英文 1.70s；录音自动提交链路用假 MediaRecorder + 真实 WAV 验证；9 前端测试/全量 166 passed。
  - 结果：已完成（2026-10-28）；统一 submitAudio、processing timer、pipeline 状态、音频预览、空文本提示；错误保留最近提交供重试。
  - 备注：真实麦克风录音仍待 T6.1/T6.2；Edge 待 T6.11；Copy 与错误联调分别在 T4.7/T4.8。

- [x] **T4.7 实现复制功能**
  - 目标：一键复制识别文本。
  - 文件：`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.7-copy.txt`。
  - 前置：T4.6。
  - 完成标准：Clipboard API 成功提示；权限失败回退 textarea；空文本禁用。
  - 验证：真实浏览器上传后点击复制，捕获文本与结果一致；强制 Clipboard 失败后 execCommand 回退成功；10 前端测试/全量 167 passed。
  - 结果：已完成（2026-10-28）；按钮已复制反馈 1.6s；“复制失败”提示；空文本/重置时 disabled。

- [x] **T4.8 实现错误展示、重试与重置**
  - 目标：4xx/5xx 可读展示，失败后可重试/重新录音。
  - 文件：`static/app.js`、`tests/test_frontend_recording.py`、`docs/evidence/t4.8-error-retry-reset.txt`。
  - 前置：T4.6。
  - 完成标准：解析 `detail`/`code`；网络错误有提示；失败不丢失语言选择；重试按钮可用；成功后可再次录音/上传。
  - 验证：浏览器拦截 503 后显示 detail/code，语言/文件保留；重试第二次成功；网络 TypeError 显示连接提示；11 前端测试/全量 168 passed。
  - 结果：已完成（2026-10-28）；重试优先当前文件，否则最近录音；关闭提示回 idle；成功后 Start/Upload 恢复。
  - 备注：真实后端停止/模型目录改名与恢复在 T6.7；Edge 在 T6.11。

- [x] **T4.9 P4 阶段收尾与可访问性检查**
  - 目标：提交前端并做基础可用性检查。
  - 文件：Git 提交、`static/*`、`tests/test_frontend_accessibility.py`、`docs/evidence/frontend-smoke.txt`、`docs/opencode/02-implementation.md`、`docs/opencode/03-testing-and-fixes.md`。
  - 前置：T4.1–T4.8。
  - 完成标准：按钮/输入有 label 或 aria-label；键盘可操作；控制台无报错；`getUserMedia` 仅在点击后调用。
  - 验证：173 passed；浏览器无 error；Tab 顺序 language→Start→file；点击前 getUserMedia=0、点击后=1；error role=alert；audio 有 aria-label。
  - 结果：P4 已完成（2026-10-28）；用户 CSS 修改保留；OpenCode 阶段二记录补充 P4，阶段三测试/修复记录已生成。
  - 备注：真实麦克风、Edge、断网、Windows 11 实机仍在 P6；E2E 可选在 T5.4。

---

## 阶段 P5：样本、真实模型测试与自动化收口

- [x] **T5.1 录制并准备测试音频与参考文本**
  - 目标：提供本人录制、合法、清晰、5–15 秒的中英文 WAV。
  - 文件：`samples/chinese.wav`、`samples/english.wav`、`samples/reference.txt`、`docs/evidence/sample-audio-check.txt`。
  - 前置：用户已确认 D3 使用本人录音；T3.5 真实模型可识别。
  - 完成标准：16 kHz/单声道/PCM16（或明确说明）；各 5–15 秒；一至两句完整语音；`reference.txt` 含参考文本、录制人授权说明、时长、来源；注明“本人录制”，不含敏感个人信息；保留原始录音备份（不提交）。
  - 验证：wave 读取 Chinese 12.0s/English 9.0s、1ch/16-bit/16k；真实模型识别可辨认；用户已确认中文参考文本。
  - 结果：已完成（2026-10-27）；原始 M4A 保留本地并加入 `.gitignore`，仓库只提交派生 WAV/reference。
  - 备注：原始录音的录制环境未单独记录；reference 已注明来源与授权。

- [x] **T5.2 真实模型集成测试（中/英）**
  - 目标：用真实本地模型断言可识别且质量达标。
  - 文件：`tests/test_real_model.py`、`tests/sample_data.py`、`app/services/metrics.py`、`tests/test_metrics.py`、`tests/test_samples.py`、`pytest.ini`、`docs/evidence/t5.2-real-model.txt`。
  - 前置：T5.1、T3.5、T3.6。
  - 完成标准：`@pytest.mark.real_model`；模型缺失时 skip 并提示下载；中文/英文各断言非空、语言脚本合理；计算并打印 CER/WER 与耗时；阈值按首轮实测校准（初定中文 CER ≤0.3、英文 WER ≤0.3）。
  - 验证：`python -m pytest -q -m real_model tests/test_real_model.py` 2 passed；中文 CER 0.2308/RTF 0.262，英文 WER 0.0000/RTF 0.181；模型缺失时 2 skipped 且有下载提示；默认 188 passed、2 deselected。
  - 结果：已完成（2026-10-28）；新增 CER/WER 工具与 10 个指标单测、5 个样本完整性单测；参考文本与样本目录交叉校验。
  - 备注：样本对 T5.2 足够（中/英、5–15 s、参考已确认）；覆盖限于单人/安静/正常语速，未覆盖噪声、远场、混合语言，属增强项。

- [x] **T5.3 真实上传 API 流程测试**
  - 目标：验证“上传真实 WAV → 完整后端 → 文本”的端到端路径。
  - 文件：`tests/test_e2e_upload.py`（`real_model` 标记）、`tests/fixtures/speech-en.webm`、`tests/real_model_support.py`、`docs/evidence/t5.3-real-api.txt`。
  - 前置：T5.2、T3.7。
  - 完成标准：TestClient 上传中英文样本；断言 200、文本非空、language 回显、duration 与样本一致、processing_seconds ≥0；另测 webm fixture。
  - 验证：中文 200/12.0 s/processing 4.441 s/CER 0.2308；英文 200/9.0 s/1.686 s/WER 0；WebM 200/8.999 s/1.912 s/WER 0；3 passed；全部 real_model 5 passed；默认 188 passed、5 deselected。
  - 结果：已完成（2026-10-28）；新增本人录音派生的 `speech-en.webm`（PyAV/libopus），真实语音 WebM 走完整后端并得到非空文本。
  - 备注：TestClient 不经过真实 TCP/浏览器；真实浏览器上传仍以 T4.6/T6 为准。Windows CI 不跑真实模型。

- [x] **T5.4 Playwright 浏览器 E2E（Windows CI 需要，默认不随 `pytest -q` 执行）**
  - 目标：自动验证页面加载、文件上传、假麦克风录音，作为无 Windows 实机时的浏览器证据。
  - 文件：`tests/e2e/test_browser.py`、`requirements-e2e.txt`、`.github/workflows/windows.yml`、`docs/evidence/e2e.txt`、截图。
  - 前置：T5.3、T4.6。
  - 完成标准：`e2e` 标记，默认不执行；Chromium/Edge 使用 `--use-fake-device-for-media-stream` 与 WAV；覆盖页面加载 + 上传成功 + 录音后停止；不进入主 requirements；CI 中可单独执行。
  - 验证：本地 Chrome 156 3 passed；页面无相关 console error；上传结果字段正确；假麦克风录音 WebM/Opus 1.2 s+ 并成功；默认 196 passed、8 deselected；无浏览器时 3 skipped 且提示安装命令；Windows CI run `40633358118` 的 Run tests / Install browser E2E / Run browser E2E 均 success。
  - 结果：已完成（2026-10-28）；使用真实 uvicorn + FakeTranscriber，不依赖模型；Windows CI 增加安装 Chromium 与 `pytest -m e2e` 步骤。
  - 备注：首次 CI run `40633226986` 因默认测试收集 e2e 模块时缺少 playwright 而失败；最终改为在 `browser` fixture 内延迟导入，默认套件无需安装 Playwright，CI run `40633358118` 通过。假麦克风/FakeTranscriber 不等于真实麦克风/真实模型；真实麦克风在 T6.1/T6.2，真实模型在 T5.2/T5.3，Edge 在 T6.11。本机 Chromium 下载超时，本地用 `PLAYWRIGHT_CHANNEL=chrome`。

- [x] **T5.5 验证默认测试的隔离性与合规静态检查**
  - 目标：证明 `pytest -q` 不依赖模型/麦克风/外网，并确认未使用被禁止的云端 ASR/Web Speech。
  - 文件：`docs/evidence/pytest-default.txt`、`docs/evidence/compliance-check.txt`。
  - 前置：T2.5、T3.9、T5.2。
  - 完成标准：临时移走 `models/` 后在干净 venv 执行 `python -m pytest -q` 全绿；无下载日志；无麦克风访问；执行时间可接受；静态搜索确认前端无 `SpeechRecognition`/`webkitSpeechRecognition`，后端无 OpenAI/Azure/Google 云端 ASR SDK 或调用，无 CDN 依赖。
  - 验证：`.venv-t55`（41 个依赖）+ 模型移走 + 离线/代理阻塞，196 passed、8 deselected、2.73s；无下载输出、无 `models/`；模型恢复 464 MB。前端仅 MediaRecorder/getUserMedia、仅 fetch `/api/transcribe`、无 CDN；app 内无 openai/azure/google/urllib/socket，模型从本地路径加载。
  - 结果：已完成（2026-10-28）；默认套件不依赖 Playwright（e2e 延迟导入）、不加载模型、不访问麦克风或外网。
  - 备注：`scripts/download_model.py` 仍可通过 HuggingFace/ModelScope 准备模型，这是题目允许的一次性步骤；运行/识别路径不下载。

- [x] **T5.6 执行真实模型统一命令并归档**
  - 目标：满足“真实模型测试单独提供”。
  - 文件：`README.md`（Tests 章节）、`docs/evidence/pytest-real-model.txt`。
  - 前置：T5.2、T5.3、T3.5。
  - 完成标准：README 写明 `python -m pytest -q -m real_model`（或环境变量门控）；实际执行通过；记录真实文本与耗时。
  - 验证：`python -m pytest -q -m real_model -s` → 5 passed、199 deselected、17.73s；中文 WAV CER 0.2308、英文 WAV WER 0、WebM WER 0；模型缺失时 5 skipped 并提示下载。
  - 结果：已完成（2026-10-28）；README 增加默认/真实模型/浏览器 E2E 三组命令与预期输出；真实文本、耗时、RTF、加载时间已归档。
  - 备注：真实模型测试需本地权重，Windows CI 不执行；命令与 README 一致。

- [x] **T5.7 P5 阶段收尾**
  - 目标：提交样本、测试与结果。
  - 文件：Git 提交、`docs/evidence/p5-summary.txt`、`docs/opencode/03-testing-and-fixes.md`。
  - 前置：T5.1–T5.6。
  - 完成标准：样本/测试进 Git；模型权重/临时文件未进 Git；测试输出归档。
  - 验证：`git status` 干净；`git ls-files samples` 仅 WAV/reference/.gitkeep；`git ls-files models .wheelhouse-check` 为 0；33 个 samples/tests 文件已跟踪；样本 SHA-256 已归档。
  - 结果：已完成（2026-10-28）；P5 总结见 `docs/evidence/p5-summary.txt`；默认 196 passed/8 deselected、真实模型 5 passed、E2E 3 passed。

- [x] **T5.8 识别语言核对与全链路日志（横切，提前执行）**
  - 目标：确认语言参数端到端生效，并为应用、请求、音频、识别、错误接入可诊断日志。
  - 文件：`app/config.py`、`app/main.py`、`app/api/routes.py`、`app/services/audio.py`、`app/services/transcriber.py`、`app/errors.py`、`scripts/verify_asr.py`、`tests/test_logging.py`、`docs/evidence/t5.8-language-and-logging.txt`、`README.md`。
  - 前置：T5.3（接口/模型链稳定）。
  - 完成标准：语言从页面到模型全程可追踪；`LOG_LEVEL` 可配置；请求带 request_id 与耗时；识别日志含请求/检测语言、脚本占比、推理耗时、文本长度；不记录音频/文本原文；4xx/5xx 有 code。
  - 验证：196 passed、8 deselected；真实模型 5 passed；真实 uvicorn 日志含 request_id、language、duration、text_chars；识别文本不出现在日志。
  - 结果：已完成（2026-10-28）；语言参数确实传入并影响解码，但 Whisper small 在音频与所选语言不一致时不强制目标语言；新增 output_language 脚本占比与 mismatch 警告，页面提示改为“请选择与音频一致的语言”。
  - 备注：强制输出目标语言/自动检测留给 T8.1；当前保持四字段契约不变。

---

## 阶段 P6：手动验证、离线与 Windows（门禁 G4）

- [x] **T6.1 手动：Chrome 麦克风录制中文并识别**
  - 目标：验证 F1 + F3 中文主流程。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/mic-zh.png`、`docs/evidence/t6.1-mic-zh.txt`。
  - 前置：T4.9、T5.1。
  - 完成标准：授权、录音、计时、停止、识别、文本展示全流程成功；记录音频时长/处理耗时/文本。
  - 验证：Chrome 156 真实麦克风，8.16 s 中文；页面 8.2 s / 1.71 s；文本“今天天气很好,我们开始测试本地语音识别系统。”；简体；忽略标点 CER 0.0；控制台无报错；截图 `mic-zh.png`。
  - 结果：已完成（2026-10-28）；修复 Whisper 繁体输出（新增本地 `zhconv` 繁转简）后复测通过；早期 10.5 s 录音的繁体/同音字问题已记录。

- [x] **T6.2 手动：Chrome 麦克风录制英文并识别**
  - 目标：验证英文主流程。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/mic-en.png`、`docs/evidence/t6.2-mic-en.txt`。
  - 前置：T6.1。
  - 完成标准：英文模式识别成功；输出为英文；记录耗时。
  - 验证：Chrome 156 真实麦克风 7.14 s；页面 7.1 s / 2.59 s；文本“Never give up. Never lose hope. Always have faith.”；WER 0.0；输出英文；截图 `mic-en.png`。
  - 结果：已完成（2026-10-28）；发现并修复 favicon 404（新增 `static/favicon.svg`），浏览器 E2E 改为断言 0 console error。

- [x] **T6.3 手动：上传中文 WAV**
  - 目标：验证 F2 + F3 中文上传。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/upload-zh.png`、`docs/evidence/t6.3-upload-zh.txt`。
  - 前置：T5.1。
  - 完成标准：选择 `samples/chinese.wav` 上传成功；结果与参考文本一致/接近。
  - 验证：Chrome 156 上传 `chinese.wav`（375 KB）；12.0 s；页面 3.98 s（服务端 3.978 s）；CER 0.2308；文本含占如/抓手/做别/金牛/西洋近音错误；截图 `upload-zh.png`。
  - 结果：已完成（2026-10-28）；真实模型上传链路正常，输出简体，无空文本/幻觉；favicon 404 已消失。

- [x] **T6.4 手动：上传英文 WAV**
  - 目标：验证英文上传。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/upload-en.png`、`docs/evidence/t6.4-upload-en.txt`。
  - 前置：T6.3。
  - 完成标准：`samples/english.wav` 上传成功；输出英文。
  - 验证：Chrome 156 上传 `english.wav`（281.3 KB）；9.0 s；页面 1.45 s（服务端 1.447 s）；输出与参考完全一致；WER 0.0；截图 `upload-en.png`。
  - 结果：已完成（2026-10-28）；首次截图误存中文结果，已重新截图确认。

- [x] **T6.5 手动：麦克风权限被拒绝**
  - 目标：验证 F5 权限异常。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/permission-denied.png`、`docs/evidence/t6.5-permission-denied.txt`。
  - 前置：T4.4。
  - 完成标准：Chrome 站点设置阻止麦克风后点击录音；页面显示明确权限提示；无崩溃；恢复权限后可录音。
  - 验证：Chrome 156 禁止麦克风后提示“麦克风权限被拒绝时，请检查浏览器地址栏的站点权限后重试。”；Error 状态、Pipeline 失败、Start 可重试；未发起无效请求；恢复后 3 s 录音提交 200（静音空文本）。
  - 结果：已完成（2026-10-28）；截图 `permission-denied.png`。

- [x] **T6.6 手动：无可用麦克风/设备不可用**
  - 目标：验证 `NotFoundError`/`NotReadableError` 分支。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/t6.6-no-mic.txt`、`docs/evidence/device-not-found.png`、`docs/evidence/device-in-use.png`。
  - 前置：T4.4。
  - 完成标准：禁用系统输入设备或占用麦克风；页面提示“未检测到麦克风/设备被占用”；上传识别仍可用。
  - 验证：Chrome DevTools 注入 NotFoundError → “未检测到可用麦克风，请连接麦克风后重试。”；注入 NotReadableError → “麦克风无法读取，可能被其他程序占用。”；两种均 Error/Pipeline 失败、Start 可重试、无后端请求；刷新恢复后可录音（4.08 s，200）。
  - 结果：已完成（2026-10-28，模拟）；本机只有内置麦克风且无法安全禁用，证据明确标注为 DevTools 注入，不冒充真实拔设备。
  - 备注：真实 NotFound/NotReadable 仍需在可禁用/拔掉麦克风的设备补验；上传不受影响已由 T6.3/T6.4 验证。

- [x] **T6.7 手动：异常上传与空语音**
  - 目标：覆盖空文件、损坏、格式、超 10 MB、静音、超时长、模型不可用。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/error-cases.txt`、`docs/evidence/auto-stop-60s.png`。
  - 前置：T4.8、T2.5。
  - 完成标准：每类场景均有明确提示且页面可继续操作；静音返回空文本/提示；模型不可用 503 提示下载/检查；另验证录音达到 60 秒时自动停止并给出提示。
  - 验证：`.txt`/空文件/>10 MB 客户端拦截；损坏 WAV 400 invalid_audio；静音 200 空文本；125 s WAV 400 audio_too_long；模型缺失 503；60 s 用户实测计时 01:00.0、自动停止提交，页面 57.2 s、processing 0.312 s、空文本。
  - 结果：已完成（2026-10-28）；6 个上传分支用 Playwright 驱动真实页面/后端，60 s 为用户真实麦克风。发现计时 60.0 s 与服务端音频 57.18 s 差约 2.8 s，已记录为已知问题，未超过 60 s 上限。
  - 备注：模型目录已恢复；错误分支页面均可重试/关闭。

- [x] **T6.8 手动：复制、重试、再次录音、上传 webm**
  - 目标：验证 F4 复制、失败恢复、连续识别，以及 F2 浏览器录音格式上传。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/upload-webm.txt`、`docs/evidence/upload-webm.png`。
  - 前置：T6.1–T6.4。
  - 完成标准：复制文本与页面一致；失败后重试成功；连续两次录音/上传均成功；在页面上传 webm fixture（或浏览器录制的 webm）识别成功。
  - 验证：`speech-en.webm` 8.999 s / 1.438 s / WER 0；剪贴板 SHA-256 与页面一致；停 8001 后网络错误，重启点“重试”复用同一 WebM，8.999 s / 2.446 s 成功；连续录音见 T6.1/T6.2，连续上传见 T6.3/T6.4。
  - 结果：已完成（2026-10-28）；重试未重新选文件，错误面板关闭；截图 `upload-webm.png`。

- [x] **T6.9 断网验证（核心）**
  - 目标：证明模型准备完成后完全离线识别。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/offline.txt`、`docs/evidence/offline-zh.png`、`docs/evidence/offline-en.png`。
  - 前置：T5.6、T6.1–T6.4。
  - 完成标准：断开网络/禁用网卡；设置 `HF_HUB_OFFLINE=1` 后重启服务；中英文各完成一次麦克风或上传识别；无外网请求；耗时正常。
  - 验证：真实关闭 Wi-Fi；HF_HUB_OFFLINE=1 重启；中文 12.0 s / 4.357 s / CER 0.1795；英文 9.0 s / 1.359 s / WER 0；模型本地加载 1.021 s；页面无网络错误，Network 无外部请求。
  - 结果：已完成（2026-10-28）；截图显示 Wi-Fi 关闭；用户消息的 2.14 s 与截图/日志 4.36 s 不一致，以截图/日志为准。
  - 备注：日志另有一次 en+chinese.wav 误选请求，不计入本项结果。

- [x] **T6.10 Windows 兼容性验证（GitHub Actions 替代，最高风险）**
  - 目标：在没有 Windows 11 实机的情况下，尽可能验证 Windows x64 + Python 3.12 的安装、启动与识别链路。
  - 文件：`.github/workflows/windows.yml`、`docs/test-report.md`（后续汇总）、`docs/evidence/windows-ci.txt`。
  - 前置：T0.7/T1.8（GitHub Actions 可用）；T1.2、T5.1、T5.4、T6.1–T6.9。
  - 完成标准：`windows-latest` 上全新 venv 执行 `pip install -r requirements.txt`；启动 uvicorn；`/health` 200；运行默认 pytest；下载真实模型并上传中英文样本成功；Playwright 使用 Chromium/Edge 假麦克风完成页面加载 + 上传 + 录音流程；记录 Python/浏览器版本、安装耗时、模型加载/推理耗时；无缺失 DLL/编译错误。
  - 验证：Run `40651179705`（首次真实模型）与 `40651812439`（缓存命中）均 success；Python 3.12.10、Edge 155.0.4283.62；模型下载 136 s；中文 12.0 s / 5.503 s / load 1.295 s；英文 9.0 s / 4.354 s / load 1.289 s；默认测试 + Chromium E2E + real_model 5 项 + Edge E2E 3 项全绿。
  - 结果：已完成（2026-10-28）；首次失败为 Windows cp1252 打印中文导致 UnicodeEncodeError，已设 PYTHONUTF8/PYTHONIOENCODING 并加 HF/hf-mirror 回退。
  - 备注：CI 是 Windows Server，不是 Windows 11 桌面；假麦克风/headless Edge 不等于真实桌面/麦克风，报告中必须披露。

- [x] **T6.11 Edge 兼容性验证（本地/CI）**
  - 目标：覆盖题目要求的 Chrome/Edge 最新稳定版。
  - 文件：`docs/test-report.md`（后续汇总）、`docs/evidence/edge.txt`。
  - 前置：T6.1–T6.4；T6.10（CI）。
  - 完成标准：Edge 打开页面、上传、识别、复制；记录实际 MediaRecorder MIME；有 Windows CI 时用 Playwright Edge 通道跑页面/上传；无 Windows 实机时在 macOS Edge 做 UI 验证并注明环境差异。
  - 验证：Windows CI Edge 155.0.4283.62 `3 passed`；页面加载、WAV 上传、复制（clipboard 文本一致）、假麦克风 WebM 录音；Run `40658826426` success。
  - 结果：已完成（2026-10-28，CI headless）；本机 macOS 未安装 Edge，桌面 Edge/真实麦克风未验证。
  - 备注：headless Edge + 假麦克风不等于 Windows 11/macOS 桌面 Edge 实机；最终报告需披露。

- [x] **T6.12 P6 阶段收尾与证据归档**
  - 目标：汇总手动/离线/Windows 结果，形成测试报告初稿。
  - 文件：`docs/test-report.md`、`docs/evidence/`、Git 提交、`docs/opencode/03-testing-and-fixes.md`。
  - 前置：T6.1–T6.11。
  - 完成标准：6 项指定手动验证全部有结果；Windows CI 结果与真实 Windows 未验证项分开记录；已知问题分级；证据文件命名可追溯；失败项有修复记录或明确说明。
  - 验证：6 项手动验证全部通过；干净环境 203 passed；真实模型 5 passed；E2E 3 passed；Windows CI 真实模型/Chromium/Edge 通过；测试报告已列已知问题与 G4 表。
  - 结果：已完成（2026-10-28）；G4 通过（Windows 11 实机/桌面 Edge/真实麦克风未验证，已明确披露）。
  - 门禁：**G4 通过（带限制披露）**；F6 仍需 G5 与文档基线。

- [ ] **T6.13 条件项：Windows 11 实机/云 VM 补验（无环境则记录阻塞）**
  - 目标：若借用/租用 Windows 11，补做真实桌面 Chrome/Edge 麦克风验证。
  - 文件：`docs/test-report.md`、`docs/evidence/windows11-real.txt`、截图。
  - 前置：可获得 Windows 11 x64 实机或云 VM；T6.10 通过。
  - 完成标准：按 README 启动；Chrome/Edge 录音中文/英文成功；上传样本；记录版本与耗时。
  - 验证：逐字执行 README；截图 + 命令输出。
  - 结果：**阻塞**（2026-10-28）；当前无 Windows 11 实机/云 VM，未执行，不计为通过。
  - 备注：Windows CI 是 Windows Server；真实桌面/麦克风仍需补验；不阻塞 G4（G4 以 Windows CI 替代）。

---

## 阶段 P7：文档、OpenCode 证据与交付

- [x] **T7.1 编写 README.md**
  - 目标：让面试官按文档独立复现。
  - 文件：`README.md`。
  - 前置：T6.12。
  - 完成标准：系统介绍、环境要求（Python 3.12、Windows 11、内存/磁盘）、安装、模型初始化（含离线/镜像）、启动、使用、API 示例、测试（默认/真实模型）、离线验证、故障排查、已知限制、项目结构；明确 Windows CI 替代验证与真实 Windows 11 未验证项。
  - 验证：README 覆盖安装/启动/模型/使用/API/配置/测试/离线/排障/限制/结构/证据；命令与当前 203/8、5 real、3 e2e、干净 203/2.53s 一致；Windows/ModelScope/镜像/离线命令齐全。
  - 结果：已完成（2026-10-28）；README 明确 Windows CI 是 Server、真实 Windows 11/桌面 Edge/真实麦克风未验证；已知问题含 60 s 音频 57.18 s、繁简与同音字、语言错配。

- [x] **T7.2 编写 docs/requirements.md**
  - 目标：记录需求理解、拆分、假设、边界。
  - 文件：`docs/requirements.md`。
  - 前置：T0.3。
  - 完成标准：F1–F6 逐项理解；必做/加分/不做；假设（60/120 秒、10 MB、单用户等）；验收标准；与 `plan.md` 一致。
  - 验证：F1–F6 逐项映射到实现/验证；必做/加分/不做分层；假设含 60/120 秒、10 MB、单用户、离线、语言错配；验收 A1–A9 与题目第 9 节对应；D1–D7 与 plan 一致。
  - 结果：已完成（2026-10-28）；F6 明确为门禁后加分项且当前未实现；Windows 11/桌面 Edge/无设备模拟/60 s 差异均列为已知差异。

- [x] **T7.3 编写 docs/design.md**
  - 目标：说明架构、模块、音频流程、模型选型与理由、错误码、限制。
  - 文件：`docs/design.md`。
  - 前置：T6.12。
  - 完成标准：含架构图/时序（文本或 Mermaid）、模块职责、请求流程、模型对比与最终选择、CPU/离线策略、错误码表、并发与安全边界、未验证项。
  - 验证：Mermaid 架构、模块表、录音/上传/识别流程、PyAV 音频细节、Whisper small 选型/备选、错误码表、锁/单进程、安全/隐私、官方资料链接齐全；与代码/README 一致。
  - 结果：已完成（2026-10-28）；明确单进程单模型锁、10 MB/120 s 双限制、zhconv 只处理 zh、Windows/Edge/60 s 差异等限制。

- [x] **T7.4 编写 docs/test-report.md（最终版）**
  - 目标：记录实际执行的测试与结果。
  - 文件：`docs/test-report.md`。
  - 前置：T5.6、T6.12。
  - 完成标准：环境信息；Mock 用例表；真实模型用例（文本、CER/WER、耗时）；6 项手动验证；异常/离线/Windows CI/Edge；真实 Windows 11 未验证项；F6 结果；已知问题与限制；命令输出路径。
  - 验证：203 个默认用例分布表；真实模型 5 项；6 项手动；Windows CI/Edge；F6 明确未实现；未验证项表；证据路径；所有“通过”有对应文件。
  - 结果：已完成（2026-10-28）；修正 `pytest-default.txt` 为最终 42 依赖/203 passed，并在 e2e 证据注明历史 196 快照。

- [x] **T7.5 编写 docs/ai-development.md**
  - 目标：回答题目 5 个问题并展示 AI Programming 能力。
  - 文件：`docs/ai-development.md`。
  - 前置：T7.6。
  - 完成标准：OpenCode 承担的任务；人工做出的关键决策（模型、限制、错误策略等）；遇到的问题与修复；如何验证 AI 代码；后续优化优先级；三阶段证据索引。
  - 验证：覆盖 OpenCode 任务、D1–D7/人工决策、12 个真实问题、8 层验证、7 项优化优先级、三阶段索引；与 `docs/opencode/`、Git/证据一致。
  - 结果：已完成（2026-10-28）；明确 AI 生成代码经人工运行/审查修正，未把 CI/假麦克风写成实机通过。

- [ ] **T7.6 导出/脱敏三阶段 OpenCode 会话**
  - 目标：提供可审计的开发过程证据。
  - 文件：`docs/opencode/01-requirements-and-design.md`、`02-implementation.md`、`03-testing-and-fixes.md`、`README.md`。
  - 前置：各阶段会话已存在；T0.5。
  - 完成标准：三阶段齐全；含关键命令、失败与修复；脱敏（路径/用户名/密钥/无关隐私）；索引说明日期、模型、范围。
  - 验证：全文搜索敏感词；人工通读；链接/文件可打开。

- [ ] **T7.7 整理问题修复记录**
  - 目标：形成可追溯的 issue log。
  - 文件：`docs/issue-log.md`。
  - 前置：开发过程中持续记录。
  - 完成标准：每个问题含现象、复现、定位、修复、验证、相关提交；至少包含一次真实测试失败/修复案例（满足阶段三要求）。
  - 验证：与 `ai-development.md`、Git 提交对应。

- [ ] **T7.8 最终 Git 整理与回归**
  - 目标：交付干净、可复现的仓库。
  - 文件：Git 历史、tag、`.gitignore`。
  - 前置：T7.1–T7.7。
  - 完成标准：分阶段提交可读；配置 GitHub remote（D4）；无模型权重/venv/缓存/密钥/大文件；最终 `pytest -q` 全绿；打必做版 tag（如 `v1.0-must-have`）；若进入 P8，P9 再打最终 tag（如 `v1.0-submission`）。
  - 验证：`git status`、`git ls-files`、`git count-objects -vH`；干净克隆后跑测试；远程仓库可访问。

- [ ] **T7.9 打包交付（如需压缩包）**
  - 目标：提供无需 Git 也可运行的交付物。
  - 文件：`local-speech-to-text.zip`（仓库外或按约定）。
  - 前置：T7.8。
  - 完成标准：排除 `models/`、`.venv/`、缓存；包含源码/样本/文档；解压后按 README 可启动；记录校验和。
  - 验证：解压到新目录，执行安装/启动/健康检查。

---

## 阶段 P8：加分功能 F6（已确认要做，严格门禁）

> **启动条件（全部满足）**：G4 所有必做验收通过；`pytest -q` 与真实模型测试通过；Windows CI/离线/文档基线完成；剩余至少 3.5 小时；有独立提交可回滚。未满足则冻结必做版本，在 `docs/test-report.md` 标注“F6 未完成（门禁未通过）”并说明原因。

- [ ] **T8.0 F6 门禁检查**
  - 目标：确认不会因实时识别伤害必做交付。
  - 文件：`docs/issue-log.md`。
  - 前置：T7.8（或至少 T6.12 + 文档基线）。
  - 完成标准：逐项勾选 G5；记录剩余时间、3 小时时间盒与回滚方案。
  - 验证：未满足任一项则停止，不创建 F6 代码。

- [ ] **T8.1 条件项：自动语言检测（低成本加分，F6 之后）**
  - 目标：支持中英文混合/自动识别。
  - 文件：`app/services/transcriber.py`、`app/api/routes.py`、`static/app.js`、`tests/test_language.py`、`docs/design.md`。
  - 前置：T8.0；F6 主流程稳定后。
  - 完成标准：额外接受 `language=auto`（zh/en 契约不变）；自动检测；响应返回检测语言；页面增加“自动”选项；非法值仍 400。
  - 验证：中英文样本自动识别；zh/en 回归；文档标注为扩展。
  - 备注：如实现成本超 45 分钟或影响契约，放弃并记录。

- [ ] **T8.2 实时识别后端（WebSocket + PCM 分片）**
  - 目标：接收 PCM 分片并用本地模型滚动转写。
  - 文件：`app/api/ws.py`、`app/services/streaming.py`、`app/main.py`、`tests/test_ws.py`。
  - 前置：T8.0。
  - 完成标准：WebSocket 协议定义清晰（采样率/格式/分片/结束）；复用当前主引擎；滚动窗口策略与最终全文策略明确；错误可关闭连接并提示；不影响 `/api/transcribe`。
  - 验证：Mock 单测；真实模型手动说话看到中间文本；停止后最终文本完整。

- [ ] **T8.3 实时识别前端**
  - 目标：录音过程中持续显示文本。
  - 文件：`static/app.js`、`static/index.html`、`static/styles.css`。
  - 前置：T8.2。
  - 完成标准：AudioWorklet 或 ScriptProcessor 采集 16 kHz 单声道 PCM；分片发送；中间结果更新；停止发送结束帧并展示最终文本；麦克风权限/断线错误可处理。
  - 验证：Chrome 实时说中文/英文；观察文本更新；停止后最终结果与上传识别接近。

- [ ] **T8.4 实时识别测试与回归**
  - 目标：证明 F6 不破坏必做。
  - 文件：`tests/test_ws.py`、`docs/test-report.md`、`docs/design.md`。
  - 前置：T8.3。
  - 完成标准：WS Mock 测试通过；`pytest -q` 全绿；真实模型实时手动验证记录；必做 6 项抽测不回归。
  - 验证：全量回归 + 手动演示。

- [ ] **T8.5 实时识别失败回滚**
  - 目标：时间不足/不稳定时安全放弃。
  - 文件：Git revert/feature flag、`docs/issue-log.md`、`docs/test-report.md`。
  - 前置：T8.2–T8.4 任一失败或超时。
  - 完成标准：必做功能恢复到 G4 状态；文档说明 F6 未完成原因；不留下半成品入口。
  - 验证：`pytest -q` + 手动主流程复测。

---

## 阶段 P9：终验与交付确认

- [ ] **T9.1 干净环境按 README 复现**
  - 目标：验证交付物可独立复现。
  - 文件：`docs/evidence/final-repro.txt`。
  - 前置：T7.9（或 T7.8）；若进入 P8，则还需 T8.4 或 T8.5 完成。
  - 完成标准：新目录/新 venv；执行 `python -m pip install -r requirements.txt`；执行 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`；`/health` 200；页面可开；上传识别成功。
  - 验证：逐字照 README；记录耗时/问题。

- [ ] **T9.2 必做需求逐项核对**
  - 目标：确保 F1–F5、接口、环境、测试、文档无遗漏。
  - 文件：`docs/test-report.md`、`plan.md` 第 3 节。
  - 前置：T9.1。
  - 完成标准：每条需求有“实现位置 + 验证证据”；F6 必须写明“已完成并演示”或“未完成及原因”，不能空泛带过；Windows 实机未验证单独标注。
  - 验证：双人/自查逐行核对；无“计划即通过”的表述。

- [ ] **T9.3 文档/代码/任务一致性检查**
  - 目标：避免计划、实现、测试报告互相矛盾。
  - 文件：`plan.md`、`todo.md`、`README.md`、`docs/*.md`。
  - 前置：T9.2。
  - 完成标准：启动命令、接口字段、错误码、限制值、模型名、测试命令一致；任务依赖无环；已完成项均有证据。
  - 验证：搜索关键数字（60/120/10 MB/small/int8）与命令；对照检查。

- [ ] **T9.4 最终交付与汇报**
  - 目标：形成提交说明与后续建议。
  - 文件：最终 Git tag/压缩包、`docs/ai-development.md`。
  - 前置：T9.1–T9.3。
  - 完成标准：交付物清单齐全；已知问题与未验证项透明；给出后续优化优先级（准确率、实时性、性能、UI）。
  - 验证：按题目第 7、9 节清单最终核对；冻结代码。

---

## 交付前总检查（Definition of Done）

- [ ] `python -m pytest -q` 在无模型、无麦克风、无外网环境通过。
- [ ] `python -m pytest -q -m real_model` 使用真实本地模型通过（中英文），输出已归档。
- [ ] 6 项手动验证全部实际执行并记录，不把“计划执行”写成“已通过”。
- [ ] 断网后中英文识别成功。
- [ ] Windows CI（`windows-latest`）按题目命令安装/启动并完成 API/真实模型/假麦克风验证；真实 Windows 11 桌面/麦克风未验证时明确标注。
- [ ] `samples/chinese.wav`、`english.wav`、`reference.txt` 为本人录制、合法、可播放、5–15 秒。
- [ ] README、requirements、design、test-report、ai-development 五份文档齐全且一致。
- [ ] OpenCode 三阶段证据脱敏、可读、与 Git 时间线对应。
- [ ] 仓库无模型权重、虚拟环境、缓存、密钥；Git 工作区干净。
- [ ] F1–F5、三个接口、异常 8 类、10 MB 限制全部通过；F6 完成并演示，或明确记录未完成原因。

---

## 任务依赖速查

```text
P0（规划/决策，含 D6 仓库/CI）
  └─> P1（脚手架/配置/健康检查/pytest/Windows CI 骨架）
        └─> P2（音频/接口/Mock 测试）
              ├─> P3（真实模型/下载/真实 API；T3.11 条件评估）──> G2
              └─> P4（前端录音/上传/展示）──┐
                                             ├─> P5（样本/真实测试）
                                             └─> P6（手动/离线/Windows CI）──> G4
                                                   └─> P7（文档/证据/交付）
                                                         ├─> P8（F6 实时识别，仅 G5 通过）─┐
                                                         └─────────────────────────────────┴─> P9（终验）
```

注意：P3 与 P4 可在 P2 完成后并行；P6 的 Windows 验证使用 GitHub Actions 替代实机，若 D6 不可用，先做其余项并将 Windows 标为未验证风险，不得默认为通过。P8 已确认要做，但只有 G5 通过才启动。

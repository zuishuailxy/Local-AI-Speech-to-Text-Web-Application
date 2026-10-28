# 需求说明（Requirements）

- 文档版本：v1.0（P7 交付版）
- 日期：2026-10-28
- 输入依据：`面试考核题-v1.md`、`plan.md`、实际实现与测试结果
- 关联文档：`README.md`、`docs/design.md`、`docs/test-report.md`、`docs/opencode/`

## 1. 背景与目标

构建一个本地部署的 Web 语音转文字应用：

- 浏览器麦克风录音或上传音频
- 后端使用本地开源 ASR 模型，在 CPU 上识别中文普通话/英语
- 页面展示语言、状态、文本、音频时长、处理耗时，并支持复制
- 模型准备完成后可完全离线运行
- 不依赖云端 ASR、浏览器 Web Speech API、Docker、Node.js、数据库或 CUDA

目标用户是需要在普通开发电脑上验证本地语音识别能力的面试官/开发者。

## 2. 角色与使用场景

| 角色 | 场景 |
| --- | --- |
| 本机用户 | 打开 `http://127.0.0.1:8000`，选择语言，录一段中文/英文并识别 |
| 本机用户 | 上传已有 WAV/WebM 文件，独立验证识别 |
| 开发者/面试官 | 按 README 安装依赖、下载模型、运行 pytest、检查真实模型与离线结果 |
| CI | 在 Windows Server 安装依赖、跑测试、下载真实模型、跑 Playwright Chromium/Edge |

单用户、本机使用；不做登录、权限管理、多用户并发、历史记录。

## 3. 功能需求

### F1 浏览器麦克风录音（必做）

| 编号 | 需求 | 当前实现 |
| --- | --- | --- |
| F1.1 | 用户点击 Start 后才请求麦克风权限 | 是；不在页面加载时调用 `getUserMedia` |
| F1.2 | Start/Stop 控制录音 | 是 |
| F1.3 | 显示录音状态和录音时长 | 是；200 ms 计时，`00:00.0` |
| F1.4 | 一次录音最长 60 秒，到时自动停止 | 是；`visibilitychange` 补检 |
| F1.5 | 停止后才提交该次完整音频 | 是；`MediaRecorder.stop` 后合并 Blob |
| F1.6 | 权限拒绝/无设备/占用/空 Blob 等给出原因 | 是；前端错误面板 |
| F1.7 | 一次识别完成后可再次录音 | 是；成功后控件恢复 |
| F1.8 | 录音失败不应崩溃或误提交 | 是；`recordingFailed` 守卫 |

验证：T6.1（中文）、T6.2（英文）、T4.3/T4.4 单测与 E2E。

### F2 音频文件上传（必做）

| 编号 | 需求 | 当前实现 |
| --- | --- | --- |
| F2.1 | 至少支持 WAV | 是 |
| F2.2 | 支持浏览器实际录音格式 | 是；WebM/Opus（同时支持 OGG/MP3/M4A/MP4/FLAC） |
| F2.3 | 上传与麦克风共用后端识别逻辑 | 是；均走 `POST /api/transcribe` → `process_audio_upload` → `Transcriber` |
| F2.4 | 不支持的格式/损坏音频给出提示 | 是；415 `unsupported_format`、400 `invalid_audio` |
| F2.5 | 上传大小上限 | 10 MB；Content-Length + 流式双重限制，413 `file_too_large` |
| F2.6 | 解码后时长上限 | 120 秒；400 `audio_too_long` |
| F2.7 | 上传后展示文件名/大小/结果 | 是 |

验证：T6.3、T6.4、T6.8、T6.7、`tests/test_audio.py`。

### F3 本地中英文语音识别（必做）

| 编号 | 需求 | 当前实现 |
| --- | --- | --- |
| F3.1 | 本地开源模型 | faster-whisper Whisper small（CTranslate2） |
| F3.2 | CPU 推理 | `device=cpu`、`compute_type=int8`、4 threads |
| F3.3 | 中文识别 | 是；页面选择 `zh` |
| F3.4 | 英文识别 | 是；页面选择 `en` |
| F3.5 | 不做翻译 | 使用 `task=transcribe`（默认），不调用翻译任务 |
| F3.6 | 结果返回页面 | 四字段 JSON |
| F3.7 | 可连续识别 | 是；模型复用，请求间无状态 |
| F3.8 | 模型准备后离线 | 是；T6.9 真实关闭 Wi-Fi |
| F3.9 | 不使用云端 ASR | 静态检查无 OpenAI/Azure/Google 等 SDK/调用 |
| F3.10 | 不使用 Web Speech API | 仅 `getUserMedia` + `MediaRecorder` |
| F3.11 | 中文输出简体 | 本地 `zhconv` 繁转简；英文不转换 |
| F3.12 | 语言参数生效 | 传入模型并影响解码；不保证音频/选择错配时强制目标脚本 |

说明：

- 题目 F3 的正常路径是“选中文说中文、选英文说英文”；这两条已通过真实模型/手动验证。
- Whisper 的 `language=zh` 只约束语言，不约束简繁；音频与选择不一致时可能输出源语言，日志记录 `asr_language_mismatch`，当前不改变四字段契约。
- 同音字错误（如“招手→抓手”）是 small 模型能力限制，不通过繁转简修复。

验证：T5.2、T5.3、T6.1、T6.2、T6.9。

### F4 识别结果展示（必做）

| 编号 | 需求 | 当前实现 |
| --- | --- | --- |
| F4.1 | 显示当前识别语言 | 页面语言选择 + 结果 `language` |
| F4.2 | 显示状态 | idle/requesting/recording/transcribing/success/error |
| F4.3 | 显示识别文字 | 文本区；空文本显示专门提示 |
| F4.4 | 显示音频时长 | `duration_seconds` |
| F4.5 | 显示处理耗时 | `processing_seconds`；请求中 100 ms 计时 |
| F4.6 | 识别过程有明确反馈 | pipeline 5 步 + 状态 + 计时 |
| F4.7 | 可复制文字 | Clipboard API + `execCommand` 回退 |
| F4.8 | 可播放预览 | `<audio controls>` + Blob URL |

验证：T4.1、T4.6、T4.7、T6.1–T6.4、T6.8、E2E。

### F5 异常处理（必做）

| 场景 | 预期 | 当前实现 |
| --- | --- | --- |
| 拒绝麦克风权限 | 提示，不崩溃 | `NotAllowedError` → 权限提示；T6.5 |
| 未检测到麦克风 | 明确错误 | `NotFoundError` 分支；T6.6（DevTools 模拟） |
| 设备被占用 | 明确错误 | `NotReadableError` 分支；T6.6（模拟） |
| 空文件/损坏音频 | 拒绝并提示 | 400 `empty_file` / `invalid_audio`；T6.7 |
| 格式不支持 | 明确提示 | 客户端预检 + 415 `unsupported_format`；T6.7 |
| 录音超过 60 秒 | 自动结束 | 60 s 自动 stop + 提示；T6.7 |
| 模型加载失败 | 可理解错误 | 503 `model_unavailable`；T6.7 |
| 识别后端出错 | 提示并允许重试 | 500 `transcription_failed`；T4.8/T6.8 |
| 无语音 | 空结果/提示 | 200 空文本 + “未检测到可识别语音”；T6.7 |
| 上传 >10 MB | 拒绝 | 前端预检 + 413 `file_too_large` |

补充：

- 前端客户端校验不替代服务端校验。
- 失败后保留语言/已选文件/最近提交，重试优先当前文件，否则最近录音。
- 网络断开显示“无法连接后端…”，恢复后可重试。

### F6 实时语音识别（加分，门禁后）

题目列为可选；D5 已确认“要做”。G5 门禁通过后已完成并合并到 `main`；Windows CI 通过。

范围（若进入 P8）：

1. 点击 Start 后持续采集 PCM（16 kHz mono）
2. WebSocket/分片发送
3. 后端滚动窗口转写，页面持续更新中间文本
4. 停止后输出最终文本
5. 不破坏现有 `/api/transcribe` 与 F1–F5

未满足条件时冻结必做版本，并在测试报告标注“F6 未完成（门禁未通过）”，不得挤占 Windows/离线/文档。

自动语言检测（`language=auto`）已实现：HTTP/WS/页面支持；返回检测到的 `zh`/`en`；zh/en 原契约不变，其他非法值仍 400。

## 4. 接口需求

| Method | Endpoint | 必需 | 说明 |
| --- | --- | --- | --- |
| GET | `/health` | 是 | `{"status":"ok"}`，200 |
| POST | `/api/transcribe` | 是 | multipart：`file` + `language` |
| GET | `/` | 是 | 返回页面 |
| GET | `/static/*` | 是 | CSS/JS/favicon |
| GET | `/docs`、`/openapi.json` | 附带 | FastAPI 文档 |

`POST /api/transcribe` 响应：

```json
{
  "text": "识别文本",
  "language": "zh",
  "duration_seconds": 12.0,
  "processing_seconds": 3.978
}
```

口径：

- `text`：识别文本，可为空字符串
- `language`：回显请求语言 `zh`/`en`
- `duration_seconds`：解码后实际音频时长
- `processing_seconds`：服务端从路由开始到推理结束的耗时，包含解码、首次模型加载、推理，不包含模型下载
- 非法参数/文件：4xx
- 模型不可用/推理失败：5xx

错误响应：

```json
{"detail": "可读说明", "code": "machine_code"}
```

## 5. 非功能需求

| 类别 | 要求 | 实现 |
| --- | --- | --- |
| 架构 | Browser/Server | FastAPI + 原生 HTML/CSS/JS |
| Python | 3.12 | 3.12.13（本机）/3.12.10（Windows CI） |
| Web 框架 | FastAPI | 是 |
| 前端 | 原生 HTML/CSS/JS | 无框架、无构建、无 CDN |
| ASR | 开源、本地、CPU | faster-whisper small + CTranslate2 |
| 离线 | 模型准备后断网可用 | T6.9 真实 Wi-Fi 关闭 |
| 依赖 | pip + requirements.txt | 42 个固定版本 |
| 平台 | Windows 11 x64 统一复现 | Windows CI 替代；真实 Win11 未验证 |
| 浏览器 | Chrome/Edge 最新稳定版 | Chrome 156 手动；Edge 155 CI |
| 隐私 | 音频/文本不写日志 | 只记录长度/时长/语言；测试断言文本不入日志 |
| 安全 | 默认本机 | 绑定 `127.0.0.1`，无认证/多用户 |
| 性能 | CPU 可接受 | small：12 s 约 3–5 s；medium 可选：约 7–9 s |
| 可观测性 | 可定位请求 | request_id、状态码、耗时、语言、text_chars |
| 测试 | pytest 默认无模型/麦克风/外网 | 233 passed, 12 deselected |
| 交付 | 文档/证据/OpenCode | README、design、test-report、ai-development、三阶段记录 |

## 6. 假设与边界

### 6.1 假设

- 用户在本机运行，使用 `127.0.0.1`/`localhost`，浏览器安全上下文允许麦克风。
- 单用户、串行使用；不要求并发优化。
- 输入为 16 kHz 左右的人声；超过 120 秒拒绝。
- 上传上限 10 MB；录音上限 60 秒。
- 语言支持 `zh`/`en`；`auto` 为显式可选扩展，只返回 zh/en。
- 不做翻译；中文输出统一简体。
- 模型权重由用户提前下载，运行时不下载。
- 浏览器录音格式为 WebM/Opus（Chrome/Edge），后端同时支持 WAV 等。
- 首次请求允许较慢（模型加载），`processing_seconds` 包含首次加载。
- 测试样本为本人录制，参考文本已确认；原始 M4A 不提交。

### 6.2 明确边界

不做：

- 登录、权限管理、数据库、识别历史
- 说话人识别/声纹、降噪算法、翻译、TTS
- 模型训练/微调、多用户并发、分布式部署
- 手机端适配、商业级实时字幕
- 云端 ASR、Web Speech API、Docker/K8s、Node 构建、CUDA 硬依赖

### 6.3 已知差异

- Windows CI 是 Windows Server，不是 Windows 11 桌面；真实桌面/麦克风未验证。
- 桌面 Edge 未手动验证；CI 为 headless + 假麦克风。
- 无设备/占用用 DevTools 注入模拟；不是真实拔设备。
- 60 秒自动停止：页面计时 60.0 s 对应服务端 59.8 s，差 0.2 s；历史 57.18 s 未复现（T10.1）。
- 中文 small 模型有近音字错误，CER 0.18–0.23；英文 WER 0。
- 语言选择不强制输出目标脚本；错配时可能输出源语言。

## 7. 优先级与范围

| 优先级 | 内容 | 状态 |
| --- | --- | --- |
| P0 必做 | F1–F5、三接口、离线、CPU、自动化测试、6 项手动验证、文档/证据 | 完成 |
| P1 交付质量 | 真实模型、Windows CI、Edge、日志、合规、干净环境 | 完成（带披露） |
| P2 加分 | F6 实时识别、自动语言检测 | 完成并合并 |
| 不做 | 登录/DB/历史/翻译/TTS/训练/多用户/手机端/云 ASR | 明确排除 |

## 8. 验收标准

对应题目第 9 节：

| 编号 | 标准 | 当前结果 |
| --- | --- | --- |
| A1 | README 可启动 | 本机/CI 通过；Win11 实机未验证 |
| A2 | 浏览器麦克风录音/停止 | Chrome 真实麦克风通过 |
| A3 | 录音提交后端 | 200，真实模型 |
| A4 | 真实模型中英文 | 5 项真实模型 + 手动通过 |
| A5 | 结果展示 | 文本/语言/时长/耗时/复制 |
| A6 | 上传独立验证 | 中文/英文 WAV + WebM 通过 |
| A7 | 常见错误不崩溃 | 8 类异常 + 10 MB 通过 |
| A8 | 自动化 + 真实模型证据 | 217/7/5 通过 |
| A9 | 源码/文档/证据 | 仓库 + docs/opencode + test-report |

题目 6.3 六项手动验证：T6.1–T6.5 + T6.9 全部完成；T6.6 为模拟补充，不计入六项。

## 9. 关键决策

| 编号 | 决策 | 影响 |
| --- | --- | --- |
| D1 | 无 Windows 11 实机 | Windows CI 替代；真实桌面/麦克风列为未验证 |
| D2 | faster-whisper small / CPU int8 | 速度与准确率折中；中文 CER 0.18–0.23 |
| D3 | 本人录制样本 | 合法、无敏感信息；M4A 不提交 |
| D4 | Git 仓库交付 | 分阶段提交 + GitHub Actions |
| D5 | F6 确认要做但受 G5 | 未通过门禁则不做，不挤占必做 |
| D6 | GitHub | CI/协作；公开仓库 |
| D7 | Whisper 主路线 | 不触发 SenseVoice 切换 |

## 10. 未决项 / 后续

1. F6 实时识别：完成并合并；Windows CI 通过；回滚基线 `v1.0-must-have` 保留。
2. 自动语言检测：已实现；短音频/噪声误判仍需样本评估。
3. Windows 11 实机/桌面 Edge/真实麦克风：无环境，待补验。
4. 60 秒计时与音频时长差异：排查 MediaRecorder/封装/后台节流。
5. 中文准确率：评估更大模型或热词/提示，但需权衡 CPU 耗时。
6. 无设备/占用：在可拔麦克风设备上做真实验证。

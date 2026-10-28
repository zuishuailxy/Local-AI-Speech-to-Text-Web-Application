# 必做需求逐项核对（T9.2）

- 日期：2026-10-28
- 分支：`feature/f6-realtime`
- 依据：`面试考核题-v1.md`、`docs/requirements.md`、`plan.md`
- 原则：每条写明“实现位置 + 验证证据”；未验证项单列，不把计划写成通过

## F1 浏览器麦克风录音

| 需求 | 实现位置 | 验证证据 | 结果 |
| --- | --- | --- | --- |
| 点击后才请求权限 | `static/app.js` `startRecording`/`startRealtime` | `test_frontend_accessibility` 检查只在启动函数内调用；T6.1/T6.2 | 通过 |
| Start/Stop 控制 | `start-button`、`stop-button`、`startRecording`/`stopRecording` | T6.1/T6.2；E2E | 通过 |
| 状态与录音时长 | 状态机、`recording-timer`、200 ms 计时 | `t4.3-timer-state.txt`、T6.1（00:08.3） | 通过 |
| 60 秒自动停止 | `updateRecordingTimer`、`visibilitychange` | `test_frontend_recording`、T6.7（01:00.0 自动提交） | 通过（音频 57.18 s 差异已记录） |
| 停止后提交完整音频 | MediaRecorder stop → Blob → FormData | T6.1/T6.2；`t4.6-request-result.txt` | 通过 |
| 权限/设备/空 Blob 错误 | `describeMediaError`、错误面板 | T6.5（真实权限）、T6.6（DevTools 模拟设备） | 通过（无设备为模拟） |
| 成功后再次录音 | 控件 phase 恢复 | T6.1/T6.2；T6.3/T6.4 连续操作 | 通过 |
| 错误后不误提交 | `recordingFailed` 守卫 | `test_frontend_recording`；T4.4 | 通过 |

## F2 音频文件上传

| 需求 | 实现位置 | 验证证据 | 结果 |
| --- | --- | --- | --- |
| 至少 WAV | `validate_upload` 白名单、PyAV | T6.3（12 s 中文） | 通过 |
| 浏览器录音格式 | WebM/Opus | T6.8（`speech-en.webm` 8.999 s，WER 0） | 通过 |
| 共用后端识别逻辑 | 上传/录音都走 `POST /api/transcribe` → `process_audio_upload` | T5.3；T6.3/T6.4/T6.8 | 通过 |
| 不支持/损坏提示 | 415 `unsupported_format`、400 `invalid_audio` | T6.7；`error-cases.txt` | 通过 |
| 10 MB 上限 | Content-Length + 流式 | `test_audio`；T6.7 413 | 通过 |
| 120 秒上限 | 容器 duration + 解码样本数 | `test_audio`；T6.7 400 | 通过 |

格式白名单：WAV/WebM/OGG/OGA/MP3/M4A/MP4/FLAC。

## F3 本地中英文识别

| 需求 | 实现位置 | 验证证据 | 结果 |
| --- | --- | --- | --- |
| 本地开源模型 | faster-whisper small + CTranslate2 | `asr-baseline.md`、T5.2/T5.3 | 通过 |
| CPU 推理 | `device=cpu`、`int8`、4 threads | `models/` 本地加载；Windows CI | 通过 |
| 中文识别 | `language=zh` + zhconv | T6.1（CER 0.0）、T6.3（CER 0.2308） | 通过 |
| 英文识别 | `language=en` | T6.2（WER 0）、T6.4（WER 0） | 通过 |
| 不做翻译 | 默认 transcribe，不调 translate | `transcriber.py`；真实输出 | 通过 |
| 可连续识别 | 模型复用、无请求状态 | T6.1/T6.2；T6.3/T6.4 | 通过 |
| 离线 | 本地模型 | T6.9 真实关闭 Wi-Fi | 通过 |
| 禁云端 ASR | 无 OpenAI/Azure/Google SDK/调用 | `compliance-check.txt` | 通过 |
| 禁 Web Speech | 仅 getUserMedia + MediaRecorder | `compliance-check.txt` | 通过 |
| 中文简体 | `zhconv` 仅 zh | T6.1 复测；`test_text` | 通过 |

已知差异：`language` 不强制输出目标脚本；音频与选择不一致时可能输出源语言，日志有 `asr_language_mismatch`。正常匹配路径通过。

## F4 结果展示

| 需求 | 实现位置 | 验证证据 | 结果 |
| --- | --- | --- | --- |
| 当前语言 | `result-language` | T6.1/T6.2/T6.3/T6.4 | 通过 |
| 状态 | idle/requesting/recording/transcribing/success/error | T4.3/T6.1；截图 | 通过 |
| 识别文字 | `result-text` | 所有手动验证 | 通过 |
| 音频时长 | `result-duration` | T6.3 12.0 s；T6.4 9.0 s | 通过 |
| 处理耗时 | `result-processing` | T6.1 1.71 s；T6.3 3.98 s | 通过 |
| 过程反馈 | pipeline + 计时 | T6.1/T6.7 | 通过 |
| 复制文字 | Clipboard + execCommand 回退 | T6.8 剪贴板哈希一致 | 通过 |

## F5 异常处理

| 场景 | 实现 | 证据 | 结果 |
| --- | --- | --- | --- |
| 拒绝权限 | 错误面板 + 权限提示 | T6.5 真实；恢复可录音 | 通过 |
| 无麦克风 | NotFound 分支 | T6.6 DevTools 模拟 | 验证（模拟） |
| 设备占用 | NotReadable 分支 | T6.6 DevTools 模拟 | 验证（模拟） |
| 空文件/损坏 | 400 empty_file/invalid_audio | T6.7 | 通过 |
| 格式不支持 | 客户端 + 415 | T6.7 | 通过 |
| 60 秒 | 自动 stop | T6.7 01:00.0 | 通过（音频 57.18 s 差异） |
| 模型失败 | 503 model_unavailable | T6.7 临时移走模型 | 通过 |
| 后端识别失败 | 500 + 重试 | T4.8/T6.8 停后端重试 | 通过 |
| 无语音 | 空文本 + 提示 | T6.7 silent.wav | 通过 |
| >10 MB | 413 + 客户端预检 | T6.7 | 通过 |

## 接口

| 接口 | 实现 | 证据 | 结果 |
| --- | --- | --- | --- |
| `GET /health` | `app/api/routes.py` | `test_health`；T9.1 | 通过 |
| `POST /api/transcribe` | multipart file+language，四字段 | T5.3/T6.3/T6.4；T9.1 | 通过 |
| `GET /` | 静态页 | `test_health`；T9.1 200 text/html | 通过 |

`processing_seconds` 口径：路由开始到推理结束，含解码、首次模型加载、推理，不含下载；代码与文档一致。

## 环境/非功能

| 项 | 结果 |
| --- | --- |
| Python 3.12 + FastAPI | 通过（3.12.13 / 3.12.10 CI） |
| 原生 HTML/CSS/JS | 通过；无 Node/CDN |
| CPU only | 通过 |
| 无 Docker/DB/云 | 通过 |
| Windows 11 x64 | **未验证**；Windows Server CI 替代 |
| 默认测试无模型/麦克风/外网 | 通过（212/9 分支；P7 干净 203/8） |
| 真实模型 | 5 passed |
| 6 项手动 | 全部完成 |
| Windows CI | 真实模型 + Chromium + Edge 通过（F6 合并前为 3 项 Edge，合并后待跑 4 项） |

## F6 实时识别（加分）

| 项 | 状态 |
| --- | --- |
| WebSocket + PCM 后端 | 完成；8 个 WS 单测 |
| 前端 ScriptProcessor + 重采样 | 完成；E2E 4 passed |
| partial 中间文本 | 真实麦克风出现（6 partials） |
| final 完整文本 | 14.08 s / 1.742 s；CER 0.0455 |
| 必做回归 | 212 passed / 真实模型 5 / HTTP 200 |
| Windows CI F6 | 已通过（run `40665695751`，Edge E2E 4 项） |
| ScriptProcessor warning | 已知 warning，非 error；后续可迁 AudioWorklet |
| 自动语言检测 | 未实现（后置） |

## 未验证/限制（不得写成通过）

| 项 | 状态 |
| --- | --- |
| 真实 Windows 11 桌面/麦克风 | 未验证；CI 是 Windows Server |
| 桌面 Edge 手动 | 未验证；仅 headless CI |
| 真实无设备/占用 | 模拟；内置麦克风无法安全禁用 |
| 60 s 计时 vs 音频 57.18 s | 已知差异，待排查 |
| 噪声/远场/中英混合 | 未覆盖 |
| F6 Windows CI | 已通过（run `40677386222`，Edge 5 项，含 auto） |
| F6 AudioWorklet | 未迁移，仅 warning |

## 结论

F1–F5、三接口、6 项手动、离线、真实模型、Windows CI（必做）均通过；F6 已完成、真实麦克风演示、合并后 Windows CI 通过。未验证项已单列，不以 CI 或模拟替代实机结论。

# 阶段三：测试与问题修复

> 会话：`ses_e838f4101ffet1mEwSYEGuuSMK`（OpenCode Desktop，`deepseek-flash` high）
> 日期：2026-10-27 至 2026-10-28
> 说明：本文件保留关键测试、失败、定位、修复与复测记录，不是完整历史对话。
> 真实模型输出、真实浏览器上传和手动验证均单独区分，不用 Mock 结果替代。

## 1. 测试分层

| 层级 | 默认执行 | 真实模型 | 内容 |
| --- | --- | --- | --- |
| 配置/错误/API 单元 | 是 | 否 | 配置、异常处理器、语言、上传校验、接口契约 |
| 音频 | 是 | 否 | 生成 WAV、WebM fixture、解码、时长、清理、错误码 |
| Transcriber | 是 | 否 | 协议、Fake、惰性加载、并发、加载/推理失败 |
| 前端静态/契约 | 是 | 否 | 结构、MediaRecorder、计时、上传、请求、复制、可访问性 |
| 日志/可观测性 | 是 | 否 | 配置级别、request_id、请求/音频/识别元数据、错误码、文本不入日志 |
| 质量指标/样本完整性 | 是 | 否 | CER/WER 归一化、编辑距离、脚本占比、WAV 参数与参考文本一致性 |
| 中文繁转简 | 是 | 否 | zhconv 繁转简、简繁/英文不变、空文本 |
| 真实模型 pytest | 手动 | 是 | 中英文样本转写、脚本占比、CER/WER、耗时 |
| 真实上传 API | 手动 | 是 | TestClient + 真实后端/模型上传 WAV/WebM、字段与耗时 |
| 浏览器 E2E | 手动 | 否 | Playwright 页面加载、WAV 上传、假麦克风录音（FakeTranscriber） |
| 真实模型 CLI | 手动 | 是 | 两份 WAV 的中英文转写、耗时、CER/WER |
| 真实浏览器上传 | 手动 | 是 | 真实 uvicorn + 本地模型，上传样本并检查四字段 |
| Windows CI | GitHub | 否 | Python 3.12 安装、导入、pytest |
| 手动/离线 | 手动 | 是 | 麦克风、权限、Edge、断网、Windows 实机 |

## 2. 当前测试结果

```bash
.venv/bin/python -m pytest -q
```

```text
203 passed, 8 deselected
```

默认测试不加载真实模型、不下载权重、不访问麦克风。

真实模型基线：

- 中文 12s：CER 0.231，RTF 0.286
- 英文 9s：WER 0.000，RTF 0.179
- 模型加载约 0.987 s

真实模型集成测试：

- 中文 CER 0.2308，RTF 0.262
- 英文 WER 0.0000，RTF 0.181
- 模型加载 0.993 s
- 模型缺失时 2 skipped，提示 ModelScope 下载命令

真实上传 API：

- 中文 12.0 s，processing 4.441 s，CER 0.2308
- 英文 9.0 s，processing 1.686 s，WER 0.0000
- WebM/Opus 语音 8.999 s，processing 1.912 s，WER 0.0000
- 全部 real_model：5 passed

默认隔离与合规：

- 干净 `.venv-t55`（仅 41 个运行依赖）+ 移走 `models/` + 离线/代理阻塞
- `196 passed, 8 deselected in 2.73s`，未创建 `models/`，无下载日志
- 前端仅 MediaRecorder/getUserMedia，fetch 仅 `/api/transcribe`，无 CDN
- `app/` 内无云端 ASR SDK、urllib/httpx/socket；模型从本地路径加载

语言核对：

- `language` 从页面 FormData → 路由 → `model.transcribe(..., language=...)` 全程传递；
- 英文音频强制 `ja` 会输出日文，说明参数确实影响解码；
- 但英文音频强制 `zh` 仍可能输出英文，中文音频强制 `en` 仍可能输出中文；
- 新增 `output_language` 脚本占比与 `asr_language_mismatch` 警告，页面提示改为“请选择与音频一致的语言”；
- 不改变四字段响应契约；强制输出目标语言/自动检测留给 T8.1。

## 3. 真实问题与修复记录

| # | 问题 | 定位 | 修复 | 复测 |
| --- | --- | --- | --- | --- |
| 1 | 系统 Python 3.9，不满足题目 3.12 | `python3 --version` | 使用 uv 管理 CPython 3.12 创建 `.venv` | Python 3.12.13；依赖复装通过 |
| 2 | 初始音频测试 `NameError: validate_upload` | pytest 失败栈 | 补充函数导入 | 音频测试全绿 |
| 3 | pytest marker probe 未被收集 | 文件名 `_marker_probe.py` 不符合 `test_*.py` | 改为 `test_marker_probe.py`；验证默认排除与 `-m real_model` 覆盖 | 默认 47 passed；probe 1 passed |
| 4 | T2.7 生产路由加入后，T2.2 测试的临时 `/api/transcribe` 被生产路由抢先处理 | 请求收到 422 而非测试路由 200 | 测试改为使用 FakeTranscriber 的合法 multipart 请求；Content-Length 中间件仍前置 | 中间件与接口测试恢复 |
| 5 | faster-whisper 直接传路径时 `av.open(metadata_errors=...)` TypeError | T3.6 直接调用 `model.transcribe(path)` | 应用统一先用 `decode_audio` 解码为 ndarray，再交给模型；CLI 同样使用 ndarray | 真实中英文 CLI/API 成功 |
| 6 | `python scripts/verify_asr.py` 报 `No module named app` | sys.path[0] 是 scripts 目录 | 在脚本中显式插入项目根 | `--help` 子进程测试通过 |
| 7 | HuggingFace/hf-mirror 超时 | 模型下载失败 | 下载脚本增加 ModelScope 源；实际 461 MiB 25.6s 完成 | 中英文真实识别成功 |
| 8 | T4.3 首次虚拟时钟不推进 | Date.now 固定 | 改为基于 performance.now 的加速时钟 | 60 秒自动停止、timer 01:00.0 |
| 9 | MediaRecorder error 后 stop 可能覆盖为 success | 代码审查 + 假 recorder 模拟 | 增加 `recordingFailed` 守卫；error 后 stop 不再生成结果 | 错误状态保持，`lastRecording` 未生成 |
| 10 | 自动化环境无法完成麦克风授权 | 页面停在 requesting，Start disabled | 不伪造真实录音；用假 stream/recorder 验证逻辑；真实麦克风留给 T6 | 权限错误/60 秒逻辑可复现 |
| 11 | Clipboard API 可能失败 | 强制 `writeText` 抛错 | textarea + `execCommand("copy")` 回退 | 按钮“已复制”，页面无 error |
| 12 | 上传失败后需保留上下文 | T4.8 浏览器拦截 503/网络错误 | 保留语言/文件/最近提交；重试优先当前文件 | 503→200、网络失败提示均验证 |
| 13 | 多次 GitHub 443 超时 | push/fetch | 仅以成功 push / Actions run 为准；失败重试 | 所有已推送 commit 的 Windows run success |
| 14 | 语言选择未强制输出目标语言 | 同一音频强制 zh/en/ja 对照 | 记录 requested/detected/output script；不改变契约；页面提示与 mismatch 警告 | 正常中/英匹配路径通过；错配可在日志中定位 |
| 15 | 默认 Windows CI 因 e2e 模块导入 playwright 失败 | run `40633226986` 的 Run tests；模块导入早于 marker 过滤 | 将 Playwright 导入移到 e2e fixture 内延迟执行 | run `40633358118` 默认测试、Chromium 安装、浏览器 E2E 全部 success |
| 16 | 真实麦克风中文输出繁体 | T6.1 实测 `今天天氣...`；Whisper `zh` 不区分字形 | 中文结果经本地 `zhconv` 转简体 | 单测 5 项；T6.1 复测 8.16 s，简体且 CER 0.0 |
| 17 | DevTools 显示 1 个问题 | 服务端日志为 `/favicon.ico` 404 | 新增本地 `static/favicon.svg` 并在页面声明 | 静态资源测试 + E2E 0 console error |

## 4. 测试证据索引

- 配置/错误/测试隔离：`docs/evidence/t1.*`、`t3.9-mock-api-matrix.txt`、`pytest-default.txt`、`compliance-check.txt`
- 音频解码/大小/清理：`t2.1-audio-validation.txt`、`t2.2-upload-limit.txt`、`t2.3-decode.txt`、`t2.4-cleanup.txt`、`t2.5-audio-tests.txt`
- ASR 引擎：`t3.1-transcriber-protocol.txt`、`t3.2-whisper-engine.txt`
- 真实模型：`model-download.txt`、`asr-baseline.md`、`t3.7-real-api.txt`、`t5.2-real-model.txt`、`t5.3-real-api.txt`、`pytest-real-model.txt`、`model-failure.txt`
- 前端：`t4.1-frontend-structure.txt`、`t4.2-media-recorder.txt`、`t4.3-timer-state.txt`、`t4.4-error-handling.txt`、`t4.5-file-selection.txt`、`t4.6-request-result.txt`、`t4.7-copy.txt`、`t4.8-error-retry-reset.txt`
- 语言/日志：`t5.8-language-and-logging.txt`
- 真实麦克风：`t6.1-mic-zh.txt`、`t6.2-mic-en.txt`、`mic-zh.png`、`mic-en.png`
- 浏览器 E2E：`e2e.txt`、`t5.4-e2e-upload.png`、`t5.4-e2e-microphone.png`
- Windows CI：Run `40633358118`（含 Chromium 安装与 3 项浏览器 E2E）；其他 run ID 见各 evidence 文件

## 5. 真实浏览器验证摘要

- 页面加载：控制台无 error；初始 idle；Tab 顺序 language → Start → file input。
- 中文上传：`text` 正确返回，12.0s，processing 4.38s。
- 英文上传：`Never give up...`，9.0s，processing 1.70s。
- 录音自动提交：假 MediaRecorder 输出真实 WAV 字节，后端返回中文文本；track 已停止。
- 复制：Clipboard 成功；强制失败后 execCommand 回退。
- 失败重试：503 显示 detail/code，重试第二次 200；网络错误显示连接提示。
- `getUserMedia` 点击前调用 0 次，点击后 1 次。

## 6. 已知问题

- 中文 small 模型有同音/近音错误，不掩盖；CER 0.231。
- 测试样本仅覆盖单人、安静环境、正常语速；噪声、远场、混合语言未覆盖。
- 真实麦克风尚未在自动化环境完成授权；T6 手动验证。
- 真实 Windows 11 桌面/麦克风未验证；CI 是 Windows Server，需在报告中披露。
- Edge 尚未手动验证。
- 断网重启验证待 T6.9。
- Playwright E2E 默认不执行，但已在 Windows CI 单独运行；假麦克风/FakeTranscriber 不代表真实设备/模型。
- 语言选择不强制目标脚本；错配时日志有 `asr_language_mismatch`。

## 7. 如何确认 AI 生成代码满足需求

1. 每个模块先写/补单测，再运行默认 pytest。
2. 用真实模型跑样本，记录原始输出、耗时、CER/WER，不把 Mock 当真实结果。
3. 用真实浏览器上传样本，检查 Network/JSON 与页面字段。
4. 用 GitHub Actions windows-latest 复跑 Python 3.12 安装/测试。
5. 对错误路径做手动注入（503、网络失败、权限拒绝、空 Blob），确认页面可恢复。
6. 以测试报告和证据文件为准，文档中的“通过”必须有命令输出或截图支持。

## 8. P5 收尾

- 样本、测试、证据已进 Git；模型权重、M4A、`.wheelhouse-check/` 未进 Git。
- 默认：203 passed、8 deselected（T6.1 增加繁转简测试后）。
- 真实模型：5 passed（中文 CER 0.2308、英文 WER 0、WebM WER 0）。
- 浏览器 E2E：本地 3 passed，Windows CI 3 passed。
- T6.1 真实麦克风中文：8.16 s，processing 1.712 s，简体，CER 0.0，控制台无报错。
- 隔离：干净 venv + 模型移走 + 离线/代理阻塞，196 passed、8 deselected、2.73s（当时 41 个依赖；后续增加本地 `zhconv`）。
- 语言/日志：`language` 已贯通；日志不记录文本原文；错配可告警。
- 详细清单：`docs/evidence/p5-summary.txt`。


## 9. P6 手动验证（进行中）

- T6.1 中文真实麦克风：8.16 s，processing 1.712 s，简体，CER 0.0，控制台无报错。
- T6.2 英文真实麦克风：7.14 s，processing 2.592 s，WER 0.0，输出英文。
- T6.2 的 DevTools `1 个问题` 定位为 favicon 404；已补 `static/favicon.svg`，E2E 现在断言 0 console error。
- T6.3 页面上传中文 WAV：12.0 s，processing 3.978 s，CER 0.2308；近音字错误如实记录。
- T6.4 页面上传英文 WAV：9.0 s，processing 1.447 s，WER 0.0；截图误存后已重新确认。
- T6.5 权限拒绝：提示与错误状态正确；恢复权限后 3 s 静音录音提交 200。
- T6.6 无设备/占用：DevTools 注入 NotFoundError/NotReadableError，提示与失败状态正确；明确标注为模拟。
- 证据：`t6.1-mic-zh.txt`、`t6.2-mic-en.txt`、`t6.3-upload-zh.txt`、`t6.4-upload-en.txt`、`t6.5-permission-denied.txt`、`t6.6-no-mic.txt`、`mic-zh.png`、`mic-en.png`、`upload-zh.png`、`upload-en.png`、`permission-denied.png`、`device-not-found.png`、`device-in-use.png`。

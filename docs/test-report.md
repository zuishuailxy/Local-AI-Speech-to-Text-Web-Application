# 测试报告（最终版）

- 日期：2026-10-28
- 项目：Local AI Speech-to-Text Web Application
- 范围：必做 F1–F5、F6、自动语言、真实模型、离线、Windows CI、Edge、手动验证、T10 优化
- 结论：必做项、F6、6 项指定手动验证通过；T10 优化已验证；第三方 Windows clone 上传/实时通过，Win11/Edge/真实麦克风细节待确认

## 1. 测试环境

| 项 | 本机 | Windows CI |
| --- | --- | --- |
| OS | macOS arm64 / Apple M1 / 16 GB | `windows-latest`（Windows Server） |
| Python | 3.12.13 | 3.12.10 |
| 浏览器 | Chrome 156.0.8078.49 | Chromium（Playwright）/ Edge 155.0.4283.62 |
| ASR | faster-whisper small / CPU int8 / beam 5 / VAD on | 同一模型 |
| 模型 | `models/faster-whisper-small`（本地 464 MB） | CI 下载并缓存 |

## 2. 自动化测试

### 默认测试

```bash
python -m pytest -q
```

```text
233 passed, 12 deselected in 1.96s
```

12 个默认排除项：7 个 `real_model` + 5 个 `e2e`。

### Mock/接口用例分布

| 文件 | 用例数 | 覆盖 |
| --- | ---: | --- |
| `test_app_factory.py` | 5 | 应用工厂、注入、静态页 |
| `test_audio.py` | 42 | 校验、流式 10 MB、解码、时长、清理 |
| `test_config.py` | 25 | 默认值、环境变量、非法值、日志级别/文件、prompt |
| `test_download_model.py` | 10 | 模型下载/校验/回退 |
| `test_errors.py` | 10 | 错误码、异常处理 |
| `test_fixtures.py` | 8 | fixture/隔离 |
| `test_frontend_accessibility.py` | 5 | label、aria、键盘 |
| `test_frontend_recording.py` | 14 | MediaRecorder、计时、上传、请求、复制、real-time、标签 |
| `test_frontend_structure.py` | 5 | 页面结构、静态资源、favicon |
| `test_health.py` | 4 | `/health`、首页 |
| `test_language.py` | 11 | zh/en/auto/非法语言 |
| `test_logging.py` | 5 | request_id、日志字段、文本不入日志 |
| `test_logging_config.py` | 4 | 文件/JSON/轮转/默认无文件 |
| `test_metrics.py` | 10 | CER/WER/脚本占比 |
| `test_samples.py` | 5 | WAV 参数、参考文本、无模型权重 |
| `test_transcribe_api.py` | 21 | 200/4xx/5xx、空文本、重试、auto |
| `test_transcriber.py` | 7 | 协议/Fake |
| `test_transcriber_unit.py` | 19 | 惰性加载、锁、推理、日志、繁转简、auto/低置信度、prompt 门控 |
| `test_text.py` | 5 | zhconv 繁转简、英文/空文本不变 |
| `test_verify_asr.py` | 6 | CLI 冒烟 |
| `test_ws.py` | 12 | WebSocket/PCM/partial/final/错误/auto |
| **合计** | **233** | 默认执行 |

真实模型 7 项、E2E 5 项默认排除，分别需要模型/浏览器。

当前全量为 233 passed、12 deselected；P7 必做版干净复验（`/tmp/stt-venv-final`，42 个依赖，模型移走，离线/代理阻塞）为 203 passed、8 deselected：

```text
203 passed, 8 deselected in 2.53s
```

### 真实模型

```bash
python -m pytest -q -m real_model -s
```

```text
7 passed, 238 deselected
```

| 测试 | 时长 | 处理/推理 | 质量 |
| --- | --- | --- | --- |
| 中文 WAV API | 12.0 s | 7.073 s（含首次加载） | CER 0.2308 |
| 英文 WAV API | 9.0 s | 1.723 s | WER 0.0000 |
| 英文 WebM API | 8.999 s | 1.785 s | WER 0.0000 |
| 中文直接推理 | 12.0 s | 4.025 s，RTF 0.3354 | CER 0.2308 |
| 英文直接推理 | 9.0 s | 1.818 s，RTF 0.2020 | WER 0.0000 |

### 浏览器 E2E

```bash
PLAYWRIGHT_CHANNEL=chrome python -m pytest -q -m e2e
```

```text
5 passed
```

覆盖页面加载、WAV 上传 + 复制、自动语言上传、假麦克风 WebM 录音、实时 WebSocket。Windows CI 另用 Chromium 与 Edge 155 跑通同一套 5 项。

### 命令输出归档

| 内容 | 证据文件 |
| --- | --- |
| 默认/干净隔离 | `docs/evidence/pytest-default.txt` |
| 真实模型 | `docs/evidence/pytest-real-model.txt` |
| 浏览器 E2E | `docs/evidence/e2e.txt` |
| Windows CI | `docs/evidence/windows-ci.txt` |
| 手动 6 项 | `docs/evidence/t6.1-*.txt` … `t6.9-*`、对应 PNG |
| 异常/边界 | `docs/evidence/error-cases.txt`、`auto-stop-60s.png`、`upload-webm.txt` |
| Edge | `docs/evidence/edge.txt` |

本机终端日志（如 `/tmp/t6.*-uvicorn.log`）仅作现场排查，不提交；上表为可复核的归档证据。

## 3. 六项指定手动验证

题目 6.3 要求至少实际验证一次：

| # | 场景 | 结果 | 关键数据 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | 浏览器麦克风中文 | 通过 | 8.16 s；processing 1.712 s；简体；CER 0.0 | `mic-zh.png`、`t6.1-mic-zh.txt` |
| 2 | 浏览器麦克风英文 | 通过 | 7.14 s；processing 2.592 s；WER 0.0 | `mic-en.png`、`t6.2-mic-en.txt` |
| 3 | 上传中文 WAV | 通过 | 12.0 s；processing 3.978 s；CER 0.2308 | `upload-zh.png`、`t6.3-upload-zh.txt` |
| 4 | 上传英文 WAV | 通过 | 9.0 s；processing 1.447 s；WER 0.0 | `upload-en.png`、`t6.4-upload-en.txt` |
| 5 | 麦克风权限被拒绝 | 通过 | Error 状态；明确提示；恢复后可录音 | `permission-denied.png`、`t6.5-permission-denied.txt` |
| 6 | 断网识别 | 通过 | 真实关闭 Wi-Fi；中文 4.357 s / CER 0.1795；英文 1.359 s / WER 0 | `offline-zh.png`、`offline-en.png`、`offline.txt` |

六项均已完成；第 6 项在 `HF_HUB_OFFLINE=1`、真实 Wi-Fi 关闭条件下完成。

## 4. 补充手动/边界验证

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 无设备/设备占用（DevTools 模拟） | NotFound/NotReadable 提示正确；明确标注模拟 | `t6.6-no-mic.txt`、`device-*.png` |
| 异常上传、静音、超时长、503 | 6 个分支提示/状态码正确 | `error-cases.txt` |
| 60 秒自动停止 | 计时 01:00.0，自动提交；服务端音频 57.18 s（T10.1 复测改为 59.8 s，差 0.2 s） | `auto-stop-60s.png`、`t10.1-60s-alignment.txt` |
| 复制、停后端重试、WebM 上传 | 通过；剪贴板哈希一致；重试复用同一文件 | `upload-webm.txt`、`upload-webm.png` |
| Windows CI | 真实模型 5 项、Chromium/Edge E2E 通过 | `windows-ci.txt` |
| Edge | Windows CI headless Edge 155，5 passed（含复制/F6/auto） | `edge.txt` |

## 5. Windows CI

| Run | 内容 | 结果 |
| --- | --- | --- |
| `40651179705` | 首次真实模型下载 + 测试 + Edge | success |
| `40651812439` | 缓存命中；Python/Edge 版本与模型耗时 | success |
| `40658826426` | Edge 复制断言补充后复跑 | success |
| `40680120089` | T10 计时标签 + 截图 | success |
| `40682285556` | T10.4 prompt opt-in | success |
| `40684188857` | prompt 不进入实时 partial | success |
| `40687099376` | T10.7 medium 可选模式 | success |
| `40690657742` | T10.8 首字延迟 | success |
| `40697700916` | 空 partial 快速重试 | success |

Windows 真实模型耗时：

```text
中文 12.000 s / processing 5.503 s / inference 4.182 s / load 1.295 s
英文 9.000 s / processing 4.354 s / inference 3.049 s / load 1.289 s
```

CI 环境是 Windows Server，不是 Windows 11 桌面；浏览器 E2E 使用 headless + 假麦克风 + FakeTranscriber。

## 6. F6 实时识别

**已完成并合并到 `main`；Windows CI 通过。**

- WebSocket `/ws/transcribe?language=zh|en`，PCM16LE 16 kHz 分片。
- 首个 partial 约 1.2 s 触发，之后每约 1.5 s；最近 3 s 窗口，partial 用 beam 1；stop 后 final 全量、beam 5。
- 样本 WebSocket：首个非空文本 2.22–2.27 s；真实麦克风 12.8 s：2.343 s；6.4 s：2.984 s（首窗口为空后重试）。
- 前端“实时识别（实验）”复选框，AudioWorklet 主路径 + 重采样 + PCM16；旧浏览器回退 ScriptProcessor。
- Mock WS：9 passed；E2E：5 passed（Chrome 本地；Windows CI run `40697700916` Edge 5 项通过）。
- T8.1 自动语言：HTTP/WS/页面支持 `auto`；中英文真实样本自动检测通过；用户手动中文/英文/实时 auto 截图；原有 zh/en 契约不变。
- 日志：成功事件带 `outcome=success`，失败事件带 `outcome=error`；支持 `LOG_FILE`/JSON/轮转；不记录音频/文本原文。
- 真实麦克风中文：14.08 s、6 partials、final 1.742 s、CER 0.0455；迁移 AudioWorklet 后实时 E2E 无 ScriptProcessor deprecation warning。
- 回滚基线 `v1.0-must-have` 保留；F6 分支已合并，合并后 Windows CI run `40697700916` 成功。
- 自动语言检测（`language=auto`）已实现：HTTP/WS/页面；中英文真实样本检测通过。

### T10 优化结果

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 60 s 计时 | 60.0 s → 59.8 s，差 0.2 s；旧 57.18 s 未复现 | `t10.1-60s-alignment.txt` |
| auto 鲁棒性 | 低置信度按输出脚本回退，记录 warning | `t10.2-auto-robustness.txt` |
| 实时首字 | 样本 2.22–2.27 s；真实麦克风 2.343 s；首窗为空时 2.984 s | `t10.8-realtime-first-text.txt` |
| 中文准确率 | medium CER 0.0769，默认仍 small | `t10.7-medium-model.txt` |
| 日志 | `LOG_FILE`、text/json、轮转；不记录原文 | `t10.5-logging.txt` |
| prompt | 默认关闭；仅 zh 且 ≥3 s，partial 不传 | `t10.4-prompt-default-analysis.md` |

### medium 模型评估（T10.7）

默认仍是 small；medium 作为批量可选模式，通过 `ASR_MODEL_SIZE=medium` 启用。

| 模型 | 中文 CER | 12 s 推理 | 9 s 英文 | 峰值内存 | 3 s 实时窗口 |
| --- | ---: | ---: | ---: | ---: | ---: |
| small | 0.2308 | 3.4–3.8 s | 2.2–2.7 s | 941 MB | 1.6 s |
| medium | **0.0769** | 7.3–8.9 s | 4.6–4.9 s | 1877 MB | 3.9 s |

- medium 修正“招手/作别”，仍有“金柳→金牛、夕阳→西洋”。
- 3 s 窗口超过实时预算，F6 不建议使用 medium。
- 领域 prompt 在 medium 上 CER 反而升到 0.1538，默认关闭。
- 复现：`scripts/benchmark_models.py`。

## 7. 已知问题与风险

| 级别 | 问题 | 说明 |
| --- | --- | --- |
| ~~中~~ 已关闭 | 60 秒计时与实际音频不一致 | T10.1 复测 5.3/5.2、10.2/10.1、60.0/59.8，最大差 0.2 s；历史 57.18 s 未复现 |
| 中 | 中文近音字错误 | small 模型把招手/金柳/夕阳识别为近音词；CER 0.18–0.23，未超过阈值 |
| 低 | Windows 实机细节待确认 | 第三方 Windows clone 上传 + 实时通过；Win11/浏览器/真实麦克风未记录，不写成全部通过 |
| 低 | 桌面 Edge 未手动验证 | 仅有 Windows CI headless Edge + 假麦克风 |
| 低 | 语言选择不强制目标脚本 | 音频与所选语言不一致时可能输出源语言；日志有 `asr_language_mismatch` |
| 低 | 无设备验证为模拟 | macOS 内置麦克风无法安全禁用；真实 NotFound/NotReadable 待其他设备 |
| 低 | 样本覆盖有限 | 单人、安静、正常语速；噪声/远场/混合语言未覆盖 |
| 低 | 首窗为空时首字约 3.0 s | 12.8 s 录音首字 2.343 s；6.4 s 首窗为空时 2.984 s |
| 低 | AudioWorklet 兼容 fallback | 主路径 AudioWorklet；旧浏览器回退 ScriptProcessor，可能有 deprecation warning |

## 8. G4 检查

| 门禁项 | 结果 |
| --- | --- |
| 6 项指定手动验证 | 通过 |
| 离线识别 | 通过（真实 Wi-Fi 关闭） |
| Windows CI 兼容性 | 通过（Windows Server） |
| 真实模型测试 | 通过（本机 + Windows CI） |
| 测试报告基线 | 本文件 |
| 所有必做项 | F1–F5 通过 |
| F6 实时识别 | 已完成并合并；Windows CI 通过 |
| Windows 实机 | 第三方 clone 上传/实时通过；细节待确认 |

**G4：通过（带已披露限制）**。不把 Windows CI 写成 Windows 11 实机通过；第三方 Windows clone 测试已通过上传 + 实时，但 Windows 版本/浏览器/真实麦克风细节待确认。

### 未执行/未验证项

| 项 | 状态 | 原因 |
| --- | --- | --- |
| 真实 Windows 11 桌面/麦克风 | 部分验证 | 第三方 Windows clone 上传/实时通过；版本/浏览器/麦克风待确认 |
| 桌面 Edge 手动操作 | 未验证 | 本机无 Edge；仅 CI headless Edge |
| 真实无设备/设备占用 | 未验证 | 内置麦克风无法安全禁用；T6.6 为 DevTools 模拟 |
| 噪声/远场/中英混合 | 未覆盖 | 样本为单人安静环境 |
| 60 s 计时与音频时长一致 | 已关闭 | 60.0 s vs 59.8 s（差 0.2 s）；历史 57.18 s 未复现 |

## 9. 证据索引

- 测试隔离/合规：`pytest-default.txt`、`compliance-check.txt`
- 真实模型：`asr-baseline.md`、`t5.2-real-model.txt`、`t5.3-real-api.txt`、`pytest-real-model.txt`
- 手动：`t6.1-mic-zh.txt` … `t6.11` 对应文件；第三方 Windows：`t6.13-windows-third-party.txt`
- 错误/边界：`error-cases.txt`、`auto-stop-60s.png`、`upload-webm.txt`
- CI：`windows-ci.txt`、`edge.txt`
- 准确率：`t10.7-medium-model.txt`、`t10.7-medium-benchmark.json`
- 实时：`t10.8-realtime-first-text.txt`
- 优化：`t10.1-60s-alignment.txt`、`t10.2-auto-robustness.txt`、`t10.3-realtime-latency.txt`、`t10.4-prompt-default-analysis.md`、`t10.5-logging.txt`、`t10.6-regression.txt`
- 问题记录：`docs/issue-log.md`
- 需求逐项核对：`docs/evidence/requirements-checklist.md`
- 样本/参考：`samples/reference.txt`、`sample-audio-check.txt`

# 测试报告（P6 初稿）

- 日期：2026-10-28
- 项目：Local AI Speech-to-Text Web Application
- 范围：必做功能 F1–F5、真实模型、离线、Windows CI、Edge、手动验证
- 结论：必做项与 6 项指定手动验证通过；Windows 11 实机/真实桌面 Edge 未验证，已单独披露

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
203 passed, 8 deselected in 1.59s
```

8 个默认排除项：5 个 `real_model` + 3 个 `e2e`。

干净环境复验（`/tmp/stt-venv-final`，42 个依赖，模型移走，离线/代理阻塞）：

```text
203 passed, 8 deselected in 2.53s
```

### 真实模型

```bash
python -m pytest -q -m real_model -s
```

```text
5 passed, 199 deselected
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
3 passed
```

覆盖页面加载、WAV 上传 + 复制、假麦克风 WebM 录音。Windows CI 另用 Chromium 与 Edge 155 跑通同一套 3 项。

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
| 60 秒自动停止 | 计时 01:00.0，自动提交；服务端音频 57.18 s | `auto-stop-60s.png` |
| 复制、停后端重试、WebM 上传 | 通过；剪贴板哈希一致；重试复用同一文件 | `upload-webm.txt`、`upload-webm.png` |
| Windows CI | 真实模型 5 项、Chromium/Edge E2E 通过 | `windows-ci.txt` |
| Edge | Windows CI headless Edge 155，3 passed（含复制） | `edge.txt` |

## 5. Windows CI

| Run | 内容 | 结果 |
| --- | --- | --- |
| `40651179705` | 首次真实模型下载 + 测试 + Edge | success |
| `40651812439` | 缓存命中；Python/Edge 版本与模型耗时 | success |
| `40658826426` | Edge 复制断言补充后复跑 | success |

Windows 真实模型耗时：

```text
中文 12.000 s / processing 5.503 s / inference 4.182 s / load 1.295 s
英文 9.000 s / processing 4.354 s / inference 3.049 s / load 1.289 s
```

CI 环境是 Windows Server，不是 Windows 11 桌面；浏览器 E2E 使用 headless + 假麦克风 + FakeTranscriber。

## 6. 已知问题与风险

| 级别 | 问题 | 说明 |
| --- | --- | --- |
| 中 | 60 秒计时与实际音频不一致 | 页面 60.0 s，服务端 57.18 s，差约 2.8 s；未超过上限，原因可能为 MediaRecorder/硬件启动/后台节流 |
| 中 | 中文近音字错误 | small 模型把招手/金柳/夕阳识别为近音词；CER 0.18–0.23，未超过阈值 |
| 中 | Windows 11 实机/真实麦克风未验证 | 仅有 Windows Server CI；不得写成 Windows 11 实机通过 |
| 低 | 桌面 Edge 未手动验证 | 仅有 Windows CI headless Edge + 假麦克风 |
| 低 | 语言选择不强制目标脚本 | 音频与所选语言不一致时可能输出源语言；日志有 `asr_language_mismatch` |
| 低 | 无设备验证为模拟 | macOS 内置麦克风无法安全禁用；真实 NotFound/NotReadable 待其他设备 |
| 低 | 样本覆盖有限 | 单人、安静、正常语速；噪声/远场/混合语言未覆盖 |

## 7. G4 检查

| 门禁项 | 结果 |
| --- | --- |
| 6 项指定手动验证 | 通过 |
| 离线识别 | 通过（真实 Wi-Fi 关闭） |
| Windows CI 兼容性 | 通过（Windows Server） |
| 真实模型测试 | 通过（本机 + Windows CI） |
| 测试报告基线 | 本文件 |
| 所有必做项 | F1–F5 通过 |
| Windows 11 实机/麦克风 | 未验证，已披露 |

**G4：通过（带已披露限制）**。不把 Windows CI 写成 Windows 11 实机通过；F6 仍需 G5 门禁与文档基线。

## 8. 证据索引

- 测试隔离/合规：`pytest-default.txt`、`compliance-check.txt`
- 真实模型：`asr-baseline.md`、`t5.2-real-model.txt`、`t5.3-real-api.txt`、`pytest-real-model.txt`
- 手动：`t6.1-mic-zh.txt` … `t6.11` 对应文件
- 错误/边界：`error-cases.txt`、`auto-stop-60s.png`、`upload-webm.txt`
- CI：`windows-ci.txt`、`edge.txt`
- 样本/参考：`samples/reference.txt`、`sample-audio-check.txt`

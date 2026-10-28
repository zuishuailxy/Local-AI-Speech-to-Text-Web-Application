# 问题修复记录（Issue Log）

- 日期：2026-10-28
- 范围：开发、测试、CI、手动验证中发现的问题
- 关联：`docs/opencode/03-testing-and-fixes.md`、`docs/test-report.md`、`docs/evidence/`

## 1. 已修复问题

| ID | 级别 | 现象 | 复现/定位 | 修复 | 验证 | 提交/证据 |
| --- | --- | --- | --- | --- | --- | --- |
| I-01 | 高 | 系统 Python 3.9，不满足题目 3.12 | `python3 --version` | 用 uv 安装 CPython 3.12 并创建 `.venv` | 3.12.13；依赖安装/pytest 通过 | `1cb1c4c` |
| I-02 | 中 | 音频测试 `NameError: validate_upload` | pytest 失败栈 | 补充测试导入 | 音频测试全绿 | `98ca88e` |
| I-03 | 低 | pytest marker probe 未被收集 | 文件名不符合 `test_*.py` | 改为 `test_marker_probe.py`；验证默认排除与 `-m` 覆盖 | 默认/probe 均符合预期 | `fc8e7f9` |
| I-04 | 中 | T2.7 生产路由加入后，测试临时路由被抢先处理 | 请求返回 422 而非测试路由 200 | 测试改用 FakeTranscriber 的合法 multipart；中间件仍前置 | 中间件/API 测试恢复 | `8722b7e` |
| I-05 | 高 | faster-whisper 直接传路径触发 `av.open(metadata_errors=...)` TypeError | T3.6 直接 `model.transcribe(path)` | 统一先用 `decode_audio` 解码 ndarray，再交给模型；CLI 同样 | 真实中英文 CLI/API 成功 | `02829b9`、`9038ef3` |
| I-06 | 中 | `python scripts/verify_asr.py` 报 `No module named app` | `sys.path[0]` 是 scripts 目录 | 脚本显式插入项目根 | `--help` 子进程测试通过 | `7c15d98` |
| I-07 | 高 | HuggingFace/hf-mirror 超时，模型下载失败 | 下载脚本超时 | 增加 ModelScope 源；实际 461 MiB 完成 | 中英文真实识别成功 | `b1827d2`、`97a59c3` |
| I-08 | 中 | T4.3 虚拟时钟不推进 | `Date.now` 固定 | 改为基于 `performance.now` 的加速时钟 | 60 秒自动 stop、timer 01:00.0 | `6565c68` |
| I-09 | 中 | MediaRecorder error 后 stop 可能覆盖为 success | 代码审查 + 假 recorder 模拟 | 增加 `recordingFailed` 守卫 | 错误状态保持，未生成结果 | `4365d89` |
| I-10 | 中 | 自动化环境无法完成真实麦克风授权 | 页面停在 requesting | 不伪造真实录音；假 stream 验证逻辑；真实麦克风留 T6 | 权限错误/60 秒逻辑可复现 | T6.1/T6.2 补验 |
| I-11 | 低 | Clipboard API 可能被拒绝 | 强制 `writeText` 抛错 | textarea + `execCommand("copy")` 回退 | 按钮“已复制”，无 error | `a365144` |
| I-12 | 中 | 上传失败后丢失语言/文件上下文 | T4.8 拦截 503/网络错误 | 保留语言/文件/最近提交；重试优先当前文件 | 503→200、网络失败提示 | `b542b9c` |
| I-13 | 中 | 中文真实输出繁体 | T6.1 `今天天氣...` | 本地 `zhconv` 繁转简；只对 zh | 单测 5 项；T6.1 复测简体 | `2eb140d` |
| I-14 | 低 | DevTools 显示 1 个问题 | 服务端 `/favicon.ico` 404 | 新增 `static/favicon.svg` 并声明 | 静态资源测试 + E2E 0 console error | `61c4595` |
| I-15 | 高 | Windows 真实模型下载步骤 exit 1 | annotation: cp1252 `UnicodeEncodeError` | `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`；HF/hf-mirror 回退 | Run `40651179705`/`40651812439` success | `bc82522` |
| I-16 | 高 | 默认 Windows CI 收集 e2e 时缺 Playwright | `ModuleNotFoundError` | Playwright 导入移到 fixture 内延迟执行 | Run `40633358118` 通过 | `7e1d302` |
| I-17 | 低 | T6.4 首次截图误存中文结果 | 截图内容与文件名不符 | 重新截当前英文结果并核对 | 语言/文件/时长正确 | `b338e9d` |
| I-18 | 中 | auto 低置信度可能静默误判 | T10.2 构造低概率用例 | 概率 <0.55 时按输出脚本回退并记录 warning | 单测 + 真实中英文仍正确 | `b83f98b` |
| I-19 | 中 | opt-in prompt 可能进入 3 s 实时 partial | T10.4 代码审查 | WebSocket partial 显式 `use_prompt=False` | 单测断言 prompt 不传 | `770da2d` |
| I-20 | 中 | 真实麦克风首字 3.59 s | `first_text_seconds` 日志 | 首个 partial 1.2 s、空结果 0.5 s 重试、partial beam 1 | 12.8 s 录音首字 2.343 s | `a99da8c`、`569cb99` |

## 2. 重点案例

### 2.1 PyAV 与 faster-whisper 路径不兼容（I-05）

- 现象：真实模型 CLI 直接 `model.transcribe("samples/chinese.wav")`，内部调用 `av.open(..., metadata_errors="ignore")`，PyAV 19 不接受该参数，抛 `TypeError`。
- 定位：T3.6 真实基线调用栈。
- 修复：应用/CLI 都先用自己的 `decode_audio` 解码为 16 kHz mono float32 ndarray，再调用 `model.transcribe(samples, ...)`。
- 验证：真实中文/英文 CLI 与 API 均成功；WebM 解码测试独立通过。
- 关联提交：`02829b9`、`9038ef3`。

### 2.2 Windows cp1252 打印中文导致 CI 失败（I-15）

- 现象：Windows real-model job 在 Download real model 步骤 exit 1；annotation 最后错误为 `UnicodeEncodeError: 'charmap' codec ...`。
- 定位：GitHub Actions annotation；下载脚本成功/失败后打印中文提示，PowerShell 默认 cp1252 无法编码。
- 修复：
  - job 级 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`
  - ModelScope 失败时回退 HuggingFace / hf-mirror
  - 失败用 `::error::` 输出最后一条错误
- 验证：`windows-latest` 真实模型、Chromium、Edge 全部通过。
- 关联提交：`e919277`、`bc82522`。

### 2.3 默认 CI 收集 e2e 缺 Playwright（I-16）

- 现象：默认 `Run tests` 失败 `No module named 'playwright'`，即使用例会被 `-m "not e2e"` 排除。
- 原因：pytest 收集模块时先执行模块级导入。
- 修复：Playwright 导入移到 `browser` fixture 内延迟执行；默认套件无需安装 Playwright。
- 验证：默认 CI 203 passed；e2e job 安装后 3 passed。
- 关联提交：`7e1d302`。

### 2.4 真实麦克风中文输出繁体（I-13）

- 现象：T6.1 首次真实录音输出 `今天天氣很好...`。
- 定位：Whisper `language=zh` 只约束语言，不区分简繁。
- 修复：中文结果经本地 `zhconv` 转简体；英文不变。
- 验证：复测 8.16 s，输出简体且 CER 0.0；单测 5 项。
- 关联提交：`2eb140d`。

## 3. 未关闭问题

> 更新：2026-10-28（T10 优化后）。O-01 已关闭；其余仍开放。

| ID | 级别 | 问题 | 状态/处理 |
| --- | --- | --- | --- |
| O-01 | 中 | 60 s 计时 60.0 s，服务端音频 57.18 s | **已关闭（2026-10-28）**：复测 5.3/5.2、10.2/10.1、60.0/59.8，最大差 0.2 s；历史 57.18 s 未复现，见 `t10.1-60s-alignment.txt` |
| O-02 | 中 | 中文 small 近音字错误 | 模型能力限制；CER 0.2308，未超过阈值；medium 可选 0.0769；不修改参考文本 |
| O-03 | 中 | Windows 11 实机/真实麦克风未验证 | 无环境；Windows Server CI 替代，报告中披露 |
| O-04 | 低 | 桌面 Edge 未手动验证 | 仅 Windows CI headless Edge；待桌面 Edge 环境 |
| O-05 | 低 | 无设备/占用为 DevTools 模拟 | 内置麦克风无法安全禁用；待可拔设备补验 |
| O-06 | 低 | 语言选择不强制目标脚本 | 错配时可能输出源语言；日志有 `asr_language_mismatch` |
| O-07 | 低 | 样本覆盖有限 | 单人/安静/正常语速；噪声/远场/混合语言未覆盖 |
| O-08 | 加分 | F6 实时识别 | 已完成、真实麦克风演示并合并；Windows CI run `40694704464` 通过 |

## 4. 处理原则

1. 不以 Mock 结果替代真实模型/真实浏览器结果。
2. 测试失败先定位，不以重跑掩盖；CI 失败查看 annotation/日志。
3. 无法现场复现的环境限制明确写“模拟/未验证”，不写成通过。
4. 每个修复尽量有单测/复测和提交记录。
5. 用户可见错误必须可读，内部错误记录日志但不泄露音频/文本原文。

## 5. F6 门禁（T8.0）

- 日期：2026-10-28 17:04 CST
- G4、默认 203、真实模型 5、Windows CI、离线、文档基线均通过。
- 用户确认剩余 ≥3.5 小时；3 小时时间盒：17:04–20:04。
- 回滚基线：tag `v1.0-must-have`（`4db4ed6`）。
- 决策：进入 F6；失败则回滚并记录原因，不影响必做版。
- 详见 `docs/evidence/f6-gate.txt`。

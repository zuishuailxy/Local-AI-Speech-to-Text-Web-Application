# AI 开发过程说明（AI Development）

- 日期：2026-10-28
- 工具：OpenCode Desktop（模型 `deepseek-flash` high）
- 会话：`ses_e838f4101ffet1mEwSYEGuuSMK`
- 交付基线：必做 F1–F5 + F6 + auto + 离线 + Windows CI + Edge + 文档 + T10 优化
- 三阶段证据：`docs/opencode/`

## 1. OpenCode 承担了哪些任务

| 阶段 | OpenCode 的任务 | 产物 |
| --- | --- | --- |
| 需求/设计 | 阅读题目、拆解 F1–F6、对比 ASR 方案、制定任务清单与门禁 | `plan.md`、`todo.md`、`docs/opencode/01-*` |
| 后端 | FastAPI 应用工厂、`/health`、`/api/transcribe`、错误模型、配置 | `app/` |
| 音频 | 上传校验、10 MB 流式限制、PyAV 解码、120 s 限制、临时文件清理 | `app/services/audio.py` |
| 模型 | faster-whisper 适配器、惰性加载、锁、模型下载脚本、CLI 冒烟 | `app/services/transcriber.py`、`scripts/` |
| 前端 | 页面结构、MediaRecorder、计时/状态机、上传、结果、复制、错误/重试 | `static/` |
| 测试 | 单测、Mock API、真实模型、Playwright E2E、隔离/合规检查 | `tests/` |
| CI | Windows 安装/测试、真实模型下载、Chromium/Edge E2E | `.github/workflows/windows.yml` |
| 文档 | README、requirements、design、test-report、OpenCode 三阶段记录 | `docs/` |

AI 负责生成代码、测试和文档草稿；最终取舍、验收和是否交付由人工决定。

## 2. 哪些重要技术决策由自己做出

| 编号 | 决策 | 原因 |
| --- | --- | --- |
| D1 | 没有 Windows 11 实机，使用 GitHub Actions `windows-latest` 做替代验证 | 不伪造实机结果；CI 是 Windows Server，明确披露 |
| D2 | faster-whisper **Whisper small**，CPU int8，beam 5，VAD on | CPU 可运行、中英双语、安装简单；medium/large 成本过高 |
| D3 | 测试音频使用本人录制，M4A 不提交，只提交派生 WAV/reference | 合法授权、无敏感信息；避免第三方素材 |
| D4 | 交付 Git 仓库，分阶段提交 | 可追溯、可回滚、便于 CI |
| D5 | F6 实时识别确认要做，但严格放在 G4/G5 门禁之后 | 不让加分项挤占必做、离线、Windows、文档 |
| D6 | GitHub 托管 + Actions | 可远程复现；公开仓库便于检查 |
| D7 | 模型路线 A：Whisper 主，SenseVoice 仅条件评估 | small 达到 G2 阈值，不引入第二套模型 |

其他人工决策：

- 60 秒录音上限、120 秒解码上限、10 MB 上传上限
- 错误码与状态码（400/413/415/422/500/503）
- 中文繁转简使用本地 `zhconv`；不做翻译
- 语言错配不改变四字段契约，只记录日志
- 测试样本不伪造；真实麦克风、Windows 11、桌面 Edge 未验证就明确写未验证

## 3. 遇到过什么问题，如何借助 AI 解决

| # | 问题 | 定位 | 修复/验证 |
| --- | --- | --- | --- |
| 1 | 系统 Python 3.9，不满足题目 | `python3 --version` | 用 uv 安装 CPython 3.12；`.venv` 固定依赖 |
| 2 | HuggingFace/hf-mirror 不可达 | 下载脚本超时 | 增加 ModelScope 下载；实际 461 MiB 完成 |
| 3 | faster-whisper 直接传路径触发 PyAV `metadata_errors` TypeError | T3.6 调用栈 | 先用 `decode_audio` 解码为 ndarray，再传给模型；CLI 同样处理 |
| 4 | 前端自动化环境无法授权麦克风 | 页面停在 requesting | 不伪造真实录音；用假 MediaRecorder 验证逻辑，真实麦克风留 T6 |
| 5 | pytest marker probe 未被收集 | 文件名不符合 `test_*.py` | 改名并验证默认排除/-m 覆盖 |
| 6 | T2.7 生产路由与测试临时路由冲突 | 请求返回 422 | 测试改用 FakeTranscriber 的合法 multipart；中间件仍前置 |
| 7 | Windows CI 真实模型下载 exit 1 | Annotation: cp1252 `UnicodeEncodeError` | 设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`；加 HF/hf-mirror 回退 |
| 8 | 默认 CI 收集 e2e 时缺 Playwright | `ModuleNotFoundError` | Playwright 导入移到 fixture 内延迟执行；默认套件无需安装 |
| 9 | 真实麦克风中文输出繁体 | T6.1 `今天天氣...` | 本地 `zhconv` 繁转简；单测 + 复测简体 |
| 10 | 60 秒计时 60.0 s，服务端音频曾 57.18 s | T6.7 日志 | T10.1 复测 5.3/5.2、10.2/10.1、60.0/59.8，最大差 0.2 s；旧值未复现，已关闭 |
| 11 | T6.4 截图误存成中文结果 | 截图内容检查 | 要求重截，核对文件名/语言/时长后才记录 |
| 12 | GitHub push 偶发 443/空响应 | push/fetch | 重试并以成功 push/Actions run 为准 |

完整记录见 `docs/opencode/03-testing-and-fixes.md`、`docs/evidence/`。

## 4. 如何确认 AI 生成的代码满足业务需求

不是只看“测试通过”，而是多层验证：

1. **每个模块先写/补单测**：音频、API、语言、错误、前端契约、日志、繁转简；默认 233 passed（T10 后；P7 必做版 203）。
2. **真实模型验证**：`pytest -m real_model` 7 项，记录原始文本、CER/WER、耗时；不把 FakeTranscriber 当真实结果。
3. **真实浏览器手动验证**：Chrome 156 真实麦克风中文/英文、上传 WAV、权限拒绝、离线；保存截图和页面文本。
4. **异常路径**：空文件、损坏、格式、10 MB、静音、120 s、503、断网、重试、60 s；记录状态码/提示。
5. **隔离/合规**：干净 venv + 移走 `models/` + 离线/代理阻塞；静态搜索确认无 Web Speech/云 ASR/CDN。
6. **Windows CI**：Python 3.12.10、真实模型、Chromium/Edge E2E；与真实 Windows 11 分开写。
7. **人工审查**：AI 生成的截图/文本/命令输出必须与代码/日志一致；发现不一致时以实际结果为准。
8. **证据可追溯**：每个“通过”对应 `docs/evidence/` 文件或 Git/Actions run；未执行项明确标注。

实际例子：

- T6.1 发现繁体输出，没有直接写“通过”，而是加繁转简、补测试、重新录音复测。
- T6.4 发现截图是中文结果，要求重截后才完成。
- Windows CI 首次下载失败，通过 annotation 定位编码问题，而不是猜“网络问题”。
- 60 s 计时与 57.18 s 音频差异没有掩盖，写入测试报告和已知问题。

## 5. 后续优化优先级（T10 后）

1. **真实 Windows 11/桌面 Edge/真实麦克风**：唯一未完成的环境项。
2. **中文准确率**：medium 已作为批量可选（CER 0.0769）；进一步可做领域数据微调。
3. **实时体验**：首字 2.2–2.3 s；可继续做重叠窗口/增量拼接，改善中间文本稳定性。
4. **样本覆盖**：噪声、远场、混合语言、数字/专有名词。
5. **AudioWorklet 回退**：在旧浏览器实机验证 ScriptProcessor 回退。
6. **工程化**：请求级超时、指标、容器化不在必做范围，按需评估。

## 6. 三阶段证据索引

| 阶段 | 文件 | 内容 |
| --- | --- | --- |
| 一：需求理解与技术设计 | `docs/opencode/01-requirements-and-design.md` | 题目拆解、ASR 选型、D1–D7、计划 |
| 二：功能开发与集成 | `docs/opencode/02-implementation.md` | 脚手架、音频、接口、模型、前端、测试矩阵、Windows CI |
| 三：测试与问题修复 | `docs/opencode/03-testing-and-fixes.md` | 测试分层、真实失败/修复、手动/离线/Windows/Edge、已知问题 |

补充：

- 测试报告：`docs/test-report.md`
- 需求/设计：`docs/requirements.md`、`docs/design.md`
- 证据目录：`docs/evidence/`
- Git 提交与 Actions run：见各证据文件

## 7. 诚实声明

- OpenCode 生成了大量代码/测试/文档草稿，但最终代码经过人工运行、审查和修正。
- 没有 Windows 11 实机，因此不能声称 Windows 11 桌面/真实麦克风通过。
- Playwright 的麦克风是假设备，CI 的 Edge 是 headless；真实设备项单独列出未验证。
- 中文 small 模型有近音字错误，未通过修参考文本或伪造输出掩盖。

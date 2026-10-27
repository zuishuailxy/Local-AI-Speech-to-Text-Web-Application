# 阶段一：需求理解与技术设计

> 本文件是 OpenCode 会话 `ses_e838f4101ffet1mEwSYEGuuSMK` 的**关键消息摘录**，不是完整历史。
> 已移除模型内部推理、工具原始输出、绝对路径与无关信息；保留需求、决策、方案与验证结论。

## 1. 会话元数据

| 项目 | 内容 |
| --- | --- |
| 工具 | OpenCode Desktop |
| 会话 ID | `ses_e838f4101ffet1mEwSYEGuuSMK` |
| 会话标题 | 面试考核题需求分析与规划 |
| 模型 | `deepseek-flash`（variant: high） |
| 日期 | 2026-10-27 |
| 项目目录 | `<repo>` |
| 输入 | `面试考核题-v1.md` |
| 产物 | `plan.md`、`todo.md`、本记录 |

## 2. 用户目标（首次请求，摘录）

用户要求先完整读取 `面试考核题-v1.md`，完成需求分析与开发规划；当前阶段明确限制：

- 只做需求分析和计划编制；
- 不编写业务代码；
- 不安装依赖；
- 不下载模型；
- 不修改现有业务文件；
- 生成 `plan.md` 与 `todo.md`，并在完成后汇报。

计划必须覆盖：项目目标与验收、必做/加分/不做范围、技术方案、ASR 候选比较、CPU/Windows/离线/依赖风险、F1–F6 与接口/环境/测试/文档映射、两天排期、风险与决策分类；任务清单必须可逐项执行和验收。

## 3. OpenCode 的执行过程

### 3.1 读取与拆解需求

OpenCode 首先完整读取题目，提取出：

- F1 浏览器麦克风录音（含 60 秒上限、状态、时长、权限/录音失败提示）。
- F2 WAV + 浏览器录音格式上传，共用后端识别逻辑。
- F3 本地开源中英文 ASR，CPU 推理，页面选择 `zh`/`en`，模型准备后离线可用，禁止云端 ASR 与 Web Speech API。
- F4 语言、状态、文本、音频时长、处理耗时、复制。
- F5 8 类异常 + 10 MB 上传限制。
- F6 加分实时识别（用户后续确认要做）。
- 三个必做接口、Windows 11 + Python 3.12 启动、pytest、真实模型验证、6 项手动验证、5 份文档、OpenCode 三阶段证据。
- 明确不做：登录、数据库、历史、说话人识别、降噪、翻译、TTS、训练、分布式、多用户、手机适配。

### 3.2 事实核查（规划阶段允许的元数据查询）

OpenCode 查询了 PyPI 元数据与官方 README，用于避免把未经验证的性能/兼容性写成事实：

- `faster-whisper 1.2.1` 依赖 `ctranslate2>=4,<5`、`av>=11`、`onnxruntime>=1.14,<2`。
- `ctranslate2 4.8.4`、`av 19.0.2`、`onnxruntime 1.31.1` 存在 cp312 win_amd64 wheel。
- `sherpa-onnx 2.0.1` 与 `sherpa-onnx-core 2.0.1` 存在 win_amd64 wheel。
- faster-whisper 官方 README 支持 CPU int8、Silero VAD、指定语言、本地目录加载。
- SenseVoice 官方资料：非自回归、支持中英日韩粤、宣称比 Whisper-small 快 5 倍以上、权重使用 FunASR Model Open Source License。
- 明确标注：以上只证明“有对应 wheel/官方声明”，**未在 Windows 11 实机验证**；实际速度/准确率、PyAV 无系统 ffmpeg 解码、模型下载可达性均需实验。

### 3.3 生成计划与任务

OpenCode 生成：

- `plan.md`：目标/范围/验收、技术方案与目录、ASR 对比、需求映射、两天排期、风险、决策分类、事实/假设区分。
- `todo.md`：按 P0–P9 排列的任务，每项包含目标、文件、前置条件、完成标准、验证方式；自动化、真实模型、手动、离线、Windows CI、文档、OpenCode 留痕均单列任务。

## 4. 关键对话摘录

### 4.1 第一轮方案汇报（助手，节选）

> 推荐：FastAPI + 原生 HTML/CSS/JavaScript + faster-whisper（Whisper small，CTranslate2 CPU int8）+ PyAV + pytest。
>
> 理由：一个多语言模型覆盖中英文；纯 pip 安装；CPU int8；本地模型目录离线；PyAV 统一解码 WAV/WebM；相比 whisper.cpp 不需要编译，相比 FunASR 不引入 PyTorch 重依赖。
>
> 风险：Windows 11 实机未验证；HuggingFace 下载可能被阻断；CPU 速度/中文准确率需实测；浏览器录音格式/权限异常需手动验证；默认测试必须不触发模型下载。
>
> 待确认：Windows 验证条件、模型规模、样本来源、Git/OpenCode 公开范围、是否做 F6。

### 4.2 用户决策 D1–D5（原文）

> D1：目前没有Windows 11 实机用于测试 D2:small ，D3：测试音频用本人录音 D4：git 仓库 D5：要做实时识别
>
> 另外：为什么不选择 sherpa-onnx + SenseVoiceSmall

### 4.3 关于 SenseVoiceSmall 的讨论（助手，节选）

结论先说：它不是被排除，而是主要备选。

优势：

- 非自回归，官方宣称同参数量下比 Whisper-small 快 5 倍以上。
- 中文/粤语优势，内置语种识别、ITN 标点。
- sherpa-onnx 支持 Windows x64，PyPI 有 win_amd64 wheel，不依赖 PyTorch。
- 官方提供 VAD + SenseVoice 的近实时示例。

没有直接作为主方案的原因：

1. 不是原生流式模型；30 秒输入限制，长音频/实时仍需 VAD/窗口切分，真正流式通常另配 streaming zipformer。
2. 权重许可证是 FunASR Model Open Source License，而 Whisper 权重是 MIT；演示可用，但分发条件不同。
3. 需要 sherpa-onnx 转换后的 ONNX 模型；自行转换会引入 PyTorch；模型源可达性未实测。
4. Python API、ITN 输出、WebM 解码组合、Windows CI 都是额外未知数；2 天且无 Windows 实机，优先减少未知数。
5. Whisper 英文/多语言生态更成熟；SenseVoice 公开优势集中在中文/粤语。
6. 识别层已抽象，后续切换成本低；先交付 Whisper 基线更稳。

最终建议：Whisper 基线 + 条件触发的时间盒评估（60–90 分钟），而不是一开始同时维护两套模型。

### 4.4 用户确认 D6/D7（原文）

> 1. Git 仓库托管在哪里： GitHub，而且我已经初始化了。2.模型路线选哪种：A

### 4.5 实施约束确认（原文）

> 你只需要提交，我手动来 push。现在开始实施 T0.5，T0.6

## 5. 最终决策记录

| 编号 | 决策 | 影响 |
| --- | --- | --- |
| D1 | 没有 Windows 11 实机 | 用 GitHub Actions `windows-latest` 做安装/启动/API/真实模型/Playwright 假麦克风替代验证；真实 Windows 11 桌面/麦克风明确标为未验证 |
| D2 | 模型规模 small | 默认 faster-whisper Whisper small，CPU int8 |
| D3 | 本人录制样本 | 中英文各 5–15 秒，注明授权、无敏感信息 |
| D4 | Git 仓库 | 分阶段提交、脱敏证据、模型权重不入库 |
| D5 | 要做 F6 | 必做通过后启动，3 小时时间盒，失败可回滚 |
| D6 | GitHub | 本地已初始化，`origin` 已由用户配置；push 已由用户完成；Actions 待 T1.8 验证 |
| D7 | 路线 A | Whisper small 为主，SenseVoiceSmall 作为条件备选；仅 T3.11 触发时评估 |

## 6. 产物与验证

- `plan.md` v0.3：包含 F1–F6、接口、环境、测试、文档映射；两天排期；风险 R1–R20；事实/假设区分。
- `todo.md`：83 项编号任务；T0.1–T0.7 已完成。
- 本地 Git：`main` 已有 initial commit；本阶段代理只做本地提交，用户已手动 push；Actions 实际运行待 T1.8。
- 未执行：依赖安装、模型下载、业务代码、Windows CI（需 T1.8 workflow）。

## 7. 备注

- 本记录的助手内容为最终回复摘录，不包含内部推理过程。
- 规划阶段查询过 PyPI/官方文档，但没有安装依赖或下载模型；相关结论仍需在 T1.2/T3.6 实测。
- 若后续实现与本文档冲突，以最终代码、测试报告和 `docs/design.md` 为准。

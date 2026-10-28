# Local AI Speech-to-Text Web Application

本地部署的中英文语音转文字 Web 应用。浏览器麦克风录音或上传音频，后端使用本地 `faster-whisper` 模型在 CPU 上识别，结果返回页面展示。

- 不需要云服务、GPU、Docker、数据库或 Node.js
- 模型准备完成后可完全离线识别
- 中文结果统一转为简体；英文保持英文
- 单用户、本机 `127.0.0.1` 使用，不做登录/并发/历史记录

## 1. 环境要求

| 项 | 要求 |
| --- | --- |
| Python | **3.12**（3.9 不支持） |
| 操作系统 | macOS / Linux / Windows 10/11 |
| CPU | 支持 AVX2 的 x64 或 Apple Silicon |
| 内存 | 最低 8 GB，推荐 16 GB |
| 磁盘 | 约 1 GB（依赖 + 模型约 464 MB） |
| 浏览器 | Chrome / Edge 最新稳定版 |
| 网络 | 仅首次下载模型需要 |

开发与验证环境：

- macOS arm64 / Apple M1 / 16 GB / Python 3.12.13 / Chrome 156
- Windows CI：`windows-latest`（Windows Server）/ Python 3.12.10 / Edge 155

> Windows CI 是 Windows Server，不是 Windows 11 桌面。真实 Windows 11 桌面和麦克风未验证，详见 [测试报告](docs/test-report.md)。

## 2. 安装

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果 PowerShell 阻止激活脚本，可只对当前用户调整执行策略：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

依赖已固定版本，核心包括 FastAPI、Uvicorn、faster-whisper、CTranslate2、PyAV、NumPy、zhconv。

## 3. 初始化模型

模型权重不提交到 Git，首次运行前下载一次：

```bash
python scripts/download_model.py --model small
```

默认目录：

```text
models/faster-whisper-small/
```

校验文件：`model.bin`、`config.json`、`tokenizer.json`、`vocabulary.txt`（或 `vocabulary.json`）。

### 国内网络 / 镜像

ModelScope（推荐在无法访问 HuggingFace 时使用）：

```bash
python scripts/download_model.py --model small --source modelscope
```

HuggingFace 镜像：

```bash
HF_ENDPOINT=https://hf-mirror.com python scripts/download_model.py --model small
```

PowerShell：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
python scripts/download_model.py --model small
```

也可以手动把 `Systran/faster-whisper-small` 的上述文件放到 `models/faster-whisper-small/`。

模型准备完成后，应用的识别路径不再访问网络；下载脚本是唯一会联网的入口。

## 4. 启动

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

说明：

- 必须通过 `http://127.0.0.1` 或 `http://localhost` 访问；`file://` 不是安全上下文，浏览器不会允许麦克风。
- 首次识别会加载模型，通常 1–2 秒；之后请求复用已加载模型。
- 端口被占用时换一个端口，例如 `--port 8001`。
- 默认只绑定 `127.0.0.1`，局域网其他设备无法访问。

调试日志：

```bash
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

PowerShell：

```powershell
$env:LOG_LEVEL = "DEBUG"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 5. 使用

1. 选择中文普通话（zh）或 English（en）
2. 点击 **Start Recording**，允许浏览器访问麦克风
3. 录音最长 60 秒；点击 **Stop Recording** 后提交
4. 或点击 **选择音频文件**，上传 WAV/WebM/OGG/MP3/M4A/MP4/FLAC
5. 等待结果，页面显示：
   - 识别文本
   - 语言
   - 音频时长
   - 处理耗时
   - 音频预览
6. 点击 **复制文本** 复制结果

限制：

- 上传文件最大 **10 MB**
- 解码后音频最长 **120 秒**
- 录音最长 **60 秒**，到时会自动停止并提交
- 空文件、损坏音频、非白名单格式、超限文件都会显示可读错误
- 静音或未检测到语音时返回空文本并提示

中文结果会经过本地 `zhconv` 繁转简；英文结果不转换。繁转简不修复同音字错误。

## 6. API

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok"}
```

### 识别

```bash
curl -X POST http://127.0.0.1:8000/api/transcribe \
  -F "file=@samples/chinese.wav" \
  -F "language=zh"
```

```json
{
  "text": "轻轻地我走了,占如我轻轻地来。我轻轻地抓手,做别西天的云彩。那河畔的金牛是西洋中的新娘。",
  "language": "zh",
  "duration_seconds": 12.0,
  "processing_seconds": 3.978
}
```

英文：

```bash
curl -X POST http://127.0.0.1:8000/api/transcribe \
  -F "file=@samples/english.wav" \
  -F "language=en"
```

错误响应格式：

```json
{
  "detail": "上传文件超过 10 MB 限制，请选择更短的音频。",
  "code": "file_too_large"
}
```

常见状态码：

| 状态 | code | 场景 |
| --- | --- | --- |
| 400 | `empty_file` / `invalid_audio` / `audio_too_long` / `invalid_language` | 空文件、损坏音频、超时长、非法语言 |
| 413 | `file_too_large` | 超过 10 MB |
| 415 | `unsupported_format` | 扩展名不在白名单 |
| 422 | `validation_error` | 缺少 file/language |
| 500 | `transcription_failed` | 推理异常 |
| 503 | `model_unavailable` | 模型缺失/加载失败 |

## 7. 配置

所有配置通过环境变量读取，启动时校验非法值。

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `ASR_MODEL_PATH` | `models/faster-whisper-small` | 本地模型目录 |
| `ASR_DEVICE` | `cpu` | 推理设备 |
| `ASR_COMPUTE_TYPE` | `int8` | CTranslate2 计算类型 |
| `ASR_CPU_THREADS` | `4` | CPU 线程数 |
| `ASR_BEAM_SIZE` | `5` | beam search |
| `ASR_VAD_FILTER` | `true` | 静音过滤 |
| `MAX_UPLOAD_MB` | `10` | 上传上限 |
| `MAX_AUDIO_SECONDS` | `120` | 解码后音频上限 |
| `LOG_LEVEL` | `INFO` | `DEBUG/INFO/WARNING/ERROR/CRITICAL` |

示例：

```bash
ASR_MODEL_PATH=/data/models/faster-whisper-small \
ASR_CPU_THREADS=6 \
LOG_LEVEL=DEBUG \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 8. 测试

默认测试不加载模型、不下载权重、不访问麦克风或外网：

```bash
python -m pytest -q
```

```text
203 passed, 8 deselected
```

8 个默认排除项：5 个 `real_model` + 3 个 `e2e`。

### 真实模型测试

先完成模型初始化：

```bash
python -m pytest -q -m real_model -s
```

```text
5 passed, 199 deselected
```

`-s` 会显示真实文本、参考文本、时长、推理耗时、RTF、CER/WER。使用：

- `samples/chinese.wav`（12.0 s）
- `samples/english.wav`（9.0 s）
- `tests/fixtures/speech-en.webm`（8.999 s）

模型缺失时 5 项会 skip，并提示 ModelScope 下载命令。

### 浏览器 E2E

E2E 默认不执行，使用假麦克风和 FakeTranscriber，不需要模型：

```bash
python -m pip install -r requirements-e2e.txt
python -m playwright install chromium
python -m pytest -q -m e2e
```

没有 Playwright Chromium 时可使用系统 Chrome：

```bash
PLAYWRIGHT_CHANNEL=chrome python -m pytest -q -m e2e
```

```text
3 passed
```

覆盖页面加载、WAV 上传 + 复制、假麦克风录音。Windows CI 另使用 Edge channel 跑同一套测试。

### 干净环境隔离

已验证：独立 venv（42 个依赖）+ 临时移走 `models/` + `HF_HUB_OFFLINE=1` + 黑洞代理：

```text
203 passed, 8 deselected in 2.53s
```

测试期间未创建 `models/`，无下载输出。详见 `docs/evidence/pytest-default.txt`。

## 9. 离线验证

模型下载完成后：

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

关闭 Wi-Fi/网卡，刷新页面，上传 `samples/chinese.wav` 和 `samples/english.wav`，均可正常识别。

已实测（真实 Wi-Fi 关闭）：

- 中文 12.0 s：processing 4.357 s，CER 0.1795
- 英文 9.0 s：processing 1.359 s，WER 0.0
- 无外网请求、无网络错误

证据：`docs/evidence/offline.txt`、`offline-zh.png`、`offline-en.png`。

## 10. 故障排查

### 503 `model_unavailable`

模型目录不存在或加载失败：

```bash
python scripts/download_model.py --model small --source modelscope
curl http://127.0.0.1:8000/health
```

确认 `models/faster-whisper-small/model.bin` 存在。恢复目录后无需重启服务，下一次请求会重新加载。

### 麦克风无法使用

- 使用 `http://127.0.0.1:8000` 或 `http://localhost:8000`，不要用 `file://`
- Chrome/Edge 地址栏站点设置中允许麦克风
- 关闭占用麦克风的其他程序
- macOS：系统设置 → 隐私与安全性 → 麦克风 → 允许浏览器

### 第一次识别很慢

首次请求会加载模型，正常约 1–3 秒；后续请求会复用模型。CPU 性能较弱时单次推理可能更慢。

### HuggingFace 超时

```bash
python scripts/download_model.py --model small --source modelscope
```

或设置 `HF_ENDPOINT=https://hf-mirror.com` 后重试。

### 端口被占用

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN   # macOS/Linux
netstat -ano | findstr :8000       # Windows
```

换端口启动即可。

### `/v1/models` 返回 404

本项目不是 OpenAI 兼容服务，没有 `/v1/models`。该请求通常来自另一个配置为 `http://127.0.0.1:8000/v1` 的本地 AI 客户端/浏览器扩展；不影响 `/health` 和 `/api/transcribe`。

### 中文出现繁体/同音字

- 繁体：后端已用 `zhconv` 统一转简体
- 同音字：small 模型能力限制，例如“语音识别”可能被识别成近音词；换更大模型或改初始提示可改善，但会增加 CPU 开销

## 11. 已知限制

- 真实 Windows 11 桌面/麦克风未验证；Windows CI 是 Windows Server。
- 桌面 Edge 未手动验证；CI 为 headless Edge + 假麦克风。
- 无设备/设备占用场景使用 DevTools 注入验证，不是真实拔设备。
- 60 秒自动停止页面计时为 60.0 s，但服务端音频曾为 57.18 s，差约 2.8 s；未超过上限，待排查 MediaRecorder/封装/后台节流。
- 中文 small 模型存在近音字错误，CER 约 0.18–0.23。
- 样本只覆盖单人、安静环境、正常语速；噪声、远场、中英混合未覆盖。
- 语言选择不强制输出目标语言；音频与所选语言不一致时可能输出源语言，日志会记录 `asr_language_mismatch`。
- 单用户、无登录、无并发控制、无历史记录；只绑定本机。
- 实时识别（F6）尚未实现。

## 12. 项目结构

```text
.
├── app/
│   ├── main.py                 # 应用工厂、/health、静态页、请求日志
│   ├── config.py               # 环境变量配置
│   ├── errors.py               # 统一错误模型
│   ├── schemas.py              # 响应模型
│   ├── api/routes.py           # POST /api/transcribe
│   └── services/
│       ├── audio.py            # 上传/流式大小/解码/清理
│       ├── transcriber.py      # faster-whisper 适配器
│       ├── metrics.py          # CER/WER
│       └── text.py             # 繁转简
├── static/                     # index.html / styles.css / app.js / favicon
├── scripts/
│   ├── download_model.py       # 模型准备（唯一联网入口）
│   └── verify_asr.py           # CLI 冒烟
├── samples/                    # chinese.wav / english.wav / reference.txt
├── tests/                      # 默认/真实模型/E2E
├── docs/
│   ├── test-report.md
│   ├── evidence/
│   └── opencode/
├── models/                     # 本地权重，Git 忽略
├── requirements.txt
├── requirements-e2e.txt
├── pytest.ini
└── README.md
```

## 13. 证据与文档

- 测试报告：[`docs/test-report.md`](docs/test-report.md)
- 需求说明：[`docs/requirements.md`](docs/requirements.md)
- 设计说明：[`docs/design.md`](docs/design.md)
- 证据目录：[`docs/evidence/`](docs/evidence/)
- OpenCode 三阶段记录：[`docs/opencode/`](docs/opencode/)
- Windows CI：[`docs/evidence/windows-ci.txt`](docs/evidence/windows-ci.txt)
- 真实模型基线：[`docs/evidence/asr-baseline.md`](docs/evidence/asr-baseline.md)

自动化结果：

```text
默认：203 passed, 8 deselected
真实模型：5 passed
浏览器 E2E：3 passed
Windows CI：Chromium + Edge + 真实模型通过
```

Windows CI 不能替代 Windows 11 实机验证；真实桌面/麦克风项在测试报告中单列为未验证。

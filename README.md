# Local AI Speech-to-Text Web Application

## Model initialization

首次运行前需要下载一次本地 ASR 模型权重（不提交到 Git）：

```bash
python scripts/download_model.py --model small
```

默认下载到 `models/faster-whisper-small/`，并校验 `model.bin`、`config.json`、`tokenizer.json`、`vocabulary.*`。

如果 HuggingFace 访问缓慢，可先设置镜像：

```bash
HF_ENDPOINT=https://hf-mirror.com python scripts/download_model.py --model small
```

中国大陆网络也可直接使用 ModelScope 公共镜像：

```bash
python scripts/download_model.py --model small --source modelscope
```

也可以手动下载 `Systran/faster-whisper-small` 到该目录。模型准备完成后，识别过程不访问网络。

## Logging

应用使用 Python 标准库 `logging`，默认级别 `INFO`，可用环境变量覆盖：

```bash
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

日志包含：

- 应用配置（模型路径、设备、线程、上传/时长限制）
- 每个请求的方法、路径、状态码、耗时和 `request_id`
- 上传扩展名/字节数、解码后时长/采样数
- 识别请求语言、模型检测语言、输出脚本占比、推理耗时、文本字符数
- 4xx/5xx 错误码与异常栈（仅未预期异常）

日志不记录音频内容、识别文本原文或请求体。响应头 `X-Request-ID` 可用于把浏览器请求与后端日志对应起来。

### Chinese output

Whisper 的 `zh` 只约束语言，不区分简体/繁体。后端对中文识别结果使用本地 `zhconv` 统一转为简体；英文结果不变。该步骤不修复同音字错误。

## Tests

默认测试不加载模型、不下载权重、不访问麦克风或外网：

```bash
python -m pytest -q
```

```text
196 passed, 8 deselected
```

8 个默认排除项为 5 个 `real_model` + 3 个 `e2e`。

### Real model tests

先完成模型初始化，再显式启用 `real_model`：

```bash
python scripts/download_model.py --model small
python -m pytest -q -m real_model -s
```

```text
5 passed, 199 deselected
```

`-s` 会显示真实文本、参考文本、时长、推理耗时、RTF、CER/WER。测试使用 `samples/chinese.wav`、`samples/english.wav` 和 `tests/fixtures/speech-en.webm`，模型缺失时会 skip 并提示下载命令。

### Browser E2E

浏览器 E2E 默认不执行，使用假麦克风与 `FakeTranscriber`，不需要模型：

```bash
python -m pip install -r requirements-e2e.txt
python -m playwright install chromium
python -m pytest -q -m e2e
```

本机没有 Playwright Chromium 时，可使用系统 Chrome：

```bash
PLAYWRIGHT_CHANNEL=chrome python -m pytest -q -m e2e
```

```text
3 passed
```

E2E 覆盖页面加载、WAV 上传、假麦克风录音；真实麦克风仍按手动验证执行。

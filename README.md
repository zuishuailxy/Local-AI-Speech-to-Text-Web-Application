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


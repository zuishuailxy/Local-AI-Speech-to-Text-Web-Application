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

也可以手动下载 `Systran/faster-whisper-small` 到该目录。模型准备完成后，识别过程不访问网络。


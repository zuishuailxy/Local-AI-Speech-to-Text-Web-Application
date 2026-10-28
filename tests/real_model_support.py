"""Shared helpers for opt-in tests that need the real local model."""

from __future__ import annotations

import pytest

from app.config import Settings

MODEL_FILES = ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")


def missing_model_files(settings: Settings) -> list[str]:
    return [
        name
        for name in MODEL_FILES
        if not (settings.asr_model_path / name).is_file()
    ]


def require_model(settings: Settings) -> None:
    """Skip the calling test with an actionable message when weights are absent."""

    missing = missing_model_files(settings)
    if not missing:
        return
    pytest.skip(
        "本地模型缺失（"
        + ", ".join(missing)
        + f"）：{settings.asr_model_path}。先运行 "
        "python scripts/download_model.py --model small --source modelscope"
    )

"""Download a CTranslate2 Whisper model into the local models directory.

Usage:
    python scripts/download_model.py --model small
    python scripts/download_model.py --model small --output models/faster-whisper-small

This script is the only place that intentionally accesses the network.  Runtime
transcription loads the resulting local directory and never downloads weights.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, Sequence

from huggingface_hub import snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "small"
MODEL_REPOS: dict[str, str] = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}
ALLOW_PATTERNS = [
    "config.json",
    "preprocessor_config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.*",
]
REQUIRED_FILES = ("model.bin", "config.json", "tokenizer.json")


class ModelDownloadError(RuntimeError):
    """A model download or post-download validation error."""


Downloader = Callable[..., str]


def repo_for_model(model: str) -> str:
    repo = MODEL_REPOS.get(model)
    if repo is None:
        supported = ", ".join(MODEL_REPOS)
        raise ModelDownloadError(
            f"不支持的模型规格: {model!r}；可选: {supported}"
        )
    return repo


def default_output(model: str) -> Path:
    return PROJECT_ROOT / "models" / f"faster-whisper-{model}"


def missing_required_files(output: Path) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (output / name).is_file()]
    if not (output / "vocabulary.txt").is_file() and not (
        output / "vocabulary.json"
    ).is_file():
        missing.append("vocabulary.txt|vocabulary.json")
    return missing


def verify_model_dir(output: Path) -> None:
    if not output.is_dir():
        raise ModelDownloadError(f"模型目录不存在: {output}")
    missing = missing_required_files(output)
    if missing:
        raise ModelDownloadError(
            "模型目录缺少必要文件: " + ", ".join(missing)
        )


def download_model(
    model: str = DEFAULT_MODEL,
    output: Path | None = None,
    *,
    revision: str | None = None,
    endpoint: str | None = None,
    force_download: bool = False,
    downloader: Downloader = snapshot_download,
) -> Path:
    """Download and validate a model; ``downloader`` is injectable for tests."""

    repo_id = repo_for_model(model)
    destination = (output or default_output(model)).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, object] = {
        "repo_id": repo_id,
        "local_dir": str(destination),
        "allow_patterns": ALLOW_PATTERNS,
        "revision": revision,
        "force_download": force_download,
    }
    if endpoint:
        kwargs["endpoint"] = endpoint

    try:
        downloader(**kwargs)
    except Exception as exc:
        raise ModelDownloadError(
            "模型下载失败。请检查网络/代理，或设置 HF_ENDPOINT 镜像后重试；"
            f"也可以手动下载 {repo_id} 并放到 {destination}。原始错误: {exc}"
        ) from exc

    verify_model_dir(destination)
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a faster-whisper CTranslate2 model for local CPU inference."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        choices=sorted(MODEL_REPOS),
        help="Model size (default: small)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination directory (default: models/faster-whisper-<model>)",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional HuggingFace revision",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("HF_ENDPOINT"),
        help="HuggingFace endpoint/mirror (default: HF_ENDPOINT env var)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files already exist",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        destination = download_model(
            args.model,
            args.output,
            revision=args.revision,
            endpoint=args.endpoint,
            force_download=args.force,
        )
        verify_model_dir(destination)
    except ModelDownloadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"模型已就绪: {destination}")
    print("关键文件:")
    for name in (*REQUIRED_FILES, "vocabulary.txt/vocabulary.json"):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Download a CTranslate2 Whisper model into the local models directory.

Usage:
    python scripts/download_model.py --model small
    python scripts/download_model.py --model small --output models/faster-whisper-small

This script is the only place that intentionally accesses the network.  Runtime
transcription loads the resulting local directory and never downloads weights.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Sequence

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
MODELSCOPE_BASE = "https://www.modelscope.cn"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


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


def _wanted_model_file(path: str) -> bool:
    name = Path(path).name
    return name in {
        "config.json",
        "preprocessor_config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.txt",
        "vocabulary.json",
    }


def modelscope_files(
    repo_id: str,
    *,
    timeout: int = 60,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    url = (
        f"{MODELSCOPE_BASE}/api/v1/models/{repo_id}/repo/files"
        "?Revision=master&Recursive=true"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "local-speech-to-text/0.1"}
    )
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ModelDownloadError(
            f"ModelScope 文件列表获取失败 ({repo_id}): {exc}"
        ) from exc

    if payload.get("Code") != 200:
        raise ModelDownloadError(
            f"ModelScope 返回异常: {payload.get('Message') or payload}"
        )
    files = payload.get("Data", {}).get("Files", [])
    if not files:
        raise ModelDownloadError(f"ModelScope 仓库没有文件: {repo_id}")
    return files


def download_modelscope(
    repo_id: str,
    destination: Path,
    *,
    force_download: bool = False,
    timeout: int = 60,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> Path:
    """Download selected files from ModelScope's public repo HTTP API."""

    files = [
        item
        for item in modelscope_files(repo_id, timeout=timeout, opener=opener)
        if _wanted_model_file(str(item.get("Path", "")))
    ]
    if not files:
        raise ModelDownloadError(f"ModelScope 仓库没有所需模型文件: {repo_id}")

    destination.mkdir(parents=True, exist_ok=True)
    for item in files:
        relative = Path(str(item["Path"]))
        target = destination / relative
        expected_size = int(item.get("Size") or 0)
        if (
            not force_download
            and target.is_file()
            and (expected_size == 0 or target.stat().st_size == expected_size)
        ):
            print(f"跳过已存在文件: {relative}")
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        query = urllib.parse.urlencode(
            {"Revision": "master", "FilePath": relative.as_posix()}
        )
        url = f"{MODELSCOPE_BASE}/api/v1/models/{repo_id}/repo?{query}"
        temporary = target.with_name(target.name + ".part")
        print(f"下载 {relative} ({expected_size / (1024 * 1024):.1f} MiB)...")
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "local-speech-to-text/0.1"}
            )
            with opener(request, timeout=timeout) as response, temporary.open(
                "wb"
            ) as output:
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    output.write(chunk)
            os.replace(temporary, target)
        except Exception as exc:
            temporary.unlink(missing_ok=True)
            raise ModelDownloadError(
                f"ModelScope 下载失败 ({relative}): {exc}"
            ) from exc

    return destination


def download_model(
    model: str = DEFAULT_MODEL,
    output: Path | None = None,
    *,
    revision: str | None = None,
    endpoint: str | None = None,
    force_download: bool = False,
    source: str = "huggingface",
    downloader: Downloader = snapshot_download,
) -> Path:
    """Download and validate a model; ``downloader`` is injectable for tests."""

    repo_id = repo_for_model(model)
    destination = (output or default_output(model)).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    if source == "modelscope":
        try:
            download_modelscope(
                repo_id,
                destination,
                force_download=force_download,
            )
        except ModelDownloadError:
            raise
        except Exception as exc:
            raise ModelDownloadError(
                f"ModelScope 模型下载失败 ({repo_id}): {exc}"
            ) from exc
        verify_model_dir(destination)
        return destination

    if source != "huggingface":
        raise ModelDownloadError(f"不支持的下载源: {source!r}")

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
            f"也可以使用 --source modelscope 或手动下载 {repo_id} 并放到 {destination}。"
            f"原始错误: {exc}"
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
        "--source",
        choices=("huggingface", "modelscope"),
        default="huggingface",
        help="Model source (default: huggingface; modelscope is useful in mainland China)",
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
            source=args.source,
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

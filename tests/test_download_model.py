from __future__ import annotations

from pathlib import Path

import pytest

from scripts.download_model import (
    ALLOW_PATTERNS,
    MODEL_REPOS,
    ModelDownloadError,
    default_output,
    download_model,
    missing_required_files,
    repo_for_model,
    verify_model_dir,
)


def create_model_files(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "model.bin").write_bytes(b"fake-model")
    (directory / "config.json").write_text("{}", encoding="utf-8")
    (directory / "tokenizer.json").write_text("{}", encoding="utf-8")
    (directory / "vocabulary.txt").write_text("a\nb\n", encoding="utf-8")


def test_model_repo_mapping() -> None:
    assert repo_for_model("small") == "Systran/faster-whisper-small"
    assert repo_for_model("base") == "Systran/faster-whisper-base"
    assert "small" in MODEL_REPOS


def test_invalid_model_is_rejected() -> None:
    with pytest.raises(ModelDownloadError, match="不支持的模型规格"):
        repo_for_model("huge")


def test_default_output_is_project_models_dir() -> None:
    path = default_output("small")

    assert path.name == "faster-whisper-small"
    assert path.parent.name == "models"


def test_verify_model_dir_accepts_complete_model(tmp_path) -> None:
    create_model_files(tmp_path)

    verify_model_dir(tmp_path)

    assert missing_required_files(tmp_path) == []


def test_verify_model_dir_rejects_missing_files(tmp_path) -> None:
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ModelDownloadError, match="缺少必要文件"):
        verify_model_dir(tmp_path)


def test_download_uses_injected_downloader_and_validates(tmp_path) -> None:
    calls: dict[str, object] = {}
    destination = tmp_path / "model"

    def fake_downloader(**kwargs):
        calls.update(kwargs)
        create_model_files(Path(kwargs["local_dir"]))
        return str(destination)

    result = download_model(
        "small",
        destination,
        endpoint="https://hf-mirror.example",
        downloader=fake_downloader,
    )

    assert result == destination
    assert calls["repo_id"] == "Systran/faster-whisper-small"
    assert calls["local_dir"] == str(destination)
    assert calls["allow_patterns"] == ALLOW_PATTERNS
    assert calls["endpoint"] == "https://hf-mirror.example"
    verify_model_dir(destination)


def test_download_failure_is_actionable(tmp_path) -> None:
    def failing_downloader(**kwargs):
        raise RuntimeError("network down")

    with pytest.raises(ModelDownloadError) as exc_info:
        download_model("small", tmp_path / "model", downloader=failing_downloader)

    message = str(exc_info.value)
    assert "HF_ENDPOINT" in message
    assert "Systran/faster-whisper-small" in message
    assert "network down" in message


def test_incomplete_download_is_rejected(tmp_path) -> None:
    def partial_downloader(**kwargs):
        destination = Path(kwargs["local_dir"])
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "config.json").write_text("{}", encoding="utf-8")
        return str(destination)

    with pytest.raises(ModelDownloadError, match="缺少必要文件"):
        download_model("small", tmp_path / "model", downloader=partial_downloader)

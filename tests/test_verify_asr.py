from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from app.config import Settings
from app.errors import InvalidLanguageError
from app.services.transcriber import FakeTranscriber
from scripts import verify_asr


def test_run_verification_with_injected_transcriber(tmp_path, wav_file_factory) -> None:
    audio_path = wav_file_factory(1.0)
    settings = Settings.from_env(environ={}, project_root=tmp_path)
    fake = FakeTranscriber(text="你好，测试。")

    output = verify_asr.run_verification(
        audio_path,
        "zh",
        settings,
        transcriber=fake,
    )

    assert output.text == "你好，测试。"
    assert output.language == "zh"
    assert output.duration_seconds == pytest.approx(1.0, abs=0.01)
    assert output.processing_seconds >= 0
    samples, language = fake.calls[0]
    assert isinstance(samples, np.ndarray)
    assert samples.shape == (16_000,)
    assert language == "zh"


def test_missing_audio_is_reported(tmp_path) -> None:
    settings = Settings.from_env(environ={}, project_root=tmp_path)

    with pytest.raises(FileNotFoundError):
        verify_asr.run_verification(
            tmp_path / "missing.wav",
            "zh",
            settings,
            transcriber=FakeTranscriber(),
        )


def test_invalid_language_is_rejected(tmp_path, wav_file_factory) -> None:
    settings = Settings.from_env(environ={}, project_root=tmp_path)

    with pytest.raises(InvalidLanguageError):
        verify_asr.run_verification(
            wav_file_factory(1.0),
            "fr",
            settings,
            transcriber=FakeTranscriber(),
        )


def test_main_missing_model_prints_actionable_hint(
    tmp_path, wav_file_factory, capsys
) -> None:
    audio_path = wav_file_factory(1.0)

    code = verify_asr.main(
        [
            str(audio_path),
            "--language",
            "zh",
            "--model-path",
            str(tmp_path / "no-model-here"),
        ]
    )

    captured = capsys.readouterr()
    assert code == 1
    assert "ERROR:" in captured.err
    assert "download_model.py" in captured.err


def test_main_success_with_fake_engine(
    tmp_path, wav_file_factory, monkeypatch, capsys
) -> None:
    audio_path = wav_file_factory(1.0)
    fake = FakeTranscriber(text="fake CLI text")
    monkeypatch.setattr(
        verify_asr,
        "WhisperTranscriber",
        lambda settings: fake,
    )

    code = verify_asr.main(
        [
            str(audio_path),
            "--language",
            "en",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "text: fake CLI text" in captured.out
    assert "language: en" in captured.out
    assert "duration_seconds:" in captured.out
    assert "processing_seconds:" in captured.out


def test_cli_help_runs_as_script_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "verify_asr.py"), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Verify local faster-whisper" in completed.stdout

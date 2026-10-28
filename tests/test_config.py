from __future__ import annotations

from pathlib import Path

import pytest

from app.config import SUPPORTED_LANGUAGES, Settings


def test_defaults_are_stable(tmp_path: Path) -> None:
    settings = Settings.from_env(environ={}, project_root=tmp_path)

    assert settings.project_root == tmp_path
    assert settings.asr_model_path == (tmp_path / "models" / "faster-whisper-small").resolve()
    assert settings.asr_model_size == "small"
    assert settings.asr_device == "cpu"
    assert settings.asr_compute_type == "int8"
    assert settings.asr_cpu_threads == 4
    assert settings.asr_beam_size == 5
    assert settings.asr_vad_filter is True
    assert settings.asr_warmup is True
    assert settings.max_upload_mb == 10
    assert settings.max_upload_bytes == 10 * 1024 * 1024
    assert settings.max_audio_seconds == 120
    assert settings.log_level == "INFO"
    assert settings.log_file is None
    assert settings.log_format == "text"
    assert settings.log_max_bytes == 5 * 1024 * 1024
    assert settings.log_backup_count == 3
    assert settings.asr_initial_prompt == ""
    assert settings.supported_languages == SUPPORTED_LANGUAGES


def test_environment_overrides_and_relative_model_path(tmp_path: Path) -> None:
    settings = Settings.from_env(
        environ={
            "ASR_MODEL_PATH": "custom/models/whisper",
            "ASR_MODEL_SIZE": "base",
            "ASR_DEVICE": "cpu",
            "ASR_COMPUTE_TYPE": "float32",
            "ASR_CPU_THREADS": "8",
            "ASR_BEAM_SIZE": "3",
            "ASR_VAD_FILTER": "false",
            "ASR_WARMUP": "no",
            "MAX_UPLOAD_MB": "5",
            "MAX_AUDIO_SECONDS": "60",
            "LOG_LEVEL": "debug",
            "LOG_FILE": "logs/app.log",
            "LOG_FORMAT": "json",
            "LOG_MAX_BYTES": "1024",
            "LOG_BACKUP_COUNT": "2",
            "ASR_INITIAL_PROMPT": "  以下是普通话的句子。  ",
        },
        project_root=tmp_path,
    )

    assert settings.asr_model_path == (tmp_path / "custom" / "models" / "whisper").resolve()
    assert settings.asr_model_size == "base"
    assert settings.asr_compute_type == "float32"
    assert settings.asr_cpu_threads == 8
    assert settings.asr_beam_size == 3
    assert settings.asr_vad_filter is False
    assert settings.asr_warmup is False
    assert settings.max_upload_mb == 5
    assert settings.max_upload_bytes == 5 * 1024 * 1024
    assert settings.max_audio_seconds == 60
    assert settings.log_level == "DEBUG"
    assert settings.log_file == (tmp_path / "logs" / "app.log").resolve()
    assert settings.log_format == "json"
    assert settings.log_max_bytes == 1024
    assert settings.log_backup_count == 2
    assert settings.asr_initial_prompt == "以下是普通话的句子。"


def test_absolute_model_path_is_preserved(tmp_path: Path) -> None:
    model_path = tmp_path / "absolute-model"
    settings = Settings.from_env(
        environ={"ASR_MODEL_PATH": str(model_path)},
        project_root=tmp_path,
    )

    assert settings.asr_model_path == model_path.resolve()


def test_model_size_selects_default_path(tmp_path: Path) -> None:
    settings = Settings.from_env(
        environ={"ASR_MODEL_SIZE": "medium"},
        project_root=tmp_path,
    )

    assert settings.asr_model_size == "medium"
    assert settings.asr_model_path == (
        tmp_path / "models" / "faster-whisper-medium"
    ).resolve()


def test_blank_model_path_falls_back_to_default(tmp_path: Path) -> None:
    settings = Settings.from_env(
        environ={"ASR_MODEL_PATH": "   "},
        project_root=tmp_path,
    )

    assert settings.asr_model_path == (tmp_path / "models" / "faster-whisper-small").resolve()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_boolean_parsing(raw: str, expected: bool, tmp_path: Path) -> None:
    settings = Settings.from_env(
        environ={"ASR_VAD_FILTER": raw, "ASR_WARMUP": raw},
        project_root=tmp_path,
    )

    assert settings.asr_vad_filter is expected
    assert settings.asr_warmup is expected


def test_invalid_boolean_names_the_variable(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ASR_VAD_FILTER"):
        Settings.from_env(environ={"ASR_VAD_FILTER": "sometimes"}, project_root=tmp_path)


def test_invalid_log_level_names_the_variable(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings.from_env(
            environ={"LOG_LEVEL": "verbose"},
            project_root=tmp_path,
        )


def test_invalid_log_format_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="LOG_FORMAT"):
        Settings.from_env(
            environ={"LOG_FORMAT": "xml"},
            project_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ASR_CPU_THREADS", "0"),
        ("ASR_CPU_THREADS", "-1"),
        ("ASR_CPU_THREADS", "abc"),
        ("ASR_BEAM_SIZE", "0"),
        ("MAX_UPLOAD_MB", "-1"),
        ("MAX_AUDIO_SECONDS", "0"),
    ],
)
def test_invalid_positive_integers_are_rejected(
    name: str, value: str, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match=name):
        Settings.from_env(environ={name: value}, project_root=tmp_path)


def test_settings_are_immutable(tmp_path: Path) -> None:
    settings = Settings.from_env(environ={}, project_root=tmp_path)

    with pytest.raises((AttributeError, TypeError)):
        settings.max_upload_mb = 99  # type: ignore[misc]


def test_too_long_initial_prompt_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ASR_INITIAL_PROMPT"):
        Settings.from_env(
            environ={"ASR_INITIAL_PROMPT": "x" * 501},
            project_root=tmp_path,
        )

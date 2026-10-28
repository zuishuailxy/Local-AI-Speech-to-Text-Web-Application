"""Application configuration.

All runtime knobs live here so the API, audio layer and ASR engine do not
scatter magic numbers. Values can be overridden with environment variables;
invalid values fail fast with a message naming the variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = Path("models") / "faster-whisper-small"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("zh", "en")

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _read_env(env: Mapping[str, str], name: str, default: str) -> str:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip()


def _parse_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = _read_env(env, name, "true" if default else "false").lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ValueError(f"{name} must be one of: true/false, 1/0, yes/no, on/off")


def _parse_positive_int(
    env: Mapping[str, str], name: str, default: int, minimum: int = 1
) -> int:
    raw = _read_env(env, name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got: {raw!r}") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got: {value}")
    return value


def _parse_log_level(env: Mapping[str, str], name: str, default: str) -> str:
    raw = _read_env(env, name, default).upper()
    if raw not in _LOG_LEVELS:
        allowed = ", ".join(sorted(_LOG_LEVELS))
        raise ValueError(f"{name} must be one of: {allowed}; got: {raw!r}")
    return raw


def _parse_prompt(env: Mapping[str, str], name: str, max_chars: int) -> str:
    value = _read_env(env, name, "").strip()
    if len(value) > max_chars:
        raise ValueError(
            f"{name} must be at most {max_chars} characters; got {len(value)}"
        )
    return value


def _parse_log_format(env: Mapping[str, str], name: str, default: str) -> str:
    raw = _read_env(env, name, default).lower()
    if raw not in {"text", "json"}:
        raise ValueError(f"{name} must be one of: text, json; got: {raw!r}")
    return raw


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable settings resolved from environment variables."""

    project_root: Path
    asr_model_path: Path
    asr_model_size: str
    asr_device: str
    asr_compute_type: str
    asr_cpu_threads: int
    asr_beam_size: int
    asr_vad_filter: bool
    asr_warmup: bool
    max_upload_mb: int
    max_audio_seconds: int
    asr_initial_prompt: str = ""
    log_level: str = "INFO"
    log_file: Path | None = None
    log_format: str = "text"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 3
    supported_languages: tuple[str, ...] = SUPPORTED_LANGUAGES

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        project_root: Path | None = None,
    ) -> "Settings":
        """Build settings from a mapping (defaults to ``os.environ``).

        Relative model paths are resolved against ``project_root`` so the same
        environment variable works on Windows and POSIX without relying on the
        process working directory.
        """

        env = os.environ if environ is None else environ
        root = (project_root or PROJECT_ROOT).expanduser().resolve()

        model_size = _read_env(env, "ASR_MODEL_SIZE", "small")
        default_model_path = Path("models") / f"faster-whisper-{model_size}"
        raw_model_path = _read_env(env, "ASR_MODEL_PATH", str(default_model_path))
        model_path = Path(raw_model_path).expanduser()
        if not model_path.is_absolute():
            model_path = root / model_path

        raw_log_file = _read_env(env, "LOG_FILE", "")
        log_file = None
        if raw_log_file:
            candidate = Path(raw_log_file).expanduser()
            if not candidate.is_absolute():
                candidate = root / candidate
            log_file = candidate.resolve()

        return cls(
            project_root=root,
            asr_model_path=model_path.resolve(),
            asr_model_size=model_size,
            asr_device=_read_env(env, "ASR_DEVICE", "cpu"),
            asr_compute_type=_read_env(env, "ASR_COMPUTE_TYPE", "int8"),
            asr_cpu_threads=_parse_positive_int(env, "ASR_CPU_THREADS", 4),
            asr_beam_size=_parse_positive_int(env, "ASR_BEAM_SIZE", 5),
            asr_vad_filter=_parse_bool(env, "ASR_VAD_FILTER", True),
            asr_warmup=_parse_bool(env, "ASR_WARMUP", True),
            asr_initial_prompt=_parse_prompt(env, "ASR_INITIAL_PROMPT", 500),
            max_upload_mb=_parse_positive_int(env, "MAX_UPLOAD_MB", 10),
            max_audio_seconds=_parse_positive_int(env, "MAX_AUDIO_SECONDS", 120),
            log_level=_parse_log_level(env, "LOG_LEVEL", "INFO"),
            log_file=log_file,
            log_format=_parse_log_format(env, "LOG_FORMAT", "text"),
            log_max_bytes=_parse_positive_int(env, "LOG_MAX_BYTES", 5 * 1024 * 1024),
            log_backup_count=_parse_positive_int(env, "LOG_BACKUP_COUNT", 3),
            supported_languages=SUPPORTED_LANGUAGES,
        )


__all__ = [
    "DEFAULT_MODEL_PATH",
    "PROJECT_ROOT",
    "SUPPORTED_LANGUAGES",
    "Settings",
]

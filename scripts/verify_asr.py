"""Command-line smoke test for local ASR without starting the web server.

Example:
    python scripts/verify_asr.py samples/chinese.wav --language zh
    python scripts/verify_asr.py samples/english.wav --language en

The script uses ASR_MODEL_PATH (or --model-path) and never downloads weights.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings
from app.errors import ApiError
from app.services.audio import decode_audio, validate_language
from app.services.transcriber import Transcriber, WhisperTranscriber


@dataclass(frozen=True, slots=True)
class VerificationOutput:
    text: str
    language: str
    duration_seconds: float
    processing_seconds: float


def run_verification(
    audio_path: Path,
    language: str,
    settings: Settings,
    *,
    transcriber: Transcriber | None = None,
) -> VerificationOutput:
    """Decode one file and transcribe it with a local model (or injected fake)."""

    if not audio_path.is_file():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    normalized_language = validate_language(
        language, settings.supported_languages
    )
    started = time.perf_counter()
    audio = decode_audio(audio_path, settings)
    engine = transcriber or WhisperTranscriber(settings)
    result = engine.transcribe(audio.samples, normalized_language)
    elapsed = time.perf_counter() - started

    return VerificationOutput(
        text=result.text,
        language=normalized_language,
        duration_seconds=audio.duration_seconds,
        processing_seconds=elapsed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify local faster-whisper transcription on one audio file."
    )
    parser.add_argument("audio", type=Path, help="Path to a WAV/WebM/OGG audio file")
    parser.add_argument(
        "--language",
        choices=("zh", "en"),
        default="zh",
        help="Recognition language (default: zh)",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Override ASR_MODEL_PATH (local model directory)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    if args.model_path is not None:
        settings = replace(
            settings,
            asr_model_path=args.model_path.expanduser().resolve(),
        )

    try:
        output = run_verification(args.audio, args.language, settings)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ApiError as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        if exc.code == "model_unavailable":
            print(
                "提示：先运行 python scripts/download_model.py --model small，"
                "或通过 --model-path 指定本地模型目录。",
                file=sys.stderr,
            )
        return 1

    print(f"text: {output.text}")
    print(f"language: {output.language}")
    print(f"duration_seconds: {output.duration_seconds:.3f}")
    print(f"processing_seconds: {output.processing_seconds:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

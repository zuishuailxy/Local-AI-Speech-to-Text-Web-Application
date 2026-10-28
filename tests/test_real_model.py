"""Opt-in integration tests against the real local faster-whisper model.

Run with ``python -m pytest -q -m real_model tests/test_real_model.py``.
These tests require ``models/faster-whisper-small`` (or ``ASR_MODEL_PATH``)
and are excluded from the default test run.
"""

from __future__ import annotations

import time

import pytest

from app.config import Settings
from app.services.audio import decode_audio
from app.services.metrics import cer, cjk_ratio, latin_ratio, wer
from app.services.transcriber import WhisperTranscriber
from tests.real_model_support import require_model
from tests.sample_data import SAMPLE_CASES, SAMPLE_DIR

pytestmark = pytest.mark.real_model

CER_THRESHOLD = 0.30
WER_THRESHOLD = 0.30
SCRIPT_RATIO_MINIMUM = 0.80


@pytest.fixture(scope="module")
def engine() -> tuple[Settings, WhisperTranscriber, float]:
    settings = Settings.from_env()
    require_model(settings)

    transcriber = WhisperTranscriber(settings)
    started = time.perf_counter()
    transcriber.warmup()
    load_seconds = time.perf_counter() - started
    print(f"\nmodel_load_seconds={load_seconds:.3f}")
    return settings, transcriber, load_seconds


@pytest.mark.parametrize(
    "case",
    SAMPLE_CASES,
    ids=[str(case["language"]) for case in SAMPLE_CASES],
)
def test_real_model_transcribes_sample(
    engine: tuple[Settings, WhisperTranscriber, float],
    case: dict[str, object],
) -> None:
    settings, transcriber, load_seconds = engine
    language = str(case["language"])
    reference = str(case["reference"])
    audio_path = SAMPLE_DIR / str(case["name"])

    assert audio_path.is_file(), f"missing sample: {audio_path}"

    audio = decode_audio(audio_path, settings)
    assert audio.duration_seconds == pytest.approx(
        float(case["duration_seconds"]), abs=0.05
    )

    started = time.perf_counter()
    result = transcriber.transcribe(audio.samples, language)
    inference_seconds = time.perf_counter() - started
    text = result.text.strip()
    rtf = inference_seconds / audio.duration_seconds

    print(f"\n[{language}] model_text: {text}")
    print(f"[{language}] reference:  {reference}")
    print(f"[{language}] duration_seconds={audio.duration_seconds:.3f}")
    print(f"[{language}] model_load_seconds={load_seconds:.3f}")
    print(f"[{language}] inference_seconds={inference_seconds:.3f}")
    print(f"[{language}] rtf={rtf:.4f}")

    assert result.language == language
    assert text, "模型返回空文本"

    if language == "zh":
        score = cer(reference, text)
        print(f"[zh] CER={score:.4f} (threshold {CER_THRESHOLD:.2f})")
        assert cjk_ratio(text) >= SCRIPT_RATIO_MINIMUM, (
            f"中文输出中汉字占比过低: {cjk_ratio(text):.2f}"
        )
        assert score <= CER_THRESHOLD, f"中文 CER {score:.4f} 超过阈值"
    else:
        score = wer(reference, text)
        print(f"[en] WER={score:.4f} (threshold {WER_THRESHOLD:.2f})")
        assert latin_ratio(text) >= SCRIPT_RATIO_MINIMUM, (
            f"英文输出中拉丁字母占比过低: {latin_ratio(text):.2f}"
        )
        assert score <= WER_THRESHOLD, f"英文 WER {score:.4f} 超过阈值"

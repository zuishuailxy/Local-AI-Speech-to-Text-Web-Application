from __future__ import annotations

import wave
from pathlib import Path

import pytest

from tests.sample_data import SAMPLE_CASES, SAMPLE_DIR


@pytest.mark.parametrize(
    "case",
    SAMPLE_CASES,
    ids=[str(case["name"]) for case in SAMPLE_CASES],
)
def test_sample_wav_is_16khz_mono_pcm16(case: dict[str, object]) -> None:
    path = SAMPLE_DIR / str(case["name"])
    assert path.is_file(), f"missing sample: {path}"

    with wave.open(str(path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16_000
        duration = wav_file.getnframes() / wav_file.getframerate()

    assert duration == pytest.approx(float(case["duration_seconds"]), abs=0.05)
    assert 5.0 <= duration <= 15.0


def test_reference_file_covers_both_samples() -> None:
    reference_file = SAMPLE_DIR / "reference.txt"
    assert reference_file.is_file()

    text = " ".join(reference_file.read_text(encoding="utf-8").split())
    compact = "".join(text.split())
    assert "本人录制" in text
    assert "reference:" in text
    for case in SAMPLE_CASES:
        assert "".join(str(case["reference"]).split()) in compact
        assert f"samples/{case['name']}" in text


def test_no_model_weights_inside_samples() -> None:
    unexpected = [
        path.name
        for path in SAMPLE_DIR.rglob("*")
        if path.is_file() and path.suffix in {".bin", ".pt", ".onnx"}
    ]
    assert unexpected == []


def test_sample_paths_are_repo_relative() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    assert SAMPLE_DIR == repo_root / "samples"

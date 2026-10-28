"""Shared metadata for the committed test samples."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "samples"

SAMPLE_CASES: tuple[dict[str, object], ...] = (
    {
        "name": "chinese.wav",
        "language": "zh",
        "duration_seconds": 12.0,
        "reference": (
            "轻轻的我走了，正如我轻轻的来；我轻轻的招手，作别西天的云彩。"
            "那河畔的金柳，是夕阳中的新娘。"
        ),
    },
    {
        "name": "english.wav",
        "language": "en",
        "duration_seconds": 9.0,
        "reference": (
            "Never give up. Never lose hope. Always have faith. "
            "It allows you to cope."
        ),
    },
)

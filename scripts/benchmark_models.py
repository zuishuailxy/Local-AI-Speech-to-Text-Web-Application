"""Compare faster-whisper model sizes on the bundled samples.

Example:
    python scripts/benchmark_models.py --models small medium
    python scripts/benchmark_models.py --models medium --json /tmp/medium.json

The script never downloads weights.  Each model must already exist at
``models/faster-whisper-<size>`` or be passed explicitly.  It reports CER/WER,
warm inference latency, short-window latency (for realtime feasibility), and
peak RSS.
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faster_whisper import WhisperModel

from app.config import Settings
from app.services.audio import decode_audio
from app.services.metrics import cer, wer
from app.services.text import to_simplified

SAMPLE_DIR = PROJECT_ROOT / "samples"
REFERENCES = {
    "zh": (
        "chinese.wav",
        "轻轻的我走了，正如我轻轻的来；我轻轻的招手，作别西天的云彩。"
        "那河畔的金柳，是夕阳中的新娘。",
        cer,
    ),
    "en": (
        "english.wav",
        "Never give up. Never lose hope. Always have faith. It allows you to cope.",
        wer,
    ),
}


@dataclass(frozen=True, slots=True)
class CaseResult:
    language: str
    seconds: list[float]
    metric: float
    text: str


def load_samples(settings: Settings) -> dict[str, Any]:
    return {
        language: decode_audio(SAMPLE_DIR / filename, settings).samples
        for language, (filename, _, _) in REFERENCES.items()
    }


def transcribe(
    model: WhisperModel,
    samples: Any,
    language: str,
    runs: int,
) -> CaseResult:
    times: list[float] = []
    text = ""
    for _ in range(runs):
        started = time.perf_counter()
        segments, _ = model.transcribe(
            samples,
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        text = to_simplified("".join(segment.text for segment in segments).strip())
        times.append(round(time.perf_counter() - started, 3))
    _, _, metric = REFERENCES[language]
    return CaseResult(language, times, round(metric(REFERENCES[language][1], text), 4), text)


def benchmark(model_size: str, runs: int, model_path: Path | None) -> dict[str, Any]:
    path = model_path or PROJECT_ROOT / "models" / f"faster-whisper-{model_size}"
    if not path.is_dir():
        raise SystemExit(
            f"模型目录不存在: {path}\n"
            f"先运行: python scripts/download_model.py --model {model_size}"
        )

    settings = Settings.from_env(
        environ={"ASR_MODEL_PATH": str(path)},
        project_root=PROJECT_ROOT,
    )
    samples = load_samples(settings)

    started = time.perf_counter()
    model = WhisperModel(
        str(path),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
    )
    load_seconds = round(time.perf_counter() - started, 3)

    # Warm up decoder/kernels before measuring.
    model.transcribe(
        samples["zh"][:16_000],
        language="zh",
        beam_size=5,
        vad_filter=True,
    )

    results = {
        language: transcribe(model, samples[language], language, runs)
        for language in ("zh", "en")
    }

    short_windows = {}
    for seconds in (3.0, 6.0):
        window = samples["zh"][: int(seconds * 16_000)]
        short_windows[f"{seconds:g}s"] = transcribe(model, window, "zh", 1)

    return {
        "model": path.name,
        "load_seconds": load_seconds,
        "zh": asdict(results["zh"]),
        "en": asdict(results["en"]),
        "zh_windows": {
            key: {"seconds": value.seconds[0], "text": value.text}
            for key, value in short_windows.items()
        },
        "max_rss_mb": round(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 1
        ),
    }


def print_report(report: dict[str, Any]) -> None:
    print(f"model={report['model']} load={report['load_seconds']:.2f}s "
          f"rss={report['max_rss_mb']:.0f}MB")
    for language in ("zh", "en"):
        item = report[language]
        label = "CER" if language == "zh" else "WER"
        print(
            f"  {language}: {label}={item['metric']:.4f} "
            f"seconds={item['seconds']}"
        )
        print(f"      {item['text']}")
    for name, item in report["zh_windows"].items():
        print(f"  window {name}: {item['seconds']:.3f}s :: {item['text']}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        default=["small", "medium"],
        help="model sizes under models/faster-whisper-<size>",
    )
    parser.add_argument("--runs", type=int, default=2, help="measured runs per language")
    parser.add_argument("--json", type=Path, help="also write raw results to this path")
    args = parser.parse_args(argv)

    reports = [benchmark(size, max(1, args.runs), None) for size in args.models]
    for report in reports:
        print_report(report)
        print()
    if args.json:
        args.json.write_text(
            json.dumps(reports, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

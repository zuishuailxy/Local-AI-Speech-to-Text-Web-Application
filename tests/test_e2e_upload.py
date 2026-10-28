"""Opt-in end-to-end upload tests through the real FastAPI app and local model.

Run with ``python -m pytest -q -m real_model tests/test_e2e_upload.py``.
The default suite excludes these tests; no model is loaded there.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.metrics import cer, cjk_ratio, latin_ratio, wer
from app.services.transcriber import WhisperTranscriber
from tests.real_model_support import require_model
from tests.sample_data import SAMPLE_CASES, SAMPLE_DIR

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEECH_WEBM = PROJECT_ROOT / "tests" / "fixtures" / "speech-en.webm"

pytestmark = pytest.mark.real_model

CER_THRESHOLD = 0.30
WER_THRESHOLD = 0.30
SCRIPT_RATIO_MINIMUM = 0.80


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    settings = Settings.from_env()
    require_model(settings)
    transcriber = WhisperTranscriber(settings)
    with TestClient(
        create_app(transcriber=transcriber, settings=settings)
    ) as test_client:
        yield test_client


def _post_audio(
    client: TestClient,
    path: Path,
    language: str,
    content_type: str,
):
    started = time.perf_counter()
    response = client.post(
        "/api/transcribe",
        data={"language": language},
        files={"file": (path.name, path.read_bytes(), content_type)},
    )
    elapsed = time.perf_counter() - started
    return response, elapsed


@pytest.mark.parametrize(
    "case",
    SAMPLE_CASES,
    ids=[str(case["language"]) for case in SAMPLE_CASES],
)
def test_upload_sample_end_to_end(
    client: TestClient,
    case: dict[str, object],
) -> None:
    language = str(case["language"])
    reference = str(case["reference"])
    path = SAMPLE_DIR / str(case["name"])

    response, elapsed = _post_audio(client, path, language, "audio/wav")

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {
        "text",
        "language",
        "duration_seconds",
        "processing_seconds",
    }
    assert body["language"] == language
    assert body["text"].strip()
    assert body["duration_seconds"] == pytest.approx(
        float(case["duration_seconds"]), abs=0.05
    )
    assert body["processing_seconds"] > 0
    assert body["processing_seconds"] <= elapsed + 0.05

    print(f"\n[{language}] upload={path.name}")
    print(f"[{language}] text: {body['text']}")
    print(f"[{language}] duration_seconds={body['duration_seconds']}")
    print(f"[{language}] processing_seconds={body['processing_seconds']}")
    print(f"[{language}] client_elapsed={elapsed:.3f}")

    if language == "zh":
        score = cer(reference, body["text"])
        print(f"[zh] CER={score:.4f}")
        assert cjk_ratio(body["text"]) >= SCRIPT_RATIO_MINIMUM
        assert score <= CER_THRESHOLD
    else:
        score = wer(reference, body["text"])
        print(f"[en] WER={score:.4f}")
        assert latin_ratio(body["text"]) >= SCRIPT_RATIO_MINIMUM
        assert score <= WER_THRESHOLD


def test_upload_speech_webm_end_to_end(client: TestClient) -> None:
    reference = str(SAMPLE_CASES[1]["reference"])

    response, elapsed = _post_audio(client, SPEECH_WEBM, "en", "audio/webm")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["language"] == "en"
    assert body["text"].strip(), "WebM 语音样本返回空文本"
    assert body["duration_seconds"] == pytest.approx(9.0, abs=0.1)
    assert body["processing_seconds"] > 0
    assert body["processing_seconds"] <= elapsed + 0.05

    score = wer(reference, body["text"])
    print(f"\n[webm] upload={SPEECH_WEBM.name}")
    print(f"[webm] text: {body['text']}")
    print(f"[webm] duration_seconds={body['duration_seconds']}")
    print(f"[webm] processing_seconds={body['processing_seconds']}")
    print(f"[webm] WER={score:.4f}")

    assert latin_ratio(body["text"]) >= SCRIPT_RATIO_MINIMUM
    assert score <= WER_THRESHOLD

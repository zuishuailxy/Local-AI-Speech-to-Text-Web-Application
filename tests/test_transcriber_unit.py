from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from app.config import Settings
from app.errors import ModelUnavailableError, TranscriptionFailedError
from app.services.transcriber import WhisperTranscriber


class FakeWhisperModel:
    def __init__(self, text_parts: tuple[str, ...] = ("你", "好")) -> None:
        self.text_parts = text_parts
        self.calls: list[tuple[np.ndarray, dict[str, Any]]] = []

    def transcribe(self, samples: np.ndarray, **kwargs: Any):
        self.calls.append((samples, kwargs))
        return (
            iter([SimpleNamespace(text=part) for part in self.text_parts]),
            SimpleNamespace(language=kwargs.get("language")),
        )


def make_settings(tmp_path, *, model_exists: bool = True) -> Settings:
    settings = Settings.from_env(environ={}, project_root=tmp_path)
    if model_exists:
        settings.asr_model_path.mkdir(parents=True)
    return settings


def make_factory(model: FakeWhisperModel):
    calls: list[tuple[str, dict[str, Any]]] = []
    lock = threading.Lock()

    def factory(path: str, **kwargs: Any) -> FakeWhisperModel:
        with lock:
            calls.append((path, kwargs))
        # Simulate a slow model load so concurrent callers would expose races.
        time.sleep(0.02)
        return model

    return factory, calls


def test_model_is_lazy_and_factory_gets_local_config(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    factory, factory_calls = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)

    assert engine.is_loaded is False
    assert factory_calls == []

    samples = np.zeros(16_000, dtype=np.float32)
    result = engine.transcribe(samples, "zh")

    assert result.text == "你好"
    assert result.language == "zh"
    assert engine.is_loaded is True
    assert len(factory_calls) == 1
    path, kwargs = factory_calls[0]
    assert path == str(settings.asr_model_path)
    assert kwargs == {
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": 4,
    }

    assert len(model.calls) == 1
    called_samples, transcribe_kwargs = model.calls[0]
    assert called_samples is samples
    assert transcribe_kwargs["language"] == "zh"
    assert transcribe_kwargs["beam_size"] == 5
    assert transcribe_kwargs["vad_filter"] is True


def test_model_is_reused_across_requests(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    factory, factory_calls = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)
    samples = np.zeros(16_000, dtype=np.float32)

    assert engine.transcribe(samples, "zh").text == "你好"
    assert engine.transcribe(samples, "en").text == "你好"

    assert len(factory_calls) == 1
    assert len(model.calls) == 2


def test_missing_model_returns_model_unavailable(tmp_path) -> None:
    settings = make_settings(tmp_path, model_exists=False)
    model = FakeWhisperModel()
    factory, factory_calls = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)

    with pytest.raises(ModelUnavailableError) as exc_info:
        engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert exc_info.value.code == "model_unavailable"
    assert factory_calls == []
    assert engine.is_loaded is False


def test_model_load_failure_is_model_unavailable(tmp_path) -> None:
    settings = make_settings(tmp_path)

    def failing_factory(path: str, **kwargs: Any) -> Any:
        raise RuntimeError(f"cannot load {path}")

    engine = WhisperTranscriber(settings, model_factory=failing_factory)

    with pytest.raises(ModelUnavailableError) as exc_info:
        engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert exc_info.value.code == "model_unavailable"
    assert engine.is_loaded is False


def test_inference_failure_is_transcription_failed(tmp_path) -> None:
    settings = make_settings(tmp_path)

    class FailingModel:
        def transcribe(self, samples: np.ndarray, **kwargs: Any):
            raise RuntimeError("inference exploded")

    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: FailingModel(),
    )

    with pytest.raises(TranscriptionFailedError) as exc_info:
        engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert exc_info.value.code == "transcription_failed"
    assert engine.is_loaded is True


def test_empty_text_is_preserved(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=())
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert result.text == ""


def test_concurrent_first_requests_load_model_once(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    factory, factory_calls = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)
    samples = np.zeros(16_000, dtype=np.float32)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(lambda _: engine.transcribe(samples, "zh"), range(4))
        )

    assert [result.text for result in results] == ["你好"] * 4
    assert len(factory_calls) == 1
    assert len(model.calls) == 4


def test_warmup_loads_without_inference(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    factory, factory_calls = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)

    engine.warmup()

    assert engine.is_loaded is True
    assert len(factory_calls) == 1
    assert model.calls == []

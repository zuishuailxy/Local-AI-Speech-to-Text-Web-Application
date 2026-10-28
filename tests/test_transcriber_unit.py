from __future__ import annotations

import logging
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
    def __init__(
        self,
        text_parts: tuple[str, ...] = ("你", "好"),
        detected_language: str | None = None,
        language_probability: float = 1.0,
    ) -> None:
        self.text_parts = text_parts
        self.detected_language = detected_language
        self.language_probability = language_probability
        self.calls: list[tuple[np.ndarray, dict[str, Any]]] = []

    def transcribe(self, samples: np.ndarray, **kwargs: Any):
        self.calls.append((samples, kwargs))
        return (
            iter([SimpleNamespace(text=part) for part in self.text_parts]),
            SimpleNamespace(
                language=kwargs.get("language") or self.detected_language,
                language_probability=self.language_probability,
            ),
        )


def make_settings(tmp_path, *, model_exists: bool = True, **env: str) -> Settings:
    settings = Settings.from_env(environ=env, project_root=tmp_path)
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


def test_model_load_logs_seconds(tmp_path, caplog) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    factory, _ = make_factory(model)
    engine = WhisperTranscriber(settings, model_factory=factory)

    with caplog.at_level(logging.INFO, logger="app.services.transcriber"):
        engine.warmup()

    assert "model_load_seconds=" in caplog.text


def test_inference_logs_language_and_inference_time(tmp_path, caplog) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=("你好",))
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    with caplog.at_level(logging.INFO, logger="app.services.transcriber"):
        engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert "requested_language=zh" in caplog.text
    assert "detected_language=zh" in caplog.text
    assert "output_language=zh" in caplog.text
    assert "inference_seconds=" in caplog.text
    assert "text_chars=2" in caplog.text


def test_language_script_mismatch_is_warned_without_changing_result(
    tmp_path, caplog
) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=("hello", " world"))
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    with caplog.at_level(logging.INFO, logger="app.services.transcriber"):
        result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert result.language == "zh"
    assert result.text == "hello world"
    assert "asr_language_mismatch" in caplog.text
    assert "requested_language=zh" in caplog.text
    assert "output_language=en" in caplog.text


def test_chinese_output_is_normalized_to_simplified(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=("今天天氣很好", "，我們開始測試。"))
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "zh")

    assert result.text == "今天天气很好，我们开始测试。"


def test_english_output_is_not_simplified(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=("今天天氣",))
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "en")

    assert result.text == "今天天氣"


def test_auto_language_uses_detected_language_and_no_forced_token(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(text_parts=("hello",), detected_language="en")
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "auto")

    assert result.language == "en"
    assert result.text == "hello"
    assert model.calls[0][1]["language"] is None


def test_auto_low_confidence_falls_back_to_script(tmp_path, caplog) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel(
        text_parts=("你好",),
        detected_language="en",
        language_probability=0.2,
    )
    engine = WhisperTranscriber(
        settings,
        model_factory=lambda path, **kwargs: model,
    )

    with caplog.at_level(logging.WARNING, logger="app.services.transcriber"):
        result = engine.transcribe(np.zeros(16_000, dtype=np.float32), "auto")

    assert result.language == "zh"
    assert result.text == "你好"
    assert "asr_auto_low_confidence" in caplog.text
    assert "fallback_language=zh" in caplog.text


PROMPT = "以下是普通话语音识别测试，包含：语音识别、实时语音识别、本地语音识别。"


def test_prompt_is_sent_only_for_long_explicit_chinese(tmp_path) -> None:
    settings = make_settings(tmp_path, ASR_INITIAL_PROMPT=PROMPT)
    model = FakeWhisperModel()
    engine = WhisperTranscriber(settings, model_factory=lambda *a, **k: model)

    engine.transcribe(np.zeros(5 * 16_000, dtype=np.float32), "zh")
    engine.transcribe(np.zeros(2 * 16_000, dtype=np.float32), "zh")
    engine.transcribe(np.zeros(5 * 16_000, dtype=np.float32), "en")
    engine.transcribe(np.zeros(5 * 16_000, dtype=np.float32), "auto")

    prompts = [kwargs.get("initial_prompt") for _, kwargs in model.calls]
    assert prompts == [PROMPT, None, None, None]


def test_prompt_text_is_not_logged(tmp_path, caplog) -> None:
    settings = make_settings(tmp_path, ASR_INITIAL_PROMPT=PROMPT)
    model = FakeWhisperModel()
    engine = WhisperTranscriber(settings, model_factory=lambda *a, **k: model)

    with caplog.at_level(logging.INFO, logger="app.services.transcriber"):
        engine.transcribe(np.zeros(5 * 16_000, dtype=np.float32), "zh")

    assert "initial_prompt=on" in caplog.text
    assert "本地语音识别" not in caplog.text


def test_use_prompt_false_disables_prompt(tmp_path) -> None:
    settings = make_settings(tmp_path, ASR_INITIAL_PROMPT=PROMPT)
    model = FakeWhisperModel()
    engine = WhisperTranscriber(settings, model_factory=lambda *a, **k: model)

    engine.transcribe(np.zeros(5 * 16_000, dtype=np.float32), "zh", use_prompt=False)

    assert "initial_prompt" not in model.calls[0][1]


def test_beam_size_override_is_forwarded(tmp_path) -> None:
    settings = make_settings(tmp_path)
    model = FakeWhisperModel()
    engine = WhisperTranscriber(settings, model_factory=lambda *a, **k: model)

    engine.transcribe(np.zeros(2 * 16_000, dtype=np.float32), "zh")
    engine.transcribe(np.zeros(2 * 16_000, dtype=np.float32), "zh", beam_size=1)

    assert model.calls[0][1]["beam_size"] == 5
    assert model.calls[1][1]["beam_size"] == 1

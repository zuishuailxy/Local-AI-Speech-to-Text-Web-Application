"""Opt-in Playwright browser end-to-end tests.

Run with:
    PLAYWRIGHT_CHANNEL=chrome .venv/bin/python -m pytest -q -m e2e

The tests start a real uvicorn server with ``FakeTranscriber`` so they do not
need model weights.  The microphone is Chromium's fake device, not a real mic.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from pathlib import Path
from typing import Any, Iterator

import pytest
import uvicorn

from app.config import PROJECT_ROOT, Settings
from app.main import create_app
from app.services.transcriber import FakeTranscriber

pytestmark = pytest.mark.e2e

SAMPLE_WAV = PROJECT_ROOT / "samples" / "english.wav"
E2E_TEXT = "E2E browser transcription result."
SCREENSHOT_DIR = os.environ.get("E2E_SCREENSHOT_DIR")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    port = _free_port()
    settings = Settings.from_env(
        environ={"LOG_LEVEL": "WARNING"},
        project_root=PROJECT_ROOT,
    )
    app = create_app(
        transcriber=FakeTranscriber(text=E2E_TEXT),
        settings=settings,
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        pytest.fail("uvicorn did not start for browser E2E")

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser() -> Iterator[Any]:
    sync_api = pytest.importorskip("playwright.sync_api")
    channel = os.environ.get("PLAYWRIGHT_CHANNEL", "").strip() or None
    launch_kwargs: dict[str, object] = {
        "headless": True,
        "args": [
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            f"--use-file-for-fake-audio-capture={SAMPLE_WAV}",
            "--autoplay-policy=no-user-gesture-required",
        ],
    }
    if channel:
        launch_kwargs["channel"] = channel

    with sync_api.sync_playwright() as playwright:
        try:
            launched = playwright.chromium.launch(**launch_kwargs)
        except sync_api.Error as exc:
            pytest.skip(
                "Playwright Chromium 未安装："
                "python -m playwright install chromium；"
                f"或设置 PLAYWRIGHT_CHANNEL=chrome。原始错误: {exc}"
            )
        try:
            yield launched
        finally:
            launched.close()


@pytest.fixture
def page(browser: Any, base_url: str) -> Iterator[Any]:
    context = browser.new_context(permissions=["microphone"])
    page = context.new_page()
    page.set_default_timeout(15_000)
    try:
        yield page
    finally:
        context.close()


def _wait_phase(page: Any, phase: str, timeout: int = 20_000) -> None:
    page.wait_for_function(
        "(expected) => window.recordingApp.getState().phase === expected",
        arg=phase,
        timeout=timeout,
    )


def _screenshot(page: Any, name: str) -> None:
    if SCREENSHOT_DIR:
        directory = Path(SCREENSHOT_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / name), full_page=True)


def _console_errors(page: Any) -> list[str]:
    errors: list[str] = []

    def record_console(message) -> None:
        if message.type == "error":
            url = (message.location or {}).get("url", "")
            errors.append(f"{message.text} [{url}]")

    page.on("console", record_console)
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def test_page_loads_with_expected_contract(page: Any, base_url: str) -> None:
    errors = _console_errors(page)

    page.goto(base_url)
    page.wait_for_load_state("networkidle")

    assert page.title() == "Local AI Speech-to-Text"
    assert page.locator("#app").get_attribute("data-state") == "idle"
    assert page.locator("#start-button").is_enabled()
    assert page.locator("#upload-button").is_disabled()
    assert page.locator("#language-select").input_value() == "zh"
    assert page.locator("#status-text").inner_text().strip()

    assert errors == []


def test_upload_wav_through_browser(page: Any, base_url: str) -> None:
    page.goto(base_url)
    page.select_option("#language-select", "en")
    page.set_input_files("#file-input", str(SAMPLE_WAV))

    assert "english.wav" in page.locator("#file-name").inner_text()
    assert page.locator("#upload-button").is_enabled()

    page.click("#upload-button")
    _wait_phase(page, "success")

    assert page.locator("#result-text").inner_text() == E2E_TEXT
    assert "English" in page.locator("#result-language").inner_text()
    assert "9.0" in page.locator("#result-duration").inner_text()
    assert page.locator("#copy-button").is_enabled()
    assert page.locator("#audio-preview").is_visible()
    assert page.locator("#audio-preview").get_attribute("src")

    _screenshot(page, "t5.4-e2e-upload.png")


def test_fake_microphone_recording(page: Any, base_url: str) -> None:
    page.goto(base_url)
    page.select_option("#language-select", "en")

    page.click("#start-button")
    _wait_phase(page, "recording")
    assert page.locator("#stop-button").is_enabled()

    page.wait_for_function(
        "() => window.recordingApp.getState().recordedMs >= 1200",
        timeout=10_000,
    )
    page.click("#stop-button")
    _wait_phase(page, "success")

    recording = page.evaluate("window.recordingApp.getState().lastRecording")
    assert recording is not None
    assert recording["mimeType"].startswith("audio/webm")
    assert recording["size"] > 1000
    assert recording["durationMs"] >= 1000
    assert page.locator("#result-text").inner_text() == E2E_TEXT
    assert "English" in page.locator("#result-language").inner_text()
    assert page.locator("#start-button").is_enabled()

    _screenshot(page, "t5.4-e2e-microphone.png")

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = {"tag": tag}
        element.update({key: value or "" for key, value in attrs})
        self.elements.append(element)


def parse_html() -> Collector:
    collector = Collector()
    collector.feed(HTML)
    return collector


def test_buttons_have_explicit_types_and_text() -> None:
    elements = parse_html().elements
    buttons = [element for element in elements if element["tag"] == "button"]

    assert buttons
    for button in buttons:
        assert button.get("type") == "button"
        assert button.get("id") or button.get("aria-label")


def test_form_controls_have_labels() -> None:
    page = parse_html().elements
    labels = {element.get("for") for element in page if element["tag"] == "label"}

    assert "language-select" in labels
    assert "file-input" in labels
    assert any(element.get("id") == "language-select" for element in page)
    assert any(element.get("id") == "file-input" for element in page)


def test_live_regions_and_alert_are_present() -> None:
    page = parse_html().elements
    live = [element for element in page if element.get("aria-live")]
    error = next(element for element in page if element.get("id") == "error-panel")

    assert len(live) >= 2
    assert error.get("role") == "alert"


def test_audio_preview_is_labelled() -> None:
    page = parse_html().elements
    audio = next(element for element in page if element.get("id") == "audio-preview")

    assert audio.get("controls") is not None
    assert audio.get("aria-label")


def test_microphone_is_requested_only_inside_start_handler() -> None:
    start = JS.index("async function startRecording")
    call = JS.index("await navigator.mediaDevices.getUserMedia")

    assert start < call
    assert JS.count("await navigator.mediaDevices.getUserMedia") == 1

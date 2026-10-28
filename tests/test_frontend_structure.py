from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "static" / "index.html"
CSS = ROOT / "static" / "styles.css"


class ElementCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: dict[str, dict[str, str]] = {}
        self.tags: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        attributes = {key: value or "" for key, value in attrs}
        element_id = attributes.get("id")
        if element_id:
            self.ids[element_id] = {"tag": tag, **attributes}

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(data.strip())


def parse_index() -> ElementCollector:
    collector = ElementCollector()
    collector.feed(INDEX.read_text(encoding="utf-8"))
    return collector


def test_required_page_contract_elements_exist() -> None:
    page = parse_index()

    expected = {
        "language-select",
        "start-button",
        "stop-button",
        "recording-timer",
        "processing-timer",
        "file-input",
        "upload-button",
        "file-name",
        "status-badge",
        "status-text",
        "pipeline-state",
        "result-panel",
        "result-language",
        "result-duration",
        "result-processing",
        "result-text",
        "copy-button",
        "error-panel",
        "error-message",
        "retry-button",
        "dismiss-error-button",
        "audio-preview",
    }

    assert expected <= set(page.ids)


def test_initial_control_states_and_labels() -> None:
    page = parse_index()

    assert page.ids["stop-button"].get("disabled") is not None
    assert page.ids["copy-button"].get("disabled") is not None
    assert page.ids["upload-button"].get("disabled") is not None
    assert page.ids["start-button"].get("type") == "button"

    assert page.ids["language-select"]["tag"] == "select"
    assert page.ids["file-input"]["tag"] == "input"
    assert page.ids["file-input"]["accept"].startswith(".wav")
    assert page.ids["result-text"].get("hidden") is not None
    assert page.ids["error-panel"].get("hidden") is not None
    assert page.ids["result-panel"]["data-result-state"] == "empty"
    assert page.ids["app"]["data-state"] == "idle"


def test_accessibility_hooks() -> None:
    page = parse_index()

    assert page.ids["error-panel"]["role"] == "alert"
    assert page.ids["status-badge"].get("class")
    assert page.ids["language-label"]["for"] == "language-select"
    assert page.ids["file-picker"]["for"] == "file-input"
    assert page.ids["result-text"].get("aria-live") == "polite"


def test_no_external_assets() -> None:
    html = INDEX.read_text(encoding="utf-8")

    assert "http://" not in html
    assert "https://" not in html
    assert "/static/styles.css" in html
    assert "/static/app.js" in html
    assert "/static/favicon.svg" in html
    assert 'src="http' not in html
    assert 'href="http' not in html


def test_static_assets_are_served() -> None:
    client = TestClient(app)

    page_response = client.get("/")
    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")
    icon_response = client.get("/static/favicon.svg")
    worklet_response = client.get("/static/pcm-worklet.js")

    assert page_response.status_code == 200
    assert "Local AI Speech-to-Text" in page_response.text
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "[data-state=\"recording\"]" in css_response.text
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert icon_response.status_code == 200
    assert "image/svg+xml" in icon_response.headers["content-type"]
    assert worklet_response.status_code == 200
    assert "javascript" in worklet_response.headers["content-type"]

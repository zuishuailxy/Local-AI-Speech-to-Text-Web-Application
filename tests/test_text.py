from __future__ import annotations

from app.services.text import to_simplified


def test_traditional_chinese_is_converted() -> None:
    assert (
        to_simplified("今天天氣很好,我們開始測試本地與陰時別系統。")
        == "今天天气很好,我们开始测试本地与阴时别系统。"
    )


def test_simplified_chinese_is_unchanged() -> None:
    text = "轻轻的我走了，正如我轻轻的来。"

    assert to_simplified(text) == text


def test_english_is_unchanged() -> None:
    text = "Never give up. Never lose hope."

    assert to_simplified(text) == text


def test_empty_text_is_preserved() -> None:
    assert to_simplified("") == ""


def test_common_traditional_words_are_converted() -> None:
    assert to_simplified("軟體與網路") == "软件与网络"

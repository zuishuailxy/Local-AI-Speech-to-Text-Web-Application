from __future__ import annotations

import pytest

from app.config import SUPPORTED_LANGUAGES
from app.errors import InvalidLanguageError
from app.services.audio import validate_language


def test_supported_languages_are_zh_and_en() -> None:
    assert SUPPORTED_LANGUAGES == ("zh", "en")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("zh", "zh"),
        ("en", "en"),
        (" ZH ", "zh"),
        ("EN", "en"),
    ],
)
def test_language_normalization(raw: str, expected: str) -> None:
    assert validate_language(raw) == expected


@pytest.mark.parametrize("raw", ["fr", "zh-CN", "auto", "", "en-US"])
def test_unsupported_language_is_rejected(raw: str) -> None:
    with pytest.raises(InvalidLanguageError) as exc_info:
        validate_language(raw)

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "invalid_language"


def test_auto_is_accepted_only_when_explicitly_enabled() -> None:
    assert validate_language(" auto ", allow_auto=True) == "auto"

    with pytest.raises(InvalidLanguageError):
        validate_language("auto")

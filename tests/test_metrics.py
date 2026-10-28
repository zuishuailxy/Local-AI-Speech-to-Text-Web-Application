from __future__ import annotations

import pytest

from app.services.metrics import (
    cer,
    cjk_ratio,
    edit_distance,
    latin_ratio,
    normalize_for_cer,
    normalize_for_wer,
    wer,
)


def test_normalize_for_cer_drops_case_space_and_punctuation() -> None:
    assert normalize_for_cer("轻轻的我走了，正如我轻轻的来。") == (
        "轻轻的我走了正如我轻轻的来"
    )
    assert normalize_for_cer("Hello, World!") == "helloworld"


def test_cer_identical_text_is_zero() -> None:
    text = "Never give up. Never lose hope."

    assert cer(text, text) == 0.0
    assert wer(text, text) == 0.0


def test_cer_ignores_punctuation_and_whitespace() -> None:
    reference = "轻轻的我走了，正如我轻轻的来。"
    hypothesis = "轻轻的我走了 正如我轻轻的来"

    assert cer(reference, hypothesis) == 0.0
    assert wer(reference, hypothesis) == 0.0


def test_cer_counts_character_substitution() -> None:
    assert cer("金柳", "金牛") == pytest.approx(0.5)
    assert cer("作别", "做别") == pytest.approx(0.5)


def test_cer_counts_insertions_and_deletions() -> None:
    assert cer("abcd", "abcde") == pytest.approx(0.25)
    assert cer("abcd", "abd") == pytest.approx(0.25)


def test_wer_is_case_and_punctuation_insensitive() -> None:
    reference = "Never give up. Never lose hope."
    hypothesis = "never give up, never lose hope"

    assert normalize_for_wer(reference) == ["never", "give", "up", "never", "lose", "hope"]
    assert wer(reference, hypothesis) == 0.0


def test_wer_counts_word_substitution() -> None:
    assert wer("always have faith", "always have fate") == pytest.approx(1 / 3)


def test_empty_reference_handling() -> None:
    assert cer("", "") == 0.0
    assert cer("", "text") == 1.0
    assert wer("", "") == 0.0
    assert wer("", "text") == 1.0


def test_edit_distance_on_token_sequences() -> None:
    assert edit_distance([], []) == 0
    assert edit_distance([], ["a", "b"]) == 2
    assert edit_distance(["a", "b"], ["a", "c"]) == 1
    assert edit_distance(["a", "b"], ["a", "b", "c"]) == 1


def test_script_ratios() -> None:
    assert cjk_ratio("你好，世界。") == pytest.approx(1.0)
    assert cjk_ratio("  ") == 0.0
    assert latin_ratio("Hello, 世界!") == pytest.approx(5 / 7)
    assert latin_ratio("") == 0.0

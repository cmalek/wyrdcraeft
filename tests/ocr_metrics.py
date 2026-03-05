from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

THORN_CHARS = {"þ", "ð", "Þ", "Ð"}
MACRON_CHARS = {
    "ā",
    "ē",
    "ī",
    "ō",
    "ū",
    "ȳ",
    "ǣ",
    "Ā",
    "Ē",
    "Ī",
    "Ō",
    "Ū",
    "Ȳ",
    "Ǣ",
}
MAX_CONSECUTIVE_BLANK_LINES = 2


def preprocess_ocr_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]

    collapsed: list[str] = []
    consecutive_blank_lines = 0
    for line in lines:
        if line.strip():
            consecutive_blank_lines = 0
            collapsed.append(line)
            continue
        consecutive_blank_lines += 1
        if consecutive_blank_lines <= MAX_CONSECUTIVE_BLANK_LINES:
            collapsed.append("")

    return "\n".join(collapsed).strip() + "\n"


def _levenshtein_distance(expected: Sequence[str], observed: Sequence[str]) -> int:
    if not expected:
        return len(observed)
    if not observed:
        return len(expected)

    previous = list(range(len(observed) + 1))
    for index_expected, expected_item in enumerate(expected, start=1):
        current = [index_expected]
        for index_observed, observed_item in enumerate(observed, start=1):
            substitution = previous[index_observed - 1] + (
                0 if expected_item == observed_item else 1
            )
            insertion = current[index_observed - 1] + 1
            deletion = previous[index_observed] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1]


def _align_characters(
    expected: str, observed: str
) -> list[tuple[str | None, str | None]]:
    expected_chars = list(expected)
    observed_chars = list(observed)
    rows = len(expected_chars) + 1
    cols = len(observed_chars) + 1
    dp = [[0 for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if expected_chars[i - 1] == observed_chars[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    alignment: list[tuple[str | None, str | None]] = []
    i = rows - 1
    j = cols - 1
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            cost = 0 if expected_chars[i - 1] == observed_chars[j - 1] else 1
            if dp[i][j] == dp[i - 1][j - 1] + cost:
                alignment.append((expected_chars[i - 1], observed_chars[j - 1]))
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            alignment.append((expected_chars[i - 1], None))
            i -= 1
            continue
        alignment.append((None, observed_chars[j - 1]))
        j -= 1

    alignment.reverse()
    return alignment


def compute_ocr_metrics(
    expected_text: str, observed_text: str
) -> dict[str, float | int]:
    normalized_expected = preprocess_ocr_text(expected_text)
    normalized_observed = preprocess_ocr_text(observed_text)

    expected_chars = list(normalized_expected)
    observed_chars = list(normalized_observed)
    expected_words = normalized_expected.split()
    observed_words = normalized_observed.split()

    character_distance = _levenshtein_distance(expected_chars, observed_chars)
    word_distance = _levenshtein_distance(expected_words, observed_words)
    cer_denominator = max(len(expected_chars), 1)
    wer_denominator = max(len(expected_words), 1)

    alignment = _align_characters(normalized_expected, normalized_observed)
    thorn_expected = 0
    thorn_preserved = 0
    thorn_to_p = 0
    macron_expected = 0
    macron_preserved = 0
    for expected_char, observed_char in alignment:
        if expected_char in THORN_CHARS:
            thorn_expected += 1
            if observed_char in THORN_CHARS:
                thorn_preserved += 1
            if observed_char in {"p", "P"}:
                thorn_to_p += 1
        if expected_char in MACRON_CHARS:
            macron_expected += 1
            if observed_char == expected_char:
                macron_preserved += 1

    thorn_to_p_rate = 0.0 if thorn_expected == 0 else thorn_to_p / thorn_expected
    macron_recall = 1.0 if macron_expected == 0 else macron_preserved / macron_expected

    return {
        "cer": character_distance / cer_denominator,
        "wer": word_distance / wer_denominator,
        "thorn_expected": thorn_expected,
        "thorn_preserved": thorn_preserved,
        "thorn_to_p_rate": thorn_to_p_rate,
        "macron_expected": macron_expected,
        "macron_preserved": macron_preserved,
        "macron_recall": macron_recall,
        "char_distance": character_distance,
        "word_distance": word_distance,
        "expected_chars": len(expected_chars),
        "expected_words": len(expected_words),
    }

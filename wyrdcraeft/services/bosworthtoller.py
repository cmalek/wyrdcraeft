from __future__ import annotations

import re
import unicodedata
from typing import Final
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models.bosworth_toller import BTSearchEntry
from .markup import normalize_old_english

#: Bosworth-Toller site root.
BT_BASE_URL: Final[str] = "https://bosworthtoller.com"
#: Search endpoint path.
BT_SEARCH_PATH: Final[str] = "/search"
#: Search timeout in seconds.
BT_SEARCH_TIMEOUT_S: Final[float] = 8.0
#: Separator used between glosses in search summary rows.
BT_MEANING_SEPARATOR: Final[str] = "⬩"
#: Whitespace normalizer for scraped text.
WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
#: Acute-to-macron translation table for OE vowels.
ACUTE_TO_MACRON_TRANSLATION: Final[dict[int, str]] = str.maketrans(
    {
        "á": "ā",
        "é": "ē",
        "í": "ī",
        "ó": "ō",
        "ú": "ū",
        "ý": "ȳ",
        "ǽ": "ǣ",
        "Á": "Ā",
        "É": "Ē",
        "Í": "Ī",
        "Ó": "Ō",
        "Ú": "Ū",
        "Ý": "Ȳ",
        "Ǽ": "Ǣ",
    }
)


def normalize_bt_spelling(spelling: str) -> str:
    """
    Convert acute-marked vowels in BT spelling to macron equivalents.

    Args:
        spelling: Source spelling from BT search.

    Returns:
        Macronized spelling.

    """
    return unicodedata.normalize("NFC", spelling).translate(ACUTE_TO_MACRON_TRANSLATION)


def fetch_bt_search_entries(query: str) -> list[BTSearchEntry]:
    """
    Fetch and parse BT search result entries for one query term.

    Args:
        query: Search string for BT endpoint.

    Returns:
        Parsed search results from first page.

    """
    with httpx.Client(follow_redirects=True, timeout=BT_SEARCH_TIMEOUT_S) as client:
        response = client.get(
            f"{BT_BASE_URL}{BT_SEARCH_PATH}",
            params={"q": query},
        )
        response.raise_for_status()
    return parse_bt_search_entries(response.text)


def parse_bt_search_entries(html: str) -> list[BTSearchEntry]:
    """
    Parse Bosworth-Toller search HTML into structured entries.

    Args:
        html: Search response HTML.

    Returns:
        Parsed search entry list in page order.

    """
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article div.btd--search-entry")
    results: list[BTSearchEntry] = []
    for order_index, card in enumerate(cards):
        anchor = card.select_one("header h3 a")
        if anchor is None:
            continue
        headword_raw = _collapse_whitespace(anchor.get_text(" ", strip=True))
        if not headword_raw:
            continue

        href = _collapse_whitespace(anchor.get("href") or "")
        entry_url = urljoin(BT_BASE_URL, href) if href else BT_BASE_URL

        pos_node = card.select_one(".btd--search-entry-wordclass")
        pos = (
            _collapse_whitespace(pos_node.get_text(" ", strip=True))
            if pos_node
            else ""
        )
        if pos.startswith("(") and pos.endswith(")"):
            pos = pos[1:-1].strip()

        meanings_node = card.select_one(".btd--search-description p")
        meanings_text = (
            _collapse_whitespace(meanings_node.get_text(" ", strip=True))
            if meanings_node
            else ""
        )
        meanings = [
            part.strip()
            for part in meanings_text.split(BT_MEANING_SEPARATOR)
            if part.strip()
        ]

        results.append(
            BTSearchEntry(
                headword_raw=headword_raw,
                headword_macronized=normalize_bt_spelling(headword_raw),
                pos=pos,
                meanings=meanings,
                entry_url=entry_url,
                order_index=order_index,
            )
        )
    return results


def closest_bt_entry(
    attested_form: str,
    entries: list[BTSearchEntry],
) -> BTSearchEntry | None:
    """
    Resolve the closest BT entry for one attested form.

    Ranking priorities:
        1. Exact match against macronized BT display spelling
        2. Exact raw case-insensitive match
        3. Exact normalized match
        4. Prefix proximity on normalized forms
        5. Smaller edit distance between normalized forms
        6. Earlier search result order

    Args:
        attested_form: Candidate form from ambiguous list.
        entries: Parsed BT entries.

    Returns:
        Best matching entry, or ``None`` when no entries exist.

    """
    if not entries:
        return None

    return max(
        entries,
        key=lambda entry: _match_rank(attested_form, entry),
    )


def closest_entries_for_forms(
    attested_forms: list[str],
    entries: list[BTSearchEntry],
) -> dict[str, BTSearchEntry | None]:
    """
    Resolve closest BT entries for all attested forms.

    Args:
        attested_forms: Candidate forms.
        entries: Parsed BT entries from search page.

    Returns:
        Mapping of attested form to best BT entry or ``None``.

    """
    return {form: closest_bt_entry(form, entries) for form in attested_forms}


def merge_bt_entries(entry_groups: list[list[BTSearchEntry]]) -> list[BTSearchEntry]:
    """
    Merge and de-duplicate BT entries while preserving first-seen order.

    Args:
        entry_groups: Lists of BT entries (for example from multiple queries).

    Returns:
        One de-duplicated ordered list with stable ``order_index`` values.

    """
    seen_keys: set[tuple[str, str]] = set()
    merged: list[BTSearchEntry] = []
    for group in entry_groups:
        for entry in group:
            dedupe_key = (entry.entry_url, entry.headword_raw.casefold())
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            merged.append(entry)

    return [
        BTSearchEntry(
            headword_raw=entry.headword_raw,
            headword_macronized=entry.headword_macronized,
            pos=entry.pos,
            meanings=entry.meanings,
            entry_url=entry.entry_url,
            order_index=idx,
        )
        for idx, entry in enumerate(merged)
    ]


def _collapse_whitespace(text: str) -> str:
    """
    Collapse all whitespace runs to a single space.

    Args:
        text: Raw text.

    Returns:
        Clean text.

    """
    return WS_RE.sub(" ", text).strip()


def _match_rank(
    attested_form: str,
    entry: BTSearchEntry,
) -> tuple[int, int, int, int, int, int]:
    """
    Build ranking tuple for one attested form vs one BT entry.

    Args:
        attested_form: Candidate form from ambiguous list.
        entry: Parsed BT entry.

    Returns:
        Ranking tuple where larger is better.

    """
    attested_raw = unicodedata.normalize("NFC", attested_form).casefold()
    entry_raw = entry.headword_raw.casefold()
    raw_exact = int(attested_raw == entry_raw)
    macronized_exact = int(attested_raw == entry.headword_macronized.casefold())

    attested_norm = normalize_old_english(attested_form) or ""
    entry_norm = normalize_old_english(entry.headword_raw) or ""

    normalized_exact = int(bool(attested_norm) and attested_norm == entry_norm)
    prefix_proximity = int(
        bool(attested_norm)
        and bool(entry_norm)
        and (
            attested_norm.startswith(entry_norm) or entry_norm.startswith(attested_norm)
        )
    )
    edit_distance = _levenshtein_distance(attested_norm, entry_norm)

    return (
        macronized_exact,
        raw_exact,
        normalized_exact,
        prefix_proximity,
        -edit_distance,
        -entry.order_index,
    )


def _levenshtein_distance(left: str, right: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.

    Args:
        left: First string.
        right: Second string.

    Returns:
        Edit distance.

    """
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + int(left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]

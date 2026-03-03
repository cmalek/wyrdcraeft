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

        href_raw = anchor.get("href")
        href = (
            _collapse_whitespace(" ".join(href_raw))
            if isinstance(href_raw, list)
            else _collapse_whitespace(href_raw or "")
        )
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


def filter_bt_entries_by_normalized_form(
    entries: list[BTSearchEntry],
    normalized_form: str,
) -> list[BTSearchEntry]:
    """
    Keep only BT entries whose headword normalizes to the given form.

    Args:
        entries: Parsed BT search entries (e.g. from first page).
        normalized_form: Target normalized key (same normalization as macron index).

    Returns:
        Filtered list in original order; entries where
        ``normalize_old_english(entry.headword_raw) != normalized_form``
        or normalization returns ``None`` are excluded.

    """
    result: list[BTSearchEntry] = []
    for entry in entries:
        entry_norm = normalize_old_english(entry.headword_raw)
        if entry_norm is not None and entry_norm == normalized_form:
            result.append(entry)
    return result


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

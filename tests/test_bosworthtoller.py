from __future__ import annotations

from unittest.mock import MagicMock, patch

from wyrdcraeft.models.bosworth_toller import BTSearchEntry
from wyrdcraeft.services.bosworthtoller import (
    fetch_bt_search_entries,
    filter_bt_entries_by_normalized_form,
    merge_bt_entries,
    normalize_bt_spelling,
    parse_bt_search_entries,
)


def test_parse_bt_search_entries_extracts_fields() -> None:
    html = """
    <article>
      <div class="btd--search-entry">
        <header>
          <h3><a href="/137">ÁC</a></h3>
          <div class="btd--search-entry-wordclass">(n.)</div>
        </header>
        <div class="btd--search-description">
          <p>OAK ⬩ quercus ⬩ robur</p>
        </div>
      </div>
    </article>
    """

    entries = parse_bt_search_entries(html)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.headword_raw == "ÁC"
    assert entry.headword_macronized == "ĀC"
    assert entry.pos == "n."
    assert entry.meanings == ["OAK", "quercus", "robur"]
    assert entry.entry_url == "https://bosworthtoller.com/137"


def test_parse_bt_search_entries_handles_missing_pos_and_meanings() -> None:
    html = """
    <article>
      <div class="btd--search-entry">
        <header>
          <h3><a href="/37406">ac</a></h3>
        </header>
      </div>
    </article>
    """

    entries = parse_bt_search_entries(html)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.headword_raw == "ac"
    assert entry.pos == ""
    assert entry.meanings == []


def test_normalize_bt_spelling_converts_acute_to_macron() -> None:
    assert normalize_bt_spelling("ác ǽnig") == "āc ǣnig"


def test_fetch_bt_search_entries_uses_search_endpoint() -> None:
    mock_response = MagicMock()
    mock_response.text = (
        "<article><div class='btd--search-entry'>"
        "<header><h3><a href='/1'>ac</a></h3></header>"
        "</div></article>"
    )
    with patch("httpx.Client.get", return_value=mock_response) as mock_get:
        entries = fetch_bt_search_entries("ac")

    assert len(entries) == 1
    mock_get.assert_called_once_with(
        "https://bosworthtoller.com/search",
        params={"q": "ac"},
    )
    mock_response.raise_for_status.assert_called_once()


def test_filter_bt_entries_by_normalized_form_keeps_matching_drops_others() -> None:
    entries = [
        BTSearchEntry(
            headword_raw="AC",
            headword_macronized="AC",
            pos="con.",
            meanings=["but"],
            entry_url="https://bosworthtoller.com/134",
            order_index=0,
        ),
        BTSearchEntry(
            headword_raw="other",
            headword_macronized="other",
            pos="n.",
            meanings=["other"],
            entry_url="https://bosworthtoller.com/999",
            order_index=1,
        ),
        BTSearchEntry(
            headword_raw="ÁC",
            headword_macronized="ĀC",
            pos="n.",
            meanings=["oak"],
            entry_url="https://bosworthtoller.com/137",
            order_index=2,
        ),
    ]
    filtered = filter_bt_entries_by_normalized_form(entries, "ac")
    expected_count = 2
    assert len(filtered) == expected_count
    assert filtered[0].headword_raw == "AC"
    assert filtered[1].headword_raw == "ÁC"


def test_filter_bt_entries_by_normalized_form_preserves_order() -> None:
    entries = [
        BTSearchEntry(
            headword_raw="ÁC",
            headword_macronized="ĀC",
            pos="n.",
            meanings=["oak"],
            entry_url="https://bosworthtoller.com/137",
            order_index=0,
        ),
        BTSearchEntry(
            headword_raw="AC",
            headword_macronized="AC",
            pos="con.",
            meanings=["but"],
            entry_url="https://bosworthtoller.com/134",
            order_index=1,
        ),
    ]
    filtered = filter_bt_entries_by_normalized_form(entries, "ac")
    assert [e.headword_raw for e in filtered] == ["ÁC", "AC"]


def test_filter_bt_entries_by_normalized_form_empty_list_returns_empty() -> None:
    assert filter_bt_entries_by_normalized_form([], "ac") == []


def test_filter_bt_entries_by_normalized_form_no_matches_returns_empty() -> None:
    entries = [
        BTSearchEntry(
            headword_raw="other",
            headword_macronized="other",
            pos="n.",
            meanings=["x"],
            entry_url="https://bosworthtoller.com/1",
            order_index=0,
        ),
    ]
    assert filter_bt_entries_by_normalized_form(entries, "ac") == []


def test_merge_bt_entries_deduplicates_and_reindexes() -> None:
    first = [
        BTSearchEntry(
            headword_raw="AC",
            headword_macronized="AC",
            pos="con.",
            meanings=["but"],
            entry_url="https://bosworthtoller.com/134",
            order_index=0,
        ),
        BTSearchEntry(
            headword_raw="ÁC",
            headword_macronized="ĀC",
            pos="n.",
            meanings=["oak"],
            entry_url="https://bosworthtoller.com/137",
            order_index=1,
        ),
    ]
    second = [
        BTSearchEntry(
            headword_raw="ÁC",
            headword_macronized="ĀC",
            pos="n.",
            meanings=["oak"],
            entry_url="https://bosworthtoller.com/137",
            order_index=0,
        )
    ]

    merged = merge_bt_entries([first, second])
    expected_count = 2

    assert len(merged) == expected_count
    assert merged[0].entry_url == "https://bosworthtoller.com/134"
    assert merged[1].entry_url == "https://bosworthtoller.com/137"
    assert merged[0].order_index == 0
    assert merged[1].order_index == 1

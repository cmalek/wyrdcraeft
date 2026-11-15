"""Tests for one-line Bosworth-Toller definition reading."""

from __future__ import annotations

import pytest

from wyrdcraeft.services.dictionary.definition_line import definition_line


@pytest.mark.parametrize(
    ("pos", "glosses", "expected"),
    [
        ("noun", ["time; time; date"], "time, date"),
        (
            "noun",
            ["a proper time, time at which a thing can; ought to be done, time; time"],
            "a proper time, time at which a thing can or ought to be done, time",
        ),
        ("noun", ["The state; dignity of an abbot"], "The state or dignity of an abbot"),
        ("noun", ["The corn; fruit of an oak"], "The corn or fruit of an oak"),
        ("verb", ["to ward off; to guard; to save"], "ward off, guard, save"),
        ("verb", ["To ward off; To guard; To save"], "ward off, guard, save"),
        (
            "noun",
            ["Beautiful, like an elf; nymph, of elfin beauty"],
            "Beautiful, like an elf, nymph, of elfin beauty",
        ),
        ("noun", ["to ward off; to guard; to save"], "to ward off, to guard, to save"),
        ("verb", ["ward off, guard, ward off"], "ward off, guard"),
        ("noun", ["Time, time, date"], "Time, date"),
        ("noun", ["a proper time, time"], "a proper time, time"),
        ("noun", ["the refuse of things; things of no value"], "the refuse of things, things of no value"),
        ("verb", ["brought forth; pp. of"], "brought forth, pp. of"),
        ("noun", ["time; time", "time; date"], "time; time, date"),
        ("noun", ["time;; date"], "time, date"),
        ("noun", [" time ; date "], "time, date"),
        ("noun", ["", "  "], ""),
        ("noun", [], ""),
    ],
)
def test_definition_line(pos: str, glosses: list[str], expected: str) -> None:
    assert definition_line(pos, glosses) == expected

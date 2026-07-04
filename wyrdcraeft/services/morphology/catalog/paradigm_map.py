"""Map generator paradigm labels to Wright catalog ``class_key`` values."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Final

from wyrdcraeft.services.markup import normalize_morphology_title

#: Map generator acute vowels to macron spellings used in ``wright_paradigms.json``.
_ACUTE_TO_MACRON: Final[dict[int, str]] = str.maketrans(
    {
        "\u00e1": "\u0101",
        "\u00e9": "\u0113",
        "\u00ed": "\u012b",
        "\u00f3": "\u014d",
        "\u00fa": "\u016b",
        "\u00fd": "\u0233",
        "\u01fd": "\u01e3",
    },
)

#: Present-participle lemma suffixes for participial class assignment.
_PRESENT_PARTICIPLE_SUFFIXES: Final[tuple[str, ...]] = ("ende", "iende")

#: Catalog ``class_key`` for present participial adjective lemmas.
_PRESENT_PARTICIPLE_CLASS_KEY: Final[str] = "adj.present_participle"

#: Catalog ``class_key`` for past participial adjective lemmas.
_PAST_PARTICIPLE_CLASS_KEY: Final[str] = "adj.past_participle"


def _canonical_exemplar_key(text: str) -> str:
    """
    Normalize one paradigmatic word for fixture lookup.

    Args:
        text: Raw paradigmatic word or generator paradigm label.

    Returns:
        Canonical lookup key aligned with ``wright_paradigms.json`` spelling.

    """
    return normalize_morphology_title(text).translate(_ACUTE_TO_MACRON)


class ParadigmClassMapper:
    """
    Resolve generator paradigm labels to catalog ``class_key`` values.

    Note:
        Resolution uses only ``wyrdcraeft/etc/morphology/wright_paradigms.json``.
        Each morph class ``paradigmatic_words`` entry indexes that class by part
        of speech (``noun``, ``verb``, ``adjective``). Generator labels that do
        not match a fixture exemplar after canonicalization return ``None``.

    Args:
        fixture_path: Optional override for tests; defaults to packaged fixture.

    """

    #: POS-scoped exemplar lookup keys mapped to catalog ``class_key``.
    _exemplar_index: dict[str, dict[str, str]]
    #: Optional generator-label overrides from ``paradigm_exemplar_map.json``.
    _override_index: dict[str, dict[str, str]]

    def __init__(self, fixture_path: Path | None = None) -> None:
        """
        Build exemplar and override indexes from packaged catalog fixtures.

        Args:
            fixture_path: Optional ``wright_paradigms.json`` path for tests.

        """
        resolved_fixture = fixture_path or Path(
            str(files("wyrdcraeft").joinpath("etc/morphology/wright_paradigms.json")),
        )
        override_path = resolved_fixture.with_name("paradigm_exemplar_map.json")
        payload = json.loads(resolved_fixture.read_text(encoding="utf-8"))
        self._exemplar_index = self._build_exemplar_index(payload["morph_classes"])
        self._override_index = self._load_override_index(override_path)

    @staticmethod
    def _build_exemplar_index(
        morph_classes: list[dict[str, object]],
    ) -> dict[str, dict[str, str]]:
        """
        Index fixture ``paradigmatic_words`` by POS and canonical exemplar key.

        Args:
            morph_classes: Parsed ``morph_classes`` rows from the fixture.

        Returns:
            Mapping from POS label to exemplar-key → ``class_key``.

        """
        index: dict[str, dict[str, str]] = {}
        for morph_class in morph_classes:
            pos = str(morph_class["pos"])
            class_key = str(morph_class["id"])
            pos_index = index.setdefault(pos, {})
            paradigmatic_words = morph_class.get("paradigmatic_words", [])
            if not isinstance(paradigmatic_words, list):
                continue
            for word in paradigmatic_words:
                key = _canonical_exemplar_key(str(word))
                if key:
                    pos_index[key] = class_key
        return index

    @staticmethod
    def _load_override_index(path: Path) -> dict[str, dict[str, str]]:
        """
        Load optional generator-label overrides from JSON.

        Args:
            path: Path to ``paradigm_exemplar_map.json``.

        Returns:
            POS-scoped override maps, or empty dicts when the file is absent.

        """
        if not path.exists():
            return {"noun": {}, "adjective": {}, "verb": {}}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            "noun": {
                _canonical_exemplar_key(str(label)): str(class_key)
                for label, class_key in payload.get("noun", {}).items()
            },
            "adjective": {
                _canonical_exemplar_key(str(label)): str(class_key)
                for label, class_key in payload.get("adjective", {}).items()
            },
            "verb": {
                _canonical_exemplar_key(str(label)): str(class_key)
                for label, class_key in payload.get("verb", {}).items()
            },
        }

    def _lookup(self, pos: str, label: str) -> str | None:
        """
        Resolve one generator label for a POS using fixture and overrides.

        Args:
            pos: Catalog POS vocabulary value.
            label: Generator paradigm or exemplar label.

        Returns:
            Matching ``class_key``, or ``None`` when no fixture exemplar matches.

        """
        key = _canonical_exemplar_key(label)
        if not key:
            return None
        override = self._override_index.get(pos, {}).get(key)
        if override is not None:
            return override
        return self._exemplar_index.get(pos, {}).get(key)

    def class_key_from_noun_paradigm(self, paradigm: str) -> str | None:
        """
        Map one noun assigner paradigm label to a catalog ``class_key``.

        Args:
            paradigm: Value from ``Word.noun_paradigm``.

        Returns:
            Catalog ``class_key`` when the label matches a fixture exemplar.

        """
        return self._lookup("noun", paradigm)

    def class_key_from_adj_paradigm(self, paradigm: str) -> str | None:
        """
        Map one adjective assigner paradigm label to a catalog ``class_key``.

        Args:
            paradigm: Value from ``Word.adj_paradigm``.

        Returns:
            Catalog ``class_key`` when the label matches a fixture exemplar.

        """
        return self._lookup("adjective", paradigm)

    def class_key_from_verb_exemplar(self, exemplar: str) -> str | None:
        """
        Map one verb paradigm title to a catalog ``class_key``.

        Args:
            exemplar: ``VerbParadigm.title`` or equivalent paradigmatic lemma.

        Returns:
            Catalog ``class_key`` when the title matches a fixture exemplar.

        """
        return self._lookup("verb", exemplar)

    def class_key_from_verb_paradigm_id(self, para_id: str) -> str | None:
        """
        Return ``None`` because ``paraID`` is not stored in the Wright fixture.

        Note:
            ``wright_paradigms.json`` indexes verb classes by paradigmatic
            lemmas, not generator ``paraID`` values. Task 4 should resolve
            ``VerbParadigm.title`` and call ``class_key_from_verb_exemplar``.

        Args:
            para_id: Generator verbal paradigm identifier.

        Returns:
            Always ``None``.

        """
        _ = para_id
        return None

    def class_key_from_participle_title(
        self,
        title: str,
        *,
        is_present: bool,
    ) -> str | None:
        """
        Map one declined participial lemma title to a participial ``class_key``.

        Note:
            Wright treats present and past participles as adjectival classes
            (``data/OldEnglishGrammar.pdf``). Present participles in the
            generator often end in ``-ende`` / ``-iende``; past participles
            use the dedicated past-participle catalog row. Part-of-speech
            scope: ``adjective``.

        Args:
            title: Declined participial lemma title.
            is_present: ``True`` for present participles, ``False`` for past.

        Returns:
            ``adj.present_participle`` or ``adj.past_participle`` when the
            title matches fixture heuristics; otherwise ``None``.

        """
        if is_present:
            normalized = _canonical_exemplar_key(title)
            if normalized.endswith(_PRESENT_PARTICIPLE_SUFFIXES):
                return _PRESENT_PARTICIPLE_CLASS_KEY
            return self._lookup("adjective", title)
        return _PAST_PARTICIPLE_CLASS_KEY

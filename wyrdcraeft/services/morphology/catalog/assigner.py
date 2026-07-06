"""Assign inflectable lemmas to Wright catalog morph classes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from wyrdcraeft.models.morph_catalog import (
    LemmaMorphClass,
    MorphClass,
    MorphClassWrightSection,
)
from wyrdcraeft.models.reference import PartOfSpeech
from wyrdcraeft.services.markup import normalize_morphology_title

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.engine import Engine

    from wyrdcraeft.models.morphology import Word
    from wyrdcraeft.services.morphology.catalog.paradigm_map import ParadigmClassMapper

#: Wright inflection paragraphs start at §330 in the catalog fixture.
_INFLECTION_SECTION_MIN: int = 330

#: Assignment provenance when resolved from generator paradigm labels.
_SOURCE_PARADIGM: str = "paradigm"
#: Assignment provenance when resolved from POS and morph-class features.
_SOURCE_FEATURES: str = "features"
#: Assignment provenance when resolved from Wright section intersection.
_SOURCE_WRIGHT_SECTION: str = "wright_section"


@dataclass(frozen=True)
class _AssignmentWrite:
    """Pending upsert payload for one lemma assignment row."""

    #: Normalized lemma title used as assignment lookup key.
    normalized_title: str
    #: Catalog part-of-speech label.
    pos: str
    #: Assigned morph-class surrogate id.
    morph_class_id: int
    #: Provenance label for how the assignment was produced.
    assignment_source: str
    #: Assignment confidence score from 0 to 100.
    confidence: int


@dataclass(frozen=True)
class AssignmentResult:
    """
    Summary counts from one lemma-to-class assignment pass.

    Note:
        Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. Part-of-speech scope: ``cross-PoS``.

    """

    #: Lemmas that received or updated an assignment row.
    assigned: int
    #: Inflectable lemmas with no resolvable morph class (no row written).
    skipped: int


@dataclass(frozen=True)
class _CatalogClass:
    """In-memory morph-class row used during assignment."""

    #: Surrogate morph-class identifier.
    id: int
    #: Stable catalog business key.
    class_key: str
    #: Catalog part-of-speech label.
    pos: str
    #: Parsed ``features_json`` payload.
    features: dict[str, object]
    #: Wright section numbers linked to this class.
    wright_sections: frozenset[int]


class LemmaMorphClassAssigner:
    """
    Assign post-paradigm lemmas to catalog ``morph_classes`` rows.

    Note:
        Assignment follows Wright's inflection taxonomy in
        ``data/OldEnglishGrammar.pdf`` and the generator's POS flags in
        ``data/Ondej_Tich_40-54-1.pdf``. Each inflectable lemma is keyed by
        ``(normalized_title, pos)`` where ``pos`` uses catalog vocabulary
        (``noun``, ``verb``, ``adjective``, ``adverb``, ``pronoun``).
        Declined participial lemmas such as ``berende`` are stored under
        ``adjective`` with participial ``class_key`` values. Part-of-speech
        scope: ``cross-PoS``.

    Args:
        engine: SQLAlchemy engine to the seeded canonical morphology DB.
        paradigm_mapper: Resolves generator paradigm labels to ``class_key``.

    """

    #: Compiled regex for Wright section numbers embedded in ``Word.wright``.
    _WRIGHT_SECTION_RE: re.Pattern[str] = re.compile(r"\d+")
    #: SQLAlchemy session factory bound to the catalog engine.
    _session_factory: sessionmaker[Session]
    #: Resolves generator paradigm labels to catalog ``class_key`` values.
    _paradigm_mapper: ParadigmClassMapper
    #: Catalog ``class_key`` to surrogate ``morph_classes.id`` map.
    _class_key_to_id: dict[str, int]
    #: Assignable morph classes grouped by catalog POS label.
    _classes_by_pos: dict[str, list[_CatalogClass]]

    def __init__(
        self,
        engine: Engine,
        paradigm_mapper: ParadigmClassMapper,
    ) -> None:
        """
        Build catalog indexes used by the assignment pipeline.

        Note:
            Linguistic behavior follows ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. Part-of-speech scope:
            ``cross-PoS``.

        Args:
            engine: SQLAlchemy engine to the seeded canonical morphology DB.
            paradigm_mapper: Resolves generator paradigm labels to ``class_key``.

        """
        #: SQLAlchemy session factory bound to the catalog engine.
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        #: Resolves generator paradigm labels to catalog ``class_key`` values.
        self._paradigm_mapper = paradigm_mapper
        with self._session_factory() as session:
            #: Catalog ``class_key`` to surrogate id map and POS-grouped classes.
            self._class_key_to_id, self._classes_by_pos = self._load_catalog(session)

    @staticmethod
    def _load_catalog(
        session: Session,
    ) -> tuple[dict[str, int], dict[str, list[_CatalogClass]]]:
        """
        Load assignable morph classes and Wright section links from the DB.

        Args:
            session: Open SQLAlchemy session.

        Returns:
            Tuple of ``class_key`` → id map and POS → class list.

        """
        morph_classes = session.scalars(
            select(MorphClass).where(MorphClass.is_assignable == 1),
        ).all()
        section_rows = session.scalars(select(MorphClassWrightSection)).all()
        sections_by_class: dict[int, set[int]] = {}
        for row in section_rows:
            sections_by_class.setdefault(row.morph_class_id, set()).add(row.section_no)

        class_key_to_id: dict[str, int] = {}
        classes_by_pos: dict[str, list[_CatalogClass]] = {}
        for morph_class in morph_classes:
            class_key_to_id[morph_class.class_key] = morph_class.id
            features = json.loads(morph_class.features_json)
            pos_code = morph_class.part_of_speech.code
            catalog_class = _CatalogClass(
                id=morph_class.id,
                class_key=morph_class.class_key,
                pos=pos_code,
                features=features if isinstance(features, dict) else {},
                wright_sections=frozenset(sections_by_class.get(morph_class.id, set())),
            )
            classes_by_pos.setdefault(pos_code, []).append(catalog_class)
        return class_key_to_id, classes_by_pos

    def assign_all(self, words: Sequence[Word]) -> AssignmentResult:
        """
        Upsert ``lemma_morph_classes`` rows for inflectable input lemmas.

        Args:
            words: Lemmas after paradigm assigners have run.

        Returns:
            Counts of assigned and skipped lemmas.

        Side Effects:
            Inserts or updates rows in ``lemma_morph_classes``.

        """
        assigned = 0
        skipped = 0
        with self._session_factory() as session:
            for word in words:
                catalog_pos = self._catalog_pos_for_word(word)
                if catalog_pos is None:
                    continue
                normalized_title = normalize_morphology_title(word.title)
                if not normalized_title:
                    skipped += 1
                    continue
                resolution = self._resolve_class_key(word, catalog_pos)
                if resolution is None:
                    skipped += 1
                    continue
                class_key, source, confidence = resolution
                morph_class_id = self._class_key_to_id.get(class_key)
                if morph_class_id is None:
                    skipped += 1
                    continue
                self._upsert_assignment(
                    session,
                    _AssignmentWrite(
                        normalized_title=normalized_title,
                        pos=catalog_pos,
                        morph_class_id=morph_class_id,
                        assignment_source=source,
                        confidence=confidence,
                    ),
                )
                assigned += 1
            session.commit()
        return AssignmentResult(assigned=assigned, skipped=skipped)

    @staticmethod
    def _catalog_pos_for_word(word: Word) -> str | None:
        """
        Map one generator ``Word`` to catalog POS vocabulary.

        Args:
            word: Post-assigner lemma row.

        Returns:
            Catalog POS label, or ``None`` when the lemma is not inflectable.

        """
        if word.pspart == 1 or word.papart == 1:
            return "adjective"
        pos_flags: tuple[tuple[int, str], ...] = (
            (word.verb, "verb"),
            (word.noun, "noun"),
            (word.adjective, "adjective"),
            (word.adverb, "adverb"),
            (word.pronoun, "pronoun"),
        )
        for flag, catalog_pos in pos_flags:
            if flag == 1:
                return catalog_pos
        return None

    def _resolve_class_key(
        self,
        word: Word,
        catalog_pos: str,
    ) -> tuple[str, str, int] | None:
        """
        Resolve one lemma to ``(class_key, assignment_source, confidence)``.

        Args:
            word: Post-assigner lemma row.
            catalog_pos: Catalog POS for the assignment key.

        Returns:
            Resolution tuple, or ``None`` when no morph class matches.

        """
        paradigm_key = self._class_key_from_paradigm(word, catalog_pos)
        if paradigm_key is not None:
            return paradigm_key, _SOURCE_PARADIGM, 100

        features_key = self._class_key_from_features(word, catalog_pos)
        if features_key is not None:
            return features_key, _SOURCE_FEATURES, 100

        wright_key = self._class_key_from_wright_sections(word, catalog_pos)
        if wright_key is not None:
            return wright_key, _SOURCE_WRIGHT_SECTION, 100

        return None

    def _class_key_from_paradigm(self, word: Word, catalog_pos: str) -> str | None:
        """
        Resolve ``class_key`` from generator paradigm labels (priority 1).

        Args:
            word: Post-assigner lemma row.
            catalog_pos: Catalog POS for the assignment key.

        Returns:
            Catalog ``class_key`` when paradigm mapping succeeds.

        """
        if catalog_pos == "noun" and word.noun_paradigm:
            return self._paradigm_mapper.class_key_from_noun_paradigm(
                word.noun_paradigm[0],
            )
        if catalog_pos == "adjective":
            if word.pspart == 1 or word.papart == 1:
                return self._paradigm_mapper.class_key_from_participle_title(
                    word.title,
                    is_present=word.pspart == 1,
                )
            if word.adj_paradigm:
                return self._paradigm_mapper.class_key_from_adj_paradigm(
                    word.adj_paradigm[0],
                )
        if catalog_pos == "verb" and word.vb_paradigm:
            para = word.vb_paradigm[0]
            by_id = self._paradigm_mapper.class_key_from_verb_paradigm_id(para.ID)
            if by_id is not None:
                return by_id
            return self._paradigm_mapper.class_key_from_verb_exemplar(para.title)
        return None

    def _class_key_from_features(self, word: Word, catalog_pos: str) -> str | None:
        """
        Resolve ``class_key`` from POS flags and morph-class features (priority 2).

        Args:
            word: Post-assigner lemma row.
            catalog_pos: Catalog POS for the assignment key.

        Returns:
            Best matching ``class_key``, or ``None`` when ambiguous or unmatched.

        """
        candidates = self._classes_by_pos.get(catalog_pos, [])
        if not candidates:
            return None

        scored: list[tuple[int, _CatalogClass]] = []
        for candidate in candidates:
            score = LemmaMorphClassAssigner._feature_match_score(
                word,
                catalog_pos,
                candidate.features,
            )
            if score > 0:
                scored.append((score, candidate))
        if not scored:
            return None

        max_score = max(score for score, _ in scored)
        best = [candidate for score, candidate in scored if score == max_score]
        if len(best) != 1:
            return None
        return best[0].class_key

    @staticmethod
    def _feature_match_score(
        word: Word,
        catalog_pos: str,
        features: dict[str, object],
    ) -> int:
        """
        Score how well one lemma matches one morph-class feature dict.

        Args:
            word: Post-assigner lemma row.
            catalog_pos: Catalog POS for the assignment key.
            features: Parsed ``morph_classes.features_json``.

        Returns:
            Match score; zero means no match.

        """
        scorers = {
            "noun": LemmaMorphClassAssigner._noun_feature_score,
            "verb": LemmaMorphClassAssigner._verb_feature_score,
            "adjective": LemmaMorphClassAssigner._adjective_feature_score,
        }
        scorer = scorers.get(catalog_pos)
        if scorer is None:
            return 1
        return scorer(word, features)

    @staticmethod
    def _noun_feature_score(word: Word, features: dict[str, object]) -> int:
        """
        Score noun lemma flags against one morph-class feature dict.

        Args:
            word: Post-assigner lemma row.
            features: Parsed ``morph_classes.features_json``.

        Returns:
            Match score; zero means no match.

        """
        gender_scope = features.get("gender_scope")
        if isinstance(gender_scope, list) and gender_scope:
            word_genders = {
                label
                for flag, label in (
                    (word.n_masc, "masculine"),
                    (word.n_fem, "feminine"),
                    (word.n_neut, "neuter"),
                )
                if flag == 1
            }
            if word_genders and not word_genders.intersection(gender_scope):
                return 0
        return 1

    @staticmethod
    def _verb_feature_score(word: Word, features: dict[str, object]) -> int:
        """
        Score verb lemma flags against one morph-class feature dict.

        Args:
            word: Post-assigner lemma row.
            features: Parsed ``morph_classes.features_json``.

        Returns:
            Match score; zero means no match.

        """
        strategy = features.get("generation_strategy")
        if word.vb_pretpres == 1:
            return 1 if strategy == "preterite_present" else 0
        if word.vb_anomalous == 1:
            return 1 if strategy == "lexeme_specific" else 0
        if word.vb_weak == 1:
            return 1 if strategy == "dental_suffix" else 0
        if word.vb_strong == 1:
            return 1 if strategy == "ablaut" else 0
        return 0

    @staticmethod
    def _adjective_feature_score(word: Word, features: dict[str, object]) -> int:
        """
        Score adjective lemma flags against one morph-class feature dict.

        Args:
            word: Post-assigner lemma row.
            features: Parsed ``morph_classes.features_json``.

        Returns:
            Match score; zero means no match.

        """
        participle = features.get("participle")
        if word.pspart == 1:
            return 1 if participle == "present" else 0
        if word.papart == 1:
            return 1 if participle == "past" else 0
        strength = features.get("strength")
        if strength in {"weak", "strong"}:
            return 1
        return 0

    def _class_key_from_wright_sections(
        self,
        word: Word,
        catalog_pos: str,
    ) -> str | None:
        """
        Resolve ``class_key`` from Wright section intersection (priority 3).

        Args:
            word: Post-assigner lemma row.
            catalog_pos: Catalog POS for the assignment key.

        Returns:
            Best matching ``class_key``, or ``None`` when no section overlap.

        """
        word_sections = self._parse_wright_sections(word.wright)
        if not word_sections:
            return None

        candidates = self._classes_by_pos.get(catalog_pos, [])
        best: tuple[int, int, str] | None = None
        for candidate in candidates:
            overlap = word_sections.intersection(candidate.wright_sections)
            if not overlap:
                continue
            overlap_size = len(overlap)
            section_span = len(candidate.wright_sections) or 1
            rank = (overlap_size, -section_span, candidate.class_key)
            if best is None or rank[:2] > best[:2] or (
                rank[:2] == best[:2] and rank[2] < best[2]
            ):
                best = (overlap_size, -section_span, candidate.class_key)
        if best is None:
            return None
        return best[2]

    @classmethod
    def _parse_wright_sections(cls, wright: str) -> set[int]:
        """
        Extract inflection Wright section numbers from ``Word.wright``.

        Args:
            wright: Stored Wright analysis string from the dictionary.

        Returns:
            Section numbers at or above ``_INFLECTION_SECTION_MIN``.

        """
        if not wright or wright.strip() in {"", "0"}:
            return set()
        sections: set[int] = set()
        for match in cls._WRIGHT_SECTION_RE.finditer(wright):
            section_no = int(match.group())
            if section_no >= _INFLECTION_SECTION_MIN:
                sections.add(section_no)
        return sections

    @staticmethod
    def _upsert_assignment(session: Session, write: _AssignmentWrite) -> None:
        """
        Insert or update one ``lemma_morph_classes`` row.

        Args:
            session: Open SQLAlchemy session.
            write: Pending assignment upsert payload.

        Side Effects:
            Adds or mutates a ``LemmaMorphClass`` row in ``session``.

        """
        existing = session.scalar(
            select(LemmaMorphClass)
            .join(
                PartOfSpeech,
                PartOfSpeech.id == LemmaMorphClass.pos_id,
            )
            .where(
                LemmaMorphClass.normalized_title == write.normalized_title,
                PartOfSpeech.code == write.pos,
            ),
        )
        if existing is None:
            pos_id = session.execute(
                select(MorphClass.pos_id).where(MorphClass.id == write.morph_class_id),
            ).scalar_one()
            session.add(
                LemmaMorphClass(
                    normalized_title=write.normalized_title,
                    pos_id=int(pos_id),
                    morph_class_id=write.morph_class_id,
                    assignment_source=write.assignment_source,
                    confidence=write.confidence,
                ),
            )
            return
        existing.morph_class_id = write.morph_class_id
        existing.assignment_source = write.assignment_source
        existing.confidence = write.confidence

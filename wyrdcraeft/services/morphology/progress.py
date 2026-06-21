"""Live progress helpers for morphology generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from rich.progress import BarColumn, Progress, TaskID, TaskProgressColumn, TextColumn

from wyrdcraeft.cli.utils import create_stderr_console

if TYPE_CHECKING:
    from rich.console import Console

    from .session import GeneratorSession


@dataclass(frozen=True)
class MorphologyStageCounts:
    """
    Input-word totals for one morphology generation run.

    Note:
        Cross-PoS scope. These counts align with the source-lemma buckets used
        by ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, they count how many source items each generation stage
        will process.

    Args:
        manual_forms: Count of manual-form rows processed as source items.
        verbs: Count of eligible verb lemmas.
        adjectives: Count of eligible adjective lemmas.
        adverbs: Count of eligible adverb lemmas.
        numerals: Count of eligible numeral lemmas.
        nouns: Count of eligible noun lemmas.

    """

    #: Count of manual-form source items.
    manual_forms: int
    #: Count of eligible verb lemmas.
    verbs: int
    #: Count of eligible adjective lemmas.
    adjectives: int
    #: Count of eligible adverb lemmas.
    adverbs: int
    #: Count of eligible numeral lemmas.
    numerals: int
    #: Count of eligible noun lemmas.
    nouns: int


@dataclass(frozen=True)
class MorphologyStageSnapshot:
    """
    One rendered stage state used to build progress banner text.

    Args:
        completed: Number of processed source words in the stage.
        total: Total source words in the stage.
        lemma: Currently visible lemma/title.
        wright: Currently visible Wright label, when present.
        forms_written: Total emitted rows written so far in the session.

    """

    #: Number of processed source words in the stage.
    completed: int
    #: Total source words in the stage.
    total: int
    #: Currently visible lemma/title.
    lemma: str
    #: Currently visible Wright label, when present.
    wright: str
    #: Total emitted rows written so far in the session.
    forms_written: int


class MorphologyStage(StrEnum):
    """
    Stable stage labels for morphology generation progress.

    Note:
        Cross-PoS scope. The stage order mirrors the morphology pipeline
        described by ``data/OldEnglishGrammar.pdf`` and
        ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this names the
        progress buckets shown while verbs, nouns, adjectives, adverbs,
        numerals, and manual override rows are processed.

    """

    #: Manual-form stage label.
    MANUAL = "manual"
    #: Verb generation stage label.
    VERBS = "verbs"
    #: Adjective generation stage label.
    ADJECTIVES = "adjectives"
    #: Adverb generation stage label.
    ADVERBS = "adverbs"
    #: Numeral generation stage label.
    NUMERALS = "numerals"
    #: Noun generation stage label.
    NOUNS = "nouns"


class MorphologySetupStep(StrEnum):
    """
    Stable setup-step labels for pre-generation morphology work.

    Note:
        Cross-PoS scope. These setup phases prepare the morphology session used
        by ``data/OldEnglishGrammar.pdf`` and ``data/Ondej_Tich_40-54-1.pdf``.
        In plain terms, they name the startup work that happens before any
        generation stage begins.

    """

    #: Input data loading step label.
    LOAD_DATA = "load data"
    #: Optional limiting and recategorization step label.
    APPLY_LIMIT = "apply limit"
    #: Prefix and hyphen cleanup step label.
    NORMALIZE_FORMS = "normalize forms"
    #: Syllable counting step label.
    COUNT_SYLLABLES = "count syllables"
    #: Verb paradigm assignment step label.
    ASSIGN_VERB_PARADIGMS = "assign verb paradigms"
    #: Adjective paradigm assignment step label.
    ASSIGN_ADJ_PARADIGMS = "assign adjective paradigms"
    #: Noun paradigm assignment step label.
    ASSIGN_NOUN_PARADIGMS = "assign noun paradigms"


class MorphologyGenerateProgressCoordinator:
    """
    Coordinate stable stderr-only live progress for morphology generation.

    Keyword Args:
        progress_every_words: Update displayed lemma on first, every Nth, and
            final processed word.
        console: Optional Rich console. Defaults to shared stderr console.
        enabled: Whether progress rendering is enabled.

    """

    #: Stable progress display order across all morphology stages.
    STAGE_ORDER: tuple[MorphologyStage, ...] = (
        MorphologyStage.MANUAL,
        MorphologyStage.VERBS,
        MorphologyStage.ADJECTIVES,
        MorphologyStage.ADVERBS,
        MorphologyStage.NUMERALS,
        MorphologyStage.NOUNS,
    )
    #: Stable startup step order before generation begins.
    SETUP_ORDER: tuple[MorphologySetupStep, ...] = (
        MorphologySetupStep.LOAD_DATA,
        MorphologySetupStep.APPLY_LIMIT,
        MorphologySetupStep.NORMALIZE_FORMS,
        MorphologySetupStep.COUNT_SYLLABLES,
        MorphologySetupStep.ASSIGN_VERB_PARADIGMS,
        MorphologySetupStep.ASSIGN_ADJ_PARADIGMS,
        MorphologySetupStep.ASSIGN_NOUN_PARADIGMS,
    )

    def __init__(
        self,
        *,
        progress_every_words: int,
        console: Console | None = None,
        enabled: bool = True,
    ) -> None:
        """
        Initialize one coordinator instance for one generation run.

        Keyword Args:
            progress_every_words: Lemma banner update cadence in processed words.
            console: Optional Rich console used for rendering.
            enabled: Whether progress output should render at all.

        Raises:
            ValueError: The cadence is not a positive integer.

        """
        if progress_every_words <= 0:
            msg = "progress_every_words must be a positive integer."
            raise ValueError(msg)

        #: Word cadence for visible lemma updates.
        self.progress_every_words = progress_every_words
        #: Whether rendering is enabled for this run.
        self.enabled = enabled
        #: Console receiving progress output.
        self.console = console or create_stderr_console()
        #: Rich progress renderer bound to stderr.
        self._progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            redirect_stdout=False,
            redirect_stderr=False,
            disable=not enabled,
        )
        #: Rich task ids keyed by stable morphology stage.
        self._task_ids: dict[MorphologyStage, TaskID] = {}
        #: Rich task ids keyed by stable setup step.
        self._setup_task_ids: dict[MorphologySetupStep, TaskID] = {}
        #: Last lemma kept in banner for each stage.
        self._visible_lemmas: dict[MorphologyStage, str] = {}

    @classmethod
    def compute_stage_totals_from_counts(
        cls,
        counts: MorphologyStageCounts,
    ) -> dict[MorphologyStage, int]:
        """
        Build one stable stage-total mapping from explicit count values.

        Args:
            counts: Explicit stage counts grouped for one generation run.

        Returns:
            Stage-total mapping in CLI display order.

        """
        return {
            MorphologyStage.MANUAL: counts.manual_forms,
            MorphologyStage.VERBS: counts.verbs,
            MorphologyStage.ADJECTIVES: counts.adjectives,
            MorphologyStage.ADVERBS: counts.adverbs,
            MorphologyStage.NUMERALS: counts.numerals,
            MorphologyStage.NOUNS: counts.nouns,
        }

    @classmethod
    def compute_stage_totals_for_session(
        cls,
        session: GeneratorSession,
    ) -> dict[MorphologyStage, int]:
        """
        Compute stage totals from current session state.

        Note:
            Cross-PoS scope. The totals follow the real iteration criteria used
            by morphology generation per ``data/OldEnglishGrammar.pdf`` and
            ``data/Ondej_Tich_40-54-1.pdf``. In plain terms, this counts source
            lemmas that will be processed in each stage, not emitted output rows.

        Args:
            session: Active generation session.

        Returns:
            Stage-total mapping matching actual generation loops as closely as
            possible.

        """
        return cls.compute_stage_totals_from_counts(
            MorphologyStageCounts(
                manual_forms=len(session.manual_forms),
                verbs=sum(
                    1
                    for word in session.words
                    if word.verb == 1 and (word.pspart + word.papart == 0)
                ),
                adjectives=len(
                    [
                        word
                        for word in session.adjectives
                        if (word.adjective == 1 or (word.pspart + word.papart) > 0)
                        and word.numeral != 1
                    ]
                ),
                adverbs=sum(1 for word in session.words if word.adverb == 1),
                numerals=sum(1 for word in session.words if word.numeral == 1),
                nouns=sum(1 for word in session.words if bool(word.noun_paradigm)),
            )
        )

    def start(self) -> None:
        """Start Rich progress rendering and register stable stage tasks."""
        if not self.enabled:
            return

        self._progress.start()
        for step in self.SETUP_ORDER:
            self._setup_task_ids[step] = self._progress.add_task(
                self._build_setup_description(step=step),
                total=1,
                completed=0,
            )
        for stage in self.STAGE_ORDER:
            self._visible_lemmas[stage] = ""
            self._task_ids[stage] = self._progress.add_task(
                self._build_description(
                    stage=stage,
                    snapshot=MorphologyStageSnapshot(
                        completed=0,
                        total=0,
                        lemma="",
                        wright="",
                        forms_written=0,
                    ),
                ),
                total=0,
                completed=0,
            )

    def stop(self) -> None:
        """Stop Rich progress rendering."""
        if self.enabled:
            self._progress.stop()

    def advance_setup(self, step: MorphologySetupStep) -> None:
        """
        Advance setup progress for one completed startup step.

        Args:
            step: Setup step that has just completed.

        """
        if not self.enabled:
            return

        self._progress.update(
            self._setup_task_ids[step],
            completed=1,
            refresh=True,
        )

    def start_stage(self, stage: MorphologyStage, *, total: int) -> None:
        """
        Initialize one stage banner with its current total.

        Args:
            stage: Stage being entered.

        Keyword Args:
            total: Number of source lemmas in the stage.

        """
        if not self.enabled:
            return

        self._visible_lemmas[stage] = ""
        self._progress.update(
            self._task_ids[stage],
            total=total,
            completed=0,
            description=self._build_description(
                stage=stage,
                snapshot=MorphologyStageSnapshot(
                    completed=0,
                    total=total,
                    lemma="",
                    wright="",
                    forms_written=0,
                ),
            ),
            refresh=True,
        )

    def advance(
        self,
        stage: MorphologyStage,
        *,
        lemma: str,
        wright: str | None,
        forms_written: int,
    ) -> None:
        """
        Advance one stage by one processed lemma and refresh its banner.

        Args:
            stage: Active stage being advanced.

        Keyword Args:
            lemma: Current lemma/title for the processed source item.
            wright: Optional Wright label for the source item.
            forms_written: Total emitted rows so far in the session.

        """
        if not self.enabled:
            return

        task = self._progress.tasks[self._task_ids[stage]]
        completed = int(task.completed) + 1
        total = int(task.total or 0)
        if self._should_update_lemma(completed=completed, total=total):
            self._visible_lemmas[stage] = lemma

        self._progress.update(
            self._task_ids[stage],
            advance=1,
            description=self._build_description(
                stage=stage,
                snapshot=MorphologyStageSnapshot(
                    completed=completed,
                    total=total,
                    lemma=self._visible_lemmas[stage],
                    wright=wright or "",
                    forms_written=forms_written,
                ),
            ),
            refresh=True,
        )

    def finish_stage(self, stage: MorphologyStage) -> None:
        """
        Mark one stage complete without changing stdout summary behavior.

        Args:
            stage: Stage that has completed.

        """
        if not self.enabled:
            return

        task = self._progress.tasks[self._task_ids[stage]]
        total = int(task.total or 0)
        self._progress.update(
            self._task_ids[stage],
            completed=total,
            refresh=True,
        )

    def _should_update_lemma(self, *, completed: int, total: int) -> bool:
        """
        Decide whether the visible lemma banner should change.

        Keyword Args:
            completed: 1-based completed count after current advance.
            total: Stage total.

        Returns:
            True when the banner should refresh for the current lemma.

        """
        if completed <= 1:
            return True
        if completed >= total:
            return True
        return completed % self.progress_every_words == 0

    def _build_description(
        self,
        *,
        stage: MorphologyStage,
        snapshot: MorphologyStageSnapshot,
    ) -> str:
        """
        Build one stage banner string for Rich progress output.

        Keyword Args:
            stage: Stage whose banner is being rendered.
            snapshot: Rendered stage state for the current progress line.

        Returns:
            Human-readable banner text for one progress task.

        """
        parts = [
            stage.value,
            f"word {snapshot.completed}/{snapshot.total}",
        ]
        if snapshot.lemma:
            parts.append(snapshot.lemma)
        if snapshot.wright:
            parts.append(f"wright={snapshot.wright}")
        parts.append(f"forms_written={snapshot.forms_written}")
        return " | ".join(parts)

    def _build_setup_description(
        self,
        *,
        step: MorphologySetupStep,
    ) -> str:
        """
        Build one setup-status banner string for startup work.

        Keyword Args:
            step: Setup step that is currently complete or active.

        Returns:
            Human-readable setup progress text.

        """
        return f"setup | {step.value}"

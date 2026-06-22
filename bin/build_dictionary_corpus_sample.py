#!/usr/bin/env python3
"""Build a stratified Bosworth-Toller dictionary corpus sample fixture."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from wyrdcraeft.services.dictionary import BTLineSplitter


@dataclass(frozen=True)
class CorpusSampleResult:
    """
    Result of one corpus-sample build run.

    Attributes:
        keys: Selected lookup keys in corpus order.
        lines: Selected raw source lines in corpus order.
        step: Stratification step used for key sampling.
        key_count: Number of keys in the sample.
        line_count: Number of lines in the sample.
        total_keys: Total available source keys before sampling.

    """

    #: Selected lookup keys in corpus order.
    keys: tuple[str, ...]
    #: Selected source lines in corpus order.
    lines: tuple[str, ...]
    #: Stratification interval used for key selection.
    step: int
    #: Number of sampled keys.
    key_count: int
    #: Number of sampled lines.
    line_count: int
    #: Total key count discovered in source.
    total_keys: int


class DictionaryCorpusSampler:
    """
    Build a stratified parser-regression corpus from ``data/oe_bt.txt``.

    The sampler indexes every valid three-field ``@`` line by its lookup key
    (the third field), then picks approximately 750 keys in corpus order and
    includes all editorial siblings for each selected key.

    Args:
        source_path: Path to ``oe_bt.txt`` source data.
        target_keys: Initial target for sampled key count.
        min_lines: Lower accepted output bound.
        max_lines: Upper accepted output bound.

    """

    def __init__(
        self,
        *,
        source_path: Path,
        target_keys: int = 750,
        min_lines: int = 900,
        max_lines: int = 1150,
    ) -> None:
        """
        Configure one corpus-sample build.

        Args:
            source_path: Path to Bosworth-Toller source file.
            target_keys: Desired sampled key count before adaptive tuning.
            min_lines: Lower accepted line-count bound.
            max_lines: Upper accepted line-count bound.

        """
        #: Source file to sample.
        self.source_path = source_path
        #: Desired sampled key count.
        self.target_keys = target_keys
        #: Lower accepted line-count bound.
        self.min_lines = min_lines
        #: Upper accepted line-count bound.
        self.max_lines = max_lines
        #: Three-field splitter reused from parser services.
        self.splitter = BTLineSplitter()

    def build(self) -> CorpusSampleResult:
        """
        Build one stratified corpus sample.

        Returns:
            Sample result with selected keys and lines.

        """
        key_to_lines = self._index_lines_by_key()
        ordered_keys = sorted(
            key_to_lines.keys(),
            key=lambda key: key_to_lines[key][0][0],
        )
        total_keys = len(ordered_keys)

        best: CorpusSampleResult | None = None
        best_distance: int | None = None
        midpoint = (self.min_lines + self.max_lines) // 2

        for candidate_target in self._candidate_target_keys():
            selected_keys, step = self._sample_keys(
                ordered_keys=ordered_keys,
                target_keys=candidate_target,
            )
            selected_lines = self._selected_lines(
                selected_keys=selected_keys,
                key_to_lines=key_to_lines,
            )
            result = CorpusSampleResult(
                keys=tuple(selected_keys),
                lines=tuple(selected_lines),
                step=step,
                key_count=len(selected_keys),
                line_count=len(selected_lines),
                total_keys=total_keys,
            )
            if self.min_lines <= result.line_count <= self.max_lines:
                return result
            distance = abs(result.line_count - midpoint)
            if best is None or best_distance is None or distance < best_distance:
                best = result
                best_distance = distance

        if best is None:
            message = "Failed to select corpus sample result."
            raise RuntimeError(message)
        return best

    def _index_lines_by_key(self) -> dict[str, list[tuple[int, str]]]:
        """
        Index source lines by lookup key while preserving source line order.

        Returns:
            Mapping of ``slug_field`` keys to ``(line_no, line)`` tuples.

        """
        key_to_lines: dict[str, list[tuple[int, str]]] = {}
        for line_no, line in enumerate(
            self.source_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            split = self.splitter.split(line)
            if split is None:
                continue
            key = split.slug_field.strip()
            if not key:
                continue
            key_to_lines.setdefault(key, []).append((line_no, line))
        return key_to_lines

    def _sample_keys(
        self,
        *,
        ordered_keys: list[str],
        target_keys: int,
    ) -> tuple[list[str], int]:
        """
        Sample keys by deterministic every-Nth stratification.

        Args:
            ordered_keys: Keys sorted by first source-line occurrence.
            target_keys: Desired number of sampled keys.

        Returns:
            Tuple of selected keys and the sampling step.

        """
        if not ordered_keys:
            return [], 1
        step = max(1, len(ordered_keys) // max(1, target_keys))
        return ordered_keys[::step], step

    def _selected_lines(
        self,
        *,
        selected_keys: list[str],
        key_to_lines: dict[str, list[tuple[int, str]]],
    ) -> list[str]:
        """
        Collect all editorial siblings for sampled keys in corpus order.

        Args:
            selected_keys: Sampled keys in corpus order.
            key_to_lines: Source index keyed by slug field.

        Returns:
            Selected source lines ordered by source line number.

        """
        indexed: list[tuple[int, str]] = []
        for key in selected_keys:
            indexed.extend(key_to_lines.get(key, []))
        indexed.sort(key=lambda pair: pair[0])
        return [line for _, line in indexed]

    def _candidate_target_keys(self) -> list[int]:
        """
        Produce target-key candidates for adaptive line-count tuning.

        Returns:
            Ordered candidate target-key values around ``self.target_keys``.

        """
        deltas = [0]
        for delta in range(25, 251, 25):
            deltas.extend([delta, -delta])
        candidates: list[int] = []
        seen: set[int] = set()
        for delta in deltas:
            candidate = max(1, self.target_keys + delta)
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
        return candidates


def main() -> None:
    """
    Build ``corpus_sample.txt`` and ``corpus_sample_manifest.json`` fixtures.

    Side Effects:
        Writes fixture files under ``tests/fixtures/dictionary``.

    """
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / "data" / "oe_bt.txt"
    fixture_dir = project_root / "tests" / "fixtures" / "dictionary"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = fixture_dir / "corpus_sample.txt"
    manifest_path = fixture_dir / "corpus_sample_manifest.json"

    sampler = DictionaryCorpusSampler(source_path=source_path)
    sample = sampler.build()

    corpus_path.write_text("\n".join(sample.lines) + "\n", encoding="utf-8")
    manifest = {
        "build_ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": "data/oe_bt.txt",
        "target_line_range": [sampler.min_lines, sampler.max_lines],
        "sampled_key_target": sampler.target_keys,
        "step": sample.step,
        "total_keys": sample.total_keys,
        "keys": list(sample.keys),
        "key_count": sample.key_count,
        "line_count": sample.line_count,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {corpus_path} (lines={sample.line_count}); "
        f"{manifest_path} (keys={sample.key_count}, step={sample.step})"
    )


if __name__ == "__main__":
    main()

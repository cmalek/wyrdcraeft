Status: DONE

Files changed:
- `wyrdcraeft/services/morphology/catalog/wright_audit.py`
- `wyrdcraeft/cli/morphology.py`
- `tests/morphology/test_wright_audit.py`
- `tests/test_cli_morphology.py`
- `doc/sessions/task-phase4-wright-audit-report.md`

Implementation summary:
- Added `WrightAuditService`, a read-only Phase 4 audit service that scans the bundled legacy source files, compares source-side Wright values against deterministic `lemma_morph_classes` assignments, and reports four categories: malformed legacy Wright, contradictions, unclassified rows, and blank-legacy-but-classified rows.
- Added `wyrdcraeft morphology audit-wright` with default human-readable output and optional `--json` full payload output. The command resolves bundled morphology sources from `--data-dir` or the packaged defaults, reads the requested or canonical DB, and never rewrites the source files.
- Added focused tests covering malformed `Camp` detection from `para_vb.txt`, contradiction reporting, blank legacy plus classified assignment, unclassified rows, JSON payload shape, and CLI read-only behavior for the source files.

Validation commands and output:

```text
.venv/bin/ruff check wyrdcraeft/services/morphology/catalog/wright_audit.py wyrdcraeft/cli/morphology.py
All checks passed!
```

```text
.venv/bin/mypy wyrdcraeft/services/morphology/catalog/wright_audit.py wyrdcraeft/cli/morphology.py
Success: no issues found in 2 source files
```

```text
PATH=".venv/bin:$PATH" make napoleon-gate
Napoleon gate passed: no new violations (124 total, 191 baseline keys).
```

```text
.venv/bin/pytest tests/morphology/test_wright_audit.py tests/test_cli_morphology.py -q
24 passed in 20.14s
```

Self-review:
- The audit stays report-only in v1: it reads source rows and DB assignments but does not mutate bundled morphology files, and the CLI test explicitly checks that file contents are unchanged after invocation.
- The implementation keeps legacy `wright` in an audit role only; deterministic assignment rows remain the canonical comparison target, and contradictions are only reported when both source and assigned section sets are non-empty and disjoint.
- The human-readable report is source-first and sample-capped to avoid overwhelming terminal output, while `--json` preserves full finding lists for follow-on analysis scripts.

# Documentation Quality Gate

This directory stores baseline data for the Napoleon documentation gate.

- Gate script: `scripts/quality/check_napoleon_gate.py`
- Baseline file: `doc/quality/napoleon_gate_baseline.json`

Modes:

- Default: fail on **new** violations not present in baseline.
- Strict (`--strict`): fail on **all** violations.
- Baseline refresh (`--write-baseline`): regenerate baseline from current state.

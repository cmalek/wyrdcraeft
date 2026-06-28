# Domain Docs

How the engineering skills should consume this repo's domain documentation when
exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root
- **`docs/adr/`** at the repo root for architecture decisions relevant to the
  area being changed

If either of these files does not exist, proceed silently. Do not flag their
absence or suggest creating them upfront.

## File structure

This repo is configured as a single-context repo:

```text
/
|- CONTEXT.md
|- docs/adr/
`- src/
```

## Use the glossary's vocabulary

When naming domain concepts in issues, plans, refactors, tests, or
documentation, prefer the terms defined in `CONTEXT.md`.

If a needed concept is missing from the glossary, either reconsider the wording
or note the gap for later domain-modeling work.

## Flag ADR conflicts

If a proposed change conflicts with an existing ADR, surface that explicitly
instead of silently overriding it.

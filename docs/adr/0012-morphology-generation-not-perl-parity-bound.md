---
status: accepted
---

# Morphology generation is not Perl-parity-bound

The generator began as a port of Tichý’s `create_dict31.pl`. Matching that
script byte-for-byte was the right gate while translating. We can no longer
compare against Perl in a useful way, and we should not be blocked from
fixing Tichý bugs, port mistakes, or paradigm choices that are not
historically right (Wright 1925 and related grammars outrank Tichý where they
disagree).

**Tests still must validate the generator.** Unit tests and Python snapshots
are regression locks on *current* output. When we intentionally change
behavior, we update those tests and snapshots in the same change. A snapshot
diff is not a veto; it is a prompt to say whether the change was meant.

This supersedes ADR 0009 Decision 7 (Perl as golden oracle / “a diff means a
parity regression, full stop”). ADR 0009’s class-shape work still stands.

## Considered options

- **Keep `create_dict31.pl` as oracle.** Rejected: the Perl is not runnable
  as a continuing product oracle here, and it encodes scholar-not-engineer
  bugs plus some wrong paradigms.
- **Drop generation tests and rely on review.** Rejected: we still need
  machine checks; we refuse only *Perl* as the authority.
- **Opt-in flags for every historically correct fix.** Rejected: that was the
  old quirks-ledger rule. Default output should be allowed to become more
  correct; flags remain for experimental extras if we want them, not as the
  only path to fix known errors.

## Consequences

- `tests/morphology/parity_harness.py` and related snapshots are Python
  regression fixtures, not a Perl contract. Rename in a later cleanup if the
  name misleads; do not treat a failing snapshot as “must revert.”
- `doc/source/overview/morphology_perl_quirks_ledger.rst` is a catalog of
  inherited Tichý behaviors, not a do-not-fix list.
- Wright-correct expansions (for example class-II `-ig-`/`-ige-` spellings)
  are in-scope for the default generator when tests are updated with them.

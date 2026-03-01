from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from wyrdcraeft.services.morphology.processors import (
    set_adj_paradigm,
    set_noun_paradigm,
    set_verb_paradigm,
)
from wyrdcraeft.services.morphology.session import GeneratorSession

REPO_ROOT = Path(__file__).resolve().parents[2]
SUBSET_DICTIONARY = REPO_ROOT / "tests/fixtures/morphology/test_dict.txt"
FULL_DICTIONARY = (
    REPO_ROOT / "wyrdcraeft/etc/morphology/dict_adj-vb-part-num-adv-noun.txt"
)
MANUAL_FORMS = REPO_ROOT / "wyrdcraeft/etc/morphology/manual_forms.txt"
VERBAL_PARADIGMS = REPO_ROOT / "wyrdcraeft/etc/morphology/para_vb.txt"
PREFIXES = REPO_ROOT / "wyrdcraeft/etc/morphology/prefixes.txt"


def build_session(*, dictionary_path: Path) -> GeneratorSession:
    """Create a fully prepared generator session for reference testing."""
    session = GeneratorSession()
    session.load_all(
        str(dictionary_path),
        str(MANUAL_FORMS),
        str(VERBAL_PARADIGMS),
        str(PREFIXES),
    )
    session.remove_prefixes()
    session.remove_hyphens()
    session.count_syllables()
    set_verb_paradigm(session)
    set_adj_paradigm(session)
    set_noun_paradigm(session)
    return session


@pytest.fixture
def subset_session() -> GeneratorSession:
    """Prepared session using the subset dictionary for default reference tests."""
    return build_session(dictionary_path=SUBSET_DICTIONARY)


@pytest.fixture
def full_session(request: pytest.FixtureRequest) -> GeneratorSession:
    """Prepared session using the full dictionary for optional smoke checks."""
    request.node.add_marker(pytest.mark.morphology_full)
    return build_session(dictionary_path=FULL_DICTIONARY)


def _command_invokes_perl(command: Any, *, shell: bool) -> bool:
    if isinstance(command, (list, tuple)):
        if not command:
            return False
        executable = Path(str(command[0])).name.lower()
        return executable.startswith("perl")

    if isinstance(command, str):
        lowered = command.strip().lower()
        if shell:
            tokens = lowered.replace(";", " ").replace("&&", " ").split()
            return bool(tokens) and tokens[0].startswith("perl")
        first_token = Path(lowered.split(maxsplit=1)[0]).name if lowered else ""
        return first_token.startswith("perl")

    return False


@pytest.fixture(autouse=True)
def fail_if_perl_subprocess_invoked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail fast if morphology tests attempt to execute Perl."""

    def _wrap(original: Any, label: str):
        def _wrapped(*args: Any, **kwargs: Any):
            command = kwargs.get("args")
            if command is None and args:
                command = args[0]
            shell = bool(kwargs.get("shell", False))
            if _command_invokes_perl(command, shell=shell):
                msg = (
                    "morphology test attempted Perl execution via "
                    f"subprocess.{label}: {command!r}"
                )
                pytest.fail(msg)
            return original(*args, **kwargs)

        return _wrapped

    monkeypatch.setattr(subprocess, "run", _wrap(subprocess.run, "run"))
    monkeypatch.setattr(subprocess, "Popen", _wrap(subprocess.Popen, "Popen"))
    monkeypatch.setattr(
        subprocess,
        "check_call",
        _wrap(subprocess.check_call, "check_call"),
    )
    monkeypatch.setattr(
        subprocess,
        "check_output",
        _wrap(subprocess.check_output, "check_output"),
    )

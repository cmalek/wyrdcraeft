"""ADR 0021: edit record lives in models; merger does not re-export it."""

from __future__ import annotations

import ast
import inspect
import textwrap
from typing import TYPE_CHECKING

from wyrdcraeft.services.dictionary import editorial_ops
from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Pre-existing, out of ADR 0021. Do not treat as a collaborator split.
_LINE_BUDGET_SKIP = frozenset({"collect_editorial_warnings"})


def test_bt_edit_record_imports_from_models_dictionary() -> None:
    from wyrdcraeft.models.dictionary import BTEditRecord

    assert BTEditRecord.__name__ == "BTEditRecord"


def test_bt_edit_record_exported_from_wyrdcraeft_models() -> None:
    from wyrdcraeft.models import BTEditRecord

    assert BTEditRecord.__module__ == "wyrdcraeft.models.dictionary"


def test_services_dictionary_does_not_export_bt_edit_record() -> None:
    from wyrdcraeft.services import dictionary as dictionary_pkg

    assert "BTEditRecord" not in dictionary_pkg.__all__
    assert not hasattr(dictionary_pkg, "BTEditRecord")


def test_merger_constructor_only_resolver_and_block_builder() -> None:
    params = inspect.signature(BTEditorialMerger.__init__).parameters
    assert set(params) == {"self", "resolver", "block_builder"}


def _body_line_count(obj: Callable[..., object]) -> int:
    source = textwrap.dedent(inspect.getsource(obj))
    tree = ast.parse(source)
    node = tree.body[0]
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if not body:
        return 0
    start = body[0].lineno
    end = max(getattr(stmt, "end_lineno", stmt.lineno) or stmt.lineno for stmt in body)
    return end - start + 1


def _local_functions(container: object) -> Iterator[Callable[..., object]]:
    home = container.__name__ if inspect.ismodule(container) else container.__module__
    for name, obj in inspect.getmembers(container, inspect.isfunction):
        if name.startswith("__"):
            continue
        if inspect.ismodule(container) and obj.__module__ != home:
            continue
        if inspect.isclass(container) and obj.__module__ != container.__module__:
            continue
        yield obj


def test_editorial_op_method_bodies_within_line_budget() -> None:
    targets: list[Callable[..., object]] = list(_local_functions(editorial_ops))
    for _cls_name, cls in inspect.getmembers(editorial_ops, inspect.isclass):
        if cls.__module__ != editorial_ops.__name__:
            continue
        targets.extend(_local_functions(cls))
    for obj in _local_functions(BTEditorialMerger):
        if obj.__name__ in _LINE_BUDGET_SKIP:
            continue
        targets.append(obj)
    offenders = [
        f"{obj.__qualname__}={_body_line_count(obj)}"
        for obj in targets
        if _body_line_count(obj) > 60
    ]
    assert not offenders, "method bodies exceed 60 lines: " + ", ".join(offenders)


def test_editorial_ops_module_exists() -> None:
    assert editorial_ops.__name__ == "wyrdcraeft.services.dictionary.editorial_ops"

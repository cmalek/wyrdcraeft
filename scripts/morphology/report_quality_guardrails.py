from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("wyrdcraeft/services/morphology")
MAX_FN_LEN = 80
MAX_CC = 15


def cyclomatic(node: ast.AST) -> int:
    score = 1
    for n in ast.walk(node):
        if isinstance(
            n,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.With,
                ast.AsyncWith,
                ast.ExceptHandler,
                ast.Try,
                ast.IfExp,
                ast.Match,
            ),
        ):
            score += 1
        elif isinstance(n, ast.BoolOp):
            score += max(0, len(n.values) - 1)
    return score


def report() -> None:  # noqa: PLR0912
    long_funcs: list[tuple[str, int, str, int]] = []
    complex_funcs: list[tuple[str, int, str, int]] = []
    noqa_complexity: list[tuple[str, int, str]] = []

    for file in sorted(ROOT.rglob("*.py")):
        src = file.read_text(encoding="utf-8")
        tree = ast.parse(src)

        for i, line in enumerate(src.splitlines(), start=1):
            if "# noqa:" in line and ("PLR0912" in line or "PLR0915" in line):
                noqa_complexity.append((str(file), i, line.strip()))

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.end_lineno is None:
                continue
            length = node.end_lineno - node.lineno + 1
            cc = cyclomatic(node)
            if length > MAX_FN_LEN:
                long_funcs.append((str(file), node.lineno, node.name, length))
            if cc > MAX_CC:
                complex_funcs.append((str(file), node.lineno, node.name, cc))

    print("# Morphology Guardrail Report")
    print(f"max_function_length={MAX_FN_LEN}")
    print(f"max_cyclomatic_complexity={MAX_CC}")
    print()

    print("## Long functions")
    for path_s, line_no, func_name, length in sorted(
        long_funcs, key=lambda x: (-x[3], x[0], x[1])
    ):
        print(f"{path_s}:{line_no} {func_name} ({length} lines)")
    if not long_funcs:
        print("None")
    print()

    print("## Complex functions")
    for path_s, line_no, func_name, cc in sorted(
        complex_funcs, key=lambda x: (-x[3], x[0], x[1])
    ):
        print(f"{path_s}:{line_no} {func_name} (cc={cc})")
    if not complex_funcs:
        print("None")
    print()

    print("## Existing complexity no-qa markers")
    for path_s, line_no, text in noqa_complexity:
        print(f"{path_s}:{line_no} {text}")
    if not noqa_complexity:
        print("None")


if __name__ == "__main__":
    report()

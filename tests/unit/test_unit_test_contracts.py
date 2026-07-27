from __future__ import annotations

import ast
from pathlib import Path


def _is_specs_path(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith(("specs/", "specs\\"))
    )


def _is_path_constructor(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "Path"


def _is_open_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "open"


def test_unit_tests_do_not_read_specs_directory() -> None:
    unit_tests_dir = Path(__file__).parent
    violations: list[str] = []

    for path in sorted(unit_tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if (_is_path_constructor(node) or _is_open_call(node)) and _is_specs_path(node.args[0]):
                violations.append(f"{path}:{node.lineno}")

    assert violations == []

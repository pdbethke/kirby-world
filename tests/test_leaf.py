"""kirby-world depends on kirby-terrain and nothing else, and that is checkable.

The claim is the reason this module exists as its own package. A test that
merely imports it would pass in a venv where Pillow happens to be present,
so this walks the package's own imports instead.
"""
import ast
import pathlib
import sys
import tomllib

PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "kirby_world"
PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
STDLIB = set(sys.stdlib_module_names)


def _top_level_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_the_package_imports_only_the_standard_library():
    offenders = []
    for path in sorted(PACKAGE.rglob("*.py")):
        for mod in _top_level_imports(path):
            if mod not in STDLIB and mod not in ("kirby_world", "kirby_terrain"):
                offenders.append(f"{path.name}: imports {mod!r}")
    assert offenders == [], f"kirby-world must depend on kirby-terrain only: {offenders}"


def test_the_guard_would_notice_a_dependency():
    """Guards the guard: if STDLIB had become everything, the test above
    would pass no matter what was imported."""
    assert "os" in STDLIB
    assert "numpy" not in STDLIB and "PIL" not in STDLIB


def test_pyproject_declares_only_kirby_terrain():
    """The import-walk above only catches a dependency once code actually
    imports it. Someone could add `dependencies = ["pillow"]` to
    pyproject.toml and every test would stay green until then. Pin the
    declaration itself."""
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    assert [d.split(">")[0] for d in data["project"]["dependencies"]] == ["kirby-terrain"]

"""Release guards, run against the BUILT distribution before upload.

Deliberately smaller than kirby-cost's and kirby-combat's: this package
reproduces no rules text or licensed prose (it cites pages, as the engines
do), so the content guards those repos need do not apply here. What remains is the pair that has actually bitten the
family -- a tag that disagrees with the built version, and a distribution
whose module does not import from a clean environment.

Usage: python scripts/check_release.py dist/
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FAILURES: list[str] = []


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def bad(msg: str) -> None:
    print(f"FAIL  {msg}")
    FAILURES.append(msg)


def the_one_wheel(dist: Path) -> Path | None:
    """A stale wheel left over in a local `dist/` would get guarded here
    while `twine upload dist/*` ships every wheel present. Insist on
    exactly one so a leftover build artifact fails loudly instead of being
    silently ignored (or silently approved)."""
    wheels = sorted(dist.glob("*.whl"))
    if not wheels:
        bad("no wheel in the distribution directory")
        return None
    if len(wheels) > 1:
        bad(
            "more than one wheel in the distribution directory: "
            f"{', '.join(w.name for w in wheels)}. "
            "Clean dist/ before building for release."
        )
        return None
    return wheels[0]


def built_version(wheel: Path) -> str | None:
    m = re.match(r"kirby_world-([^-]+)-", wheel.name)
    if not m:
        bad(f"cannot read a version out of {wheel.name}")
        return None
    return m.group(1)


def check_tag_matches(version: str) -> None:
    """A tag that does not match the built version publishes the wrong thing."""
    ref = os.environ.get("GITHUB_REF", "")
    if not ref.startswith("refs/tags/"):
        ok("not a tagged build; skipping the tag/version check")
        return
    tag = ref.removeprefix("refs/tags/").lstrip("v")
    if tag == version:
        ok(f"tag v{tag} agrees with the built version")
    else:
        bad(f"tag v{tag} does not match the built version {version}")


def check_imports_clean(wheel: Path, version: str) -> None:
    """The wheel must import, and answer a geometry question, with nothing
    else installed --- in particular with no fight engine. kirby-terrain is
    a declared dependency but is read lazily, only for a Furnishing's
    durability, so the probe below needs neither.

    An editable install of this very repo puts a `.pth` file on `sys.path`
    that wins over `PYTHONPATH`, so a naive probe silently imports the
    SOURCE TREE instead of the extracted wheel. The probe asserts where the
    module actually came from, not just that importing it raised nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(wheel) as z:
            z.extractall(tmp)
        probe = (
            "import os, sys;"
            "sys.modules['kirby_combat'] = None;"
            "import kirby_world as w;"
            "assert w.__file__.startswith(os.environ['EXPECTED_ROOT']), ("
            "  'imported from ' + w.__file__ + ', not the extracted wheel'"
            ");"
            "from kirby_world.movement_legality import movement_reach;"
            "s = w.Scene(id='h', name='h', bounds=w.SceneBounds(0, 0, 0, 20, 20, 4),"
            "  surfaces=[], walls=[], hazards=[], ambient=w.AmbientConditions());"
            "s = s.place_combatant('ana', w.Position(1.0, 0.0, 0.0));"
            "assert w.position_of(s, 'ana') == w.Position(1.0, 0.0, 0.0);"
            "assert movement_reach('flight', w.Position(0, 0, 1), w.Position(5, 0, 1), 10.0, s).reachable"
        )
        res = subprocess.run(
            [sys.executable, "-S", "-c", probe],
            cwd=tmp,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": tmp, "EXPECTED_ROOT": tmp},
            capture_output=True,
            text=True,
            check=False,
        )
    if res.returncode == 0:
        ok(f"kirby-world {version}: imports FROM THE WHEEL and answers a reach query with no fight engine")
    else:
        bad(f"the built wheel does not import cleanly: {res.stderr.strip()}")


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    if not dist.is_dir():
        print(f"no such directory: {dist}")
        return 1
    wheel = the_one_wheel(dist)
    if wheel is not None:
        version = built_version(wheel)
        if version is not None:
            check_tag_matches(version)
            check_imports_clean(wheel, version)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} release guard(s) failed")
        return 1
    print("all release guards passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

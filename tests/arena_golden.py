"""Capture and serialise arenas for the generators' goldens.

`kirby-api` rebuilds every fight's map from its seed and its stored
`ArenaGenerator` on each reload, so each generator's output is a contract.
This serialises a whole Arena (scene plus start positions) deterministically.

* `tests/golden/arena_walls_only.json` was written against the UNMODIFIED
  0.1.1 generator (no generator argument then); WALLS_ONLY must rebuild it.
* `tests/golden/arena_with_cover.json` was written from the 0.2.0 release
  code (f49fd1d), before 0.2.0 was published; WITH_COVER must rebuild it.

Regenerate only on purpose, and only for a NEW generator:
`python -m tests.arena_golden WITH_COVER` overwrites that generator's golden,
which hides exactly the drift the golden exists to catch for one already
released.
"""
from __future__ import annotations

import dataclasses
import json
import random
import sys
from pathlib import Path

SEEDS = (1, 2, 3, 4, 5)
FIGHTER_COUNTS = (4, 31)
GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN = GOLDEN_DIR / "arena_walls_only.json"


def golden_for(generator) -> Path:
    """The golden file for ``generator`` (an `ArenaGenerator`)."""
    return GOLDEN_DIR / f"arena_{generator.value}.json"


def serialise_arena(arena) -> str:
    """Every field that defines the scene, sorted keys, stable text."""
    doc = {
        "scene": dataclasses.asdict(arena.scene),
        "start_positions": [list(p) for p in arena.start_positions],
    }
    return json.dumps(doc, sort_keys=True, indent=1)


def build_all(build) -> dict[str, str]:
    return {
        f"seed={s},n={n}": serialise_arena(build(random.Random(s), n))
        for s in SEEDS for n in FIGHTER_COUNTS
    }


if __name__ == "__main__":
    from kirby_world.generate import ArenaGenerator, generate_arena

    if len(sys.argv) != 2:
        sys.exit("usage: python -m tests.arena_golden <ArenaGenerator name, "
                 f"one of {', '.join(g.name for g in ArenaGenerator)}>")
    generator = ArenaGenerator[sys.argv[1]]
    out = build_all(lambda rng, n: generate_arena(
        rng, fighter_count=n, generator=generator))
    path = golden_for(generator)
    path.write_text(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print(f"wrote {len(out)} scenes to {path}", file=sys.stderr)

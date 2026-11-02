"""Capture and serialise arenas for the WALLS_ONLY golden.

`kirby-api` rebuilds every fight's map from its seed on each reload, so the
0.1.1 generator's output is a contract. This serialises a whole Arena (scene
plus start positions) deterministically; `tests/golden/arena_walls_only.json`
was written by running it against the UNMODIFIED 0.1.1 generator.

Regenerate only on purpose: `python tests/arena_golden.py <generate_arena kwargs
as 'generator=...'>` is deliberately not offered, because regenerating hides
exactly the drift the golden exists to catch.
"""
from __future__ import annotations

import dataclasses
import json
import random
import sys
from pathlib import Path

SEEDS = (1, 2, 3, 4, 5)
FIGHTER_COUNTS = (4, 31)
GOLDEN = Path(__file__).parent / "golden" / "arena_walls_only.json"


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
    # Capture mode: 0.1.1 signature, no generator argument.
    from kirby_world.generate import generate_arena

    out = build_all(lambda rng, n: generate_arena(rng, fighter_count=n))
    GOLDEN.write_text(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print(f"wrote {len(out)} scenes to {GOLDEN}", file=sys.stderr)

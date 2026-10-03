"""The point of this package, as a test that cannot pass by accident.

A house with five occupants doing chores is a place and nothing else. It
must be buildable, and its geometry askable, with the fight engine NOT
importable at all --- not merely unused. The subprocess blocks the import
outright, so a stray `import kirby_combat` anywhere on the path fails here
instead of quietly succeeding in a venv where it happens to be installed.
"""
import subprocess
import sys

PROBE = """
import sys
sys.modules["kirby_combat"] = None   # any import of it now raises
from kirby_world import AmbientConditions, Position, Scene, SceneBounds, World, position_of
from kirby_world.movement_legality import movement_reach

house = Scene(id="house", name="Safehouse", bounds=SceneBounds(0, 0, 0, 20, 20, 4),
              surfaces=[], walls=[], hazards=[], ambient=AmbientConditions())
for i, who in enumerate(["ana", "ben", "cal", "dee", "eve"]):
    house = house.place_combatant(who, Position(float(i), 0.0, 0.0))
assert house.encounter is None
assert len(house.combatant_positions) == 5
assert position_of(house, "cal") == Position(2.0, 0.0, 0.0)
assert World(id="w", name="Town").scenes == []
out = movement_reach("flight", Position(0, 0, 1), Position(5, 0, 1), 10.0, house)
assert out.reachable, out
import kirby_world.construct, kirby_world.cover, kirby_world.falling, kirby_world.generate
import kirby_world.geometry, kirby_world.hazards, kirby_world.occupancy, kirby_world.visibility
print("ok")
"""


def test_a_house_with_occupants_needs_no_fight_engine():
    res = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, check=False)
    assert res.returncode == 0 and res.stdout.strip() == "ok", res.stderr


def test_the_block_would_notice_an_import():
    """Guards the guard: the block must really make the import fail."""
    res = subprocess.run(
        [sys.executable, "-c", 'import sys; sys.modules["kirby_combat"] = None; import kirby_combat'],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode != 0 and "ModuleNotFoundError" in res.stderr


def test_a_mover_who_cannot_move_goes_nowhere():
    """The seam that replaced a fight's Stunned check: whether the mover may
    move at all is asked by the caller, and the answer is honoured."""
    from kirby_world import AmbientConditions, Position, Scene, SceneBounds
    from kirby_world.movement_legality import movement_reach

    house = Scene(id="h", name="h", bounds=SceneBounds(0, 0, 0, 20, 20, 4),
                  surfaces=[], walls=[], hazards=[], ambient=AmbientConditions())
    start = Position(0, 0, 1)
    out = movement_reach("flight", start, Position(5, 0, 1), 10.0, house,
                         mover_can_move=False)
    assert not out.reachable and out.landing == start and out.fall is None

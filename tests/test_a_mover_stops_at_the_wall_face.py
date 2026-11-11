"""A man stopped by a wall ends on HIS side of it, never inside it.

The engine models a man as a point (`falling.is_supported_at`: "a
combatant's footprint is just its xy point"). Stopping that point at the
exact spot his path met the wall put him ON the wall's line, which is on
neither side of it: every sight line to him crossed the wall, so nobody on
either side could see him. Found 2026-11-11 in the corral recording, where
Billy Claiborne, knocked back into Fly's gallery, vanished from all eight
men around him.
"""
from kirby_world import AmbientConditions, Position, Scene, SceneBounds
from kirby_world.geometry import (
    WALL_FACE_CLEARANCE_M,
    line_of_sight_clear,
    short_of_the_wall,
)
from kirby_world.movement_legality import movement_reach
from kirby_world.scene import Surface, Wall

WALL = Wall(
    id="w", name="w",
    segment=(Position(5, 0, 0), Position(5, 10, 0)),
    height_m=3.0, blocks_los=True, blocks_movement=True,
    cover_level=4, body=6,
)


def _yard() -> Scene:
    return Scene(
        id="yard", name="yard", bounds=SceneBounds(0, 0, 0, 20, 20, 4),
        surfaces=[Surface(id="g", name="g",
                          polygon_xy=[(0, 0), (20, 0), (20, 20), (0, 20)],
                          elevation_m=0.0, surface_type="ground",
                          cover_level=0, is_supporting=True)],
        walls=[WALL], hazards=[], ambient=AmbientConditions(),
    )


def test_short_of_the_wall_stays_on_the_near_side():
    x, y = short_of_the_wall((1.0, 5.0), (5.0, 5.0))
    assert x == 5.0 - WALL_FACE_CLEARANCE_M and y == 5.0


def test_short_of_the_wall_never_goes_behind_the_start():
    # Already closer than the clearance: he stays where he was.
    assert short_of_the_wall((4.999, 5.0), (5.0, 5.0)) == (4.999, 5.0)


def test_a_runner_into_a_wall_is_seen_from_his_own_side():
    out = movement_reach("running", Position(1, 5, 0), Position(9, 5, 0),
                         20.0, _yard())
    assert out.reachable is False
    assert out.landing.x < 5.0
    friend, foe = Position(1, 2, 0), Position(9, 2, 0)
    assert line_of_sight_clear(friend, out.landing, [WALL])
    assert not line_of_sight_clear(foe, out.landing, [WALL])

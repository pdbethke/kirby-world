"""cover_spots: where a man can take cover, from whom, and can he get there.

Lifted from the wall loops in kirby-combat's enumeration (Hide) and Brief
(sightings), which each walked `scene.walls` on their own. The cover level
is 6E2 p.45's "behind cover" fact, computed per threat.
"""
from __future__ import annotations

from kirby_world import AmbientConditions, Furnishing, Position, Scene, SceneBounds, Wall
from kirby_world.cover import CoverSpot, cover_spots


def _scene(*, walls=(), furnishings=()) -> Scene:
    return Scene(
        id="s", name="S", bounds=SceneBounds(0, 0, 0, 60, 60, 10),
        surfaces=[], walls=list(walls), hazards=[],
        ambient=AmbientConditions(), combatant_positions={},
        furnishings=list(furnishings),
    )


def _wall_at_x(x: float, *, height: float = 3.0) -> Wall:
    return Wall(
        id="w", name="Wall",
        segment=(Position(x, 0.0, 0.0), Position(x, 10.0, 0.0)),
        height_m=height,
    )


HERE = Position(0.0, 5.0, 0.0)
THREAT = {"t": Position(30.0, 5.0, 0.0)}


def test_a_wall_between_him_and_the_threat_is_a_spot():
    spots = cover_spots(
        _scene(walls=[_wall_at_x(10.0)]),
        from_pos=HERE, threats=THREAT, reach_m=20.0, mode="running",
    )
    assert len(spots) == 1
    s = spots[0]
    assert isinstance(s, CoverSpot)
    assert s.feature_id == "w"
    assert s.blocks_los is True
    assert s.cover_by_threat == {"t": 4}
    assert s.reachable_this_phase is True


def test_a_furnishing_counts_once_not_four_times():
    car = Furnishing(
        id="car", name="Automobile",
        polygon_xy=[(10.0, 3.0), (14.0, 3.0), (14.0, 7.0), (10.0, 7.0)],
        height_m=1.5, material="wooden wall",
    )
    scene = _scene(furnishings=[car])
    spots = cover_spots(
        scene, from_pos=HERE, threats=THREAT, reach_m=20.0, mode="running",
    )
    assert [s.feature_id for s in spots] == ["car"]
    assert spots[0].blocks_los == car.blocks_los
    assert spots[0].cover_by_threat["t"] > 0


def test_out_of_reach_is_listed_but_not_reachable():
    spots = cover_spots(
        _scene(walls=[_wall_at_x(13.0)]),
        from_pos=HERE, threats=THREAT, reach_m=5.0, mode="running",
    )
    assert len(spots) == 1
    assert spots[0].distance_m > 5.0
    assert spots[0].reachable_this_phase is False


def test_no_cover_from_anyone_is_not_a_spot():
    # A short wall lying along the line of fire: standing beside it, the
    # shot still comes straight in, so it shields him from nobody.
    along = Wall(id="along", name="Along",
                 segment=(Position(10.0, 5.0, 0.0), Position(12.0, 5.0, 0.0)),
                 height_m=3.0)
    spots = cover_spots(
        _scene(walls=[along]),
        from_pos=HERE, threats=THREAT, reach_m=20.0, mode="running",
    )
    assert spots == []


def test_best_cover_across_threats_sorts_first():
    near = Wall(id="near", name="Near",
                segment=(Position(5.0, 0.0, 0.0), Position(5.0, 10.0, 0.0)),
                height_m=3.0, cover_level=2, blocks_movement=False)
    far = _wall_at_x(12.0)
    spots = cover_spots(
        _scene(walls=[near, far]),
        from_pos=HERE, threats=THREAT, reach_m=20.0, mode="running",
    )
    assert [s.feature_id for s in spots] == ["w", "near"]


def test_the_fold_keeps_the_edge_he_can_reach():
    # A wagon with the threat to the east and the man north of it. The
    # nearest edge's standoff lands INSIDE the footprint (4, 1): equal
    # cover, nearer, and unreachable. The old per-edge loop offered the
    # west edge at (2, 0), which he can walk to; the fold must keep that.
    wagon = Furnishing(
        id="wagon", name="Hay wagon",
        polygon_xy=[(3.0, -2.0), (5.0, -2.0), (5.0, 2.0), (3.0, 2.0)],
        height_m=1.5, material="wooden wall", body=6, cover_level=3,
    )
    spots = cover_spots(
        _scene(furnishings=[wagon]), from_pos=Position(4.0, 5.0, 0.0),
        threats={"t": Position(10.0, 5.0, 0.0)}, reach_m=6.0, mode="running",
    )
    assert len(spots) == 1
    assert spots[0].reachable_this_phase is True
    assert (spots[0].position.x, spots[0].position.y) == (2.0, 0.0)


def test_cover_he_can_reach_outranks_better_cover_he_cannot():
    near = Wall(id="near", name="Near",
                segment=(Position(5.0, 0.0, 0.0), Position(5.0, 10.0, 0.0)),
                height_m=3.0, cover_level=2)
    far = _wall_at_x(13.0)
    spots = cover_spots(
        _scene(walls=[near, far]),
        from_pos=HERE, threats=THREAT, reach_m=5.0, mode="running",
    )
    assert [s.feature_id for s in spots] == ["near", "w"]
    assert [s.reachable_this_phase for s in spots] == [True, False]

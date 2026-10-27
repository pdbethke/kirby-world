"""Falling — support check, falling damage, landing resolution.

Falling damage is 6E2 p.142: a Short Fall (20m or less) does 1d6 per full 2m
fallen; a Long Fall (21m or more) does 1d6 per 2m/Segment of VELOCITY at impact,
read off the Falling Table (+10m velocity each Segment, applied before the
move, to a 60m maximum, so a fall never does more than 30d6).
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_world.geometry import point_in_polygon_xy
from kirby_world.scene import Position, Scene, Surface


@dataclass(frozen=True)
class FallingResult:
    combatant_id: str
    from_pos: Position
    landed_at: Position
    fall_distance_m: float
    damage_dice: int         # normal damage dice, vs PD


def is_supported_at(pos: Position, scene: Scene) -> bool:
    """True if any supporting surface — authored or a derived wall top — exists at pos.z within the combatant's xy-footprint.

    Simplified: a combatant's footprint is just its xy point. A surface supports
    iff point_in_polygon_xy(pos.xy, surface.polygon_xy) AND surface.elevation_m == pos.z
    AND surface.is_supporting.
    """
    for surf in scene.supporting_surfaces():
        if not surf.is_supporting:
            continue
        if abs(surf.elevation_m - pos.z) > 1e-6:
            continue
        if point_in_polygon_xy((pos.x, pos.y), surf.polygon_xy):
            return True
    return False


SHORT_FALL_MAX_M = 20
GRAVITY_M_PER_SEGMENT = 10
MAX_FALL_VELOCITY_M = 60


def impact_velocity(fall_distance_m: float) -> int:
    """The Falling Table (6E2 p.142): velocity in m/Segment when a fall of this
    length strikes the ground. Gravity adds 10m each Segment before the move,
    and velocity stops rising at 60m/Segment."""
    velocity = fallen = 0
    while fallen < fall_distance_m:
        velocity = min(velocity + GRAVITY_M_PER_SEGMENT, MAX_FALL_VELOCITY_M)
        fallen += velocity
    return velocity


def compute_falling_damage(fall_distance_m: float) -> int:
    """Normal Damage dice for a fall (6E2 p.142).

    Short Fall (20m or less): 1d6 per full 2m fallen ("a four-story building
    16m high would take 8d6"). Long Fall (21m or more): 1d6 per 2m/Segment of
    velocity at impact ("hitting the ground at a velocity of 50m takes 25d6").
    """
    if fall_distance_m <= SHORT_FALL_MAX_M:
        return int(fall_distance_m // 2)
    return impact_velocity(fall_distance_m) // 2


def _highest_supporting_surface_below(pos: Position, scene: Scene) -> Surface | None:
    """Return the supporting surface with the highest elevation that:
    - is below pos.z
    - contains pos.xy in its polygon
    - is_supporting is True
    """
    candidates = [
        s for s in scene.supporting_surfaces()
        if s.is_supporting
        and s.elevation_m < pos.z
        and point_in_polygon_xy((pos.x, pos.y), s.polygon_xy)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda s: s.elevation_m)


def resolve_fall(
    combatant_id: str,
    from_pos: Position,
    scene: Scene,
    gravity_scale: float = 1.0,
) -> FallingResult:
    """Resolve a fall from `from_pos`. Finds the highest supporting surface
    directly below in the xy footprint; landed_at.z = that surface's elevation.
    If no supporting surface below, lands at bounds.min_z (ground level).

    `gravity_scale` multiplies the effective fall distance for damage purposes
    (1.0 = Earth-normal). Lower gravity -> less damage; higher -> more.
    """
    landing_surface = _highest_supporting_surface_below(from_pos, scene)
    if landing_surface is not None:
        landed_z = landing_surface.elevation_m
    else:
        landed_z = scene.bounds.min_z
    landed_at = Position(x=from_pos.x, y=from_pos.y, z=landed_z, facing=from_pos.facing)
    fall_distance = (from_pos.z - landed_z) * gravity_scale
    damage = compute_falling_damage(fall_distance)
    return FallingResult(
        combatant_id=combatant_id,
        from_pos=from_pos,
        landed_at=landed_at,
        fall_distance_m=fall_distance,
        damage_dice=damage,
    )

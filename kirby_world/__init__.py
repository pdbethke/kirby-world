"""kirby-world — places: a World of Scenes, and the geometry inside them.

Pure: no dice, no rulebook engine, no database. A house with five people in
it, and what is reachable from the kitchen, needs nothing else installed.
The fight that may happen in a place lives in kirby-combat, which depends
on this package and never the other way round.
"""
from kirby_world.construct import (
    Construct,
    ConstructEffect,
    construct_from_hazard,
    construct_from_spawn_spec,
    construct_from_wall,
    constructs_containing,
    constructs_in,
)
from kirby_world.movement_legality import mode_requires_support
from kirby_world.occupancy import blocked_by_furnishing, position_of
from kirby_world.scene import (
    AmbientConditions,
    Furnishing,
    Hazard,
    HazardEffect,
    Position,
    Scene,
    SceneBounds,
    Surface,
    Wall,
    is_climbable,
    wall_top_surface,
)
from kirby_world.world import World

__all__ = [
    "AmbientConditions",
    "Construct",
    "ConstructEffect",
    "Furnishing",
    "Hazard",
    "HazardEffect",
    "Position",
    "Scene",
    "SceneBounds",
    "Surface",
    "Wall",
    "World",
    "blocked_by_furnishing",
    "construct_from_hazard",
    "construct_from_spawn_spec",
    "construct_from_wall",
    "constructs_containing",
    "constructs_in",
    "is_climbable",
    "mode_requires_support",
    "position_of",
    "wall_top_surface",
]

"""kirby-world — places: a World of Scenes, and the geometry inside them.

Pure: no dice, no rulebook engine, no database. A house with five people in
it, and what is reachable from the kitchen, needs nothing else installed.
The fight that may happen in a place lives in kirby-combat, which depends
on this package and never the other way round.
"""
from kirby_world.world import World
from kirby_world.occupancy import blocked_by_furnishing, position_of
from kirby_world.scene import (
    Furnishing, Scene, SceneBounds, Surface, Wall, Hazard, HazardEffect,
    Position, AmbientConditions, wall_top_surface, is_climbable,
)
from kirby_world.construct import (
    Construct, ConstructEffect, construct_from_wall, construct_from_hazard,
    constructs_in,
    construct_from_spawn_spec, constructs_containing,
)
from kirby_world.movement_legality import mode_requires_support

__all__ = [
    "World", "position_of", "blocked_by_furnishing", "Furnishing",
    "Scene", "SceneBounds", "Surface", "Wall", "Hazard", "HazardEffect",
    "Position", "AmbientConditions", "wall_top_surface", "is_climbable",
    "Construct", "ConstructEffect", "construct_from_wall", "construct_from_hazard",
    "constructs_in",
    "construct_from_spawn_spec", "constructs_containing",
    "mode_requires_support",
]

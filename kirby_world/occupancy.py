"""Who and what is standing where --- questions a place can answer alone.

Lifted from kirby-combat's `scene/placement.py`, which also commits moves
to a fight's ledger. Recording a move is the fight's business and stayed
there; these two only read the Scene.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kirby_world.scene import Furnishing, Position, Scene


def position_of(scene: Scene | None, combatant_id: str) -> Position | None:
    """Where a combatant is standing, or ``None`` if they are not on the map.

    Not on the map is not the same as at the origin --- a combatant with no
    position is absent from every distance calculation rather than adjacent
    to whoever happens to be at (0, 0, 0).
    """
    if scene is None:
        return None
    return (getattr(scene, "combatant_positions", None) or {}).get(combatant_id)


def blocked_by_furnishing(scene: Scene, pos: Position) -> Furnishing | None:
    """The Furnishing standing on that spot, or None.

    THE QUESTION A LINE COULD NEVER ANSWER. Scenery was a `Wall` --- a
    segment with no width --- so it occupied no ground and nothing could
    refuse a man who walked into it. Measured on the O.K. Corral board,
    where the wagon is a 2 m line: Wyatt stands 0.40 m from it, Virgil
    0.50, Morgan 0.82, all three inside any wagon of a realistic size.

    ABOVE IT IS NOT INSIDE IT. A man on a wagon's bed is standing ON the
    thing, which is the same distinction `Scene.supporting_surfaces`
    already draws for wall tops --- and a furnishing you can walk through
    blocks nobody at any height.
    """
    for f in (getattr(scene, "furnishings", None) or []):
        if not f.blocks_movement:
            continue
        if getattr(pos, "z", 0.0) >= f.height_m:
            continue
        if f.occupies(pos.x, pos.y):
            return f
    return None

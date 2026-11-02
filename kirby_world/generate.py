"""Building the ground — procedural arenas, in the engine.

WHERE THIS CAME FROM AND WHY IT MOVED. This was 254 lines in the parked
kirby-api wrapper (`combat/random_fight/terrain.py`), and its own docstring
made the case for the move: *"PURE: given the same ``random.Random`` this
returns the same arena, and it touches neither the database nor the clock."*
Its whole import list was ``math``, ``random`` and ``dataclasses``. Pure
rules code in a web service is the definition of what this carve-out
exists to relocate.

WHAT CHANGED IN THE MOVE: it builds a real ``Scene`` rather than the dict
payload a persistence layer wanted. The engine's own type is what the loop,
enumeration, cover and line of sight all consume, so emitting anything else
would mean every caller converting before it could fight on the result. A
consumer that needs rows serialises the Scene; that is its job, not this
function's.

THE FINDING THIS FILE CARRIES, which is worth reading before tuning any of
the numbers: an arena where every wall blocks line of sight produces a
fight about the walls. Measured on the seed-1234 run of the first version,
**18 of 37 actions were `attack_construct`** -- the AI saying "I must
destroy the intervening wall to clear a path". That was GOOD PLAY AGAINST A
BAD ARENA, not bad play: combat perception governs targeting, so fighters
that cannot see each other correctly breach instead. The fix was
architectural, not behavioural -- roughly 40% of walls are now low cover
you can see and shoot over, which is what the hand-authored URBAN_ROOFTOP
had and the generator had dropped.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum

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
)

#: How close to a wall segment counts as "inside" it, in metres.
WALL_CLEARANCE_M = 2.0

#: How many times to try placing one fighter before giving up.
PLACEMENT_ATTEMPTS = 50


class ArenaUnplaceable(RuntimeError):
    """A start position or a furnishing could not be found a clear place."""


class ArenaGenerator(str, Enum):
    """Which generator builds the map. REQUIRED, never defaulted.

    kirby-api rebuilds every fight's map from its seed on each reload, so
    changing what a seed builds would silently change every old fight's map.
    The generator is therefore a version the caller names and stores beside
    the seed, and an old fight keeps the one it started with.
    """

    #: The 0.1.1 generator, unchanged: walls, tiers, hazards and nothing to
    #: stand behind. Held to a golden in the tests.
    WALLS_ONLY = "walls_only"
    #: The same draws, then furnishings placed after the start positions.
    WITH_COVER = "with_cover"


def _require_generator(generator) -> ArenaGenerator:
    """A plain string is refused: the enum is the contract, not the spelling."""
    if not isinstance(generator, ArenaGenerator):
        raise TypeError(
            f"generator must be an ArenaGenerator, got {generator!r}; pass "
            f"ArenaGenerator.WALLS_ONLY or ArenaGenerator.WITH_COVER"
        )
    return generator


#: Furniture a WITH_COVER arena is stocked from: (kind, OBJECT_DURABILITY
#: material, footprint length m, footprint width m, height m). Materials are
#: 6E2 p.173 Objects Table rows; the sizes are ours (the table has none).
FURNISHING_KINDS: tuple[tuple[str, str, float, float, float], ...] = (
    ("crates", "furniture, heavy wood", 1.2, 1.2, 1.2),
    ("car", "automobile", 4.5, 1.8, 1.5),
    ("armored_car", "armored car", 5.5, 2.2, 2.2),
    ("barrier", "concrete wall", 3.0, 0.6, 1.0),
    ("tree", "medium tree", 0.8, 0.8, 6.0),
)

#: How far a furnishing keeps from every start position, in metres, edge
#: to edge: a man must not open the fight standing against his cover.
FURNISHING_START_CLEARANCE_M = 2.0


@dataclass(frozen=True)
class Arena:
    """A generated map and the places it is safe to start fighters."""

    scene: Scene
    start_positions: list[tuple[float, float, float]]

    @property
    def name(self) -> str:
        return self.scene.name


def _half_extent(fighter_count: int) -> float:
    """Half the arena's width, sized to the roster.

    A fixed arena crowds eight fighters and strands two.
    """
    return max(20.0, 9.0 * math.sqrt(max(1, fighter_count)))


def _climb_difficulty_for(height_m: float) -> int | None:
    """6E1 p.70: an ORDINARY face needs no Skill, a DIFFICULT one does.

    Difficulty FOLLOWS FROM HEIGHT rather than being rolled beside it.
    Rolling the two independently produced 0.9m parapets that needed
    trained climbing and 9m sheer faces you could scramble untrained ---
    noise, not architecture. Waist-high cover is something you vault; a
    storey of sheer wall is not.
    """
    if height_m <= 1.5:
        return 0
    if height_m <= 4.0:
        return -1
    if height_m <= 7.0:
        return -2
    return -3


def _rect(cx: float, cy: float, hw: float, hh: float) -> list[tuple[float, float]]:
    """A CCW rectangle centred on (cx, cy)."""
    return [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]


def _near_segment(p: tuple[float, float], a: tuple[float, float],
                  b: tuple[float, float]) -> bool:
    """Is ``p`` within ``WALL_CLEARANCE_M`` of segment a-b?"""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay) <= WALL_CLEARANCE_M
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)) <= WALL_CLEARANCE_M


def _in_polygon(p: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    """Ray-cast point-in-polygon."""
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def generate_arena(rng: random.Random, *, fighter_count: int,
                   generator: ArenaGenerator) -> Arena:
    """A new map, sized to the roster and safe to spawn into.

    Deterministic for a given ``rng`` and ``generator``: the same seed builds
    the same arena, which is what makes a generated fight reproducible.

    ``WALLS_ONLY`` draws from ``rng`` in exactly the 0.1.1 order. ``WITH_COVER``
    makes those same draws first and places furnishings afterwards, so it
    adds to the 0.1.1 map and never reshuffles it.

    RULING: the furnishing count is one per two fighters, at least four. It
    is a rule of the generator, not a default, because no caller chooses it:
    a crowd needs more to stand behind, and a duel still needs somewhere to go.
    """
    generator = _require_generator(generator)
    h = _half_extent(fighter_count)
    name = f"random-{rng.getrandbits(24):06x}"

    surfaces = [Surface(
        id="ground", name="ground", polygon_xy=_rect(0.0, 0.0, h, h),
        elevation_m=0.0, surface_type="ground", is_supporting=True,
    )]
    # 1-3 elevated tiers. Elevation is what makes the vantage rules and
    # line-of-sight-vs-height do any work at all.
    tiers: list[Surface] = []
    for i in range(rng.randint(1, 3)):
        tw, th = rng.uniform(0.18, 0.36) * h, rng.uniform(0.18, 0.36) * h
        cx, cy = rng.uniform(-h + tw, h - tw), rng.uniform(-h + th, h - th)
        tier = Surface(
            id=f"tier_{i}", name=f"tier_{i}", polygon_xy=_rect(cx, cy, tw, th),
            elevation_m=round(rng.uniform(3.0, 8.0), 1),
            surface_type="rooftop", is_supporting=True,
        )
        tiers.append(tier)
        surfaces.append(tier)

    walls: list[Wall] = []
    for i in range(rng.randint(2, 6)):
        ax, ay = rng.uniform(-h * 0.85, h * 0.85), rng.uniform(-h * 0.85, h * 0.85)
        ang = rng.uniform(0.0, math.tau)
        length = rng.uniform(6.0, 0.5 * h)
        bx = max(-h, min(h, ax + math.cos(ang) * length))
        by = max(-h, min(h, ay + math.sin(ang) * length))
        # HEIGHT DECIDES COVER-OR-WALL, and the difference drives the whole
        # fight. See the module docstring: all-blocking walls made 18 of 37
        # actions `attack_construct`, because fighters who cannot see each
        # other correctly breach instead of shooting. ~40% low cover.
        low = rng.random() < 0.4
        height = round(rng.uniform(0.9, 1.8), 1) if low else round(rng.uniform(2.5, 9.0), 1)
        walls.append(Wall(
            id=f"{'cover' if low else 'wall'}_{i}",
            name=f"{'cover' if low else 'wall'}_{i}",
            segment=(Position(round(ax, 2), round(ay, 2), 0.0),
                     Position(round(bx, 2), round(by, 2), 0.0)),
            height_m=height,
            blocks_los=not low, blocks_movement=not low,
            cover_level=rng.randint(2, 4),
            # ALWAYS destructible: "smash the cover" is a tactic, and an
            # absent def_value reads as indestructible to the engine.
            def_value=rng.randint(3, 8), body=rng.randint(4, 12),
            walkable_width_m=round(rng.uniform(0.8, 2.0), 1) if rng.random() < 0.5 else 0.0,
            climb_difficulty=_climb_difficulty_for(height),
        ))

    hazards: list[Hazard] = []
    for kind in rng.sample(["deep_pool", "fire_zone"], rng.randint(0, 2)):
        hw, hh = rng.uniform(0.08, 0.18) * h, rng.uniform(0.08, 0.18) * h
        cx, cy = rng.uniform(-h + hw, h - hw), rng.uniform(-h + hh, h - hh)
        if kind == "deep_pool":
            effect, elev = HazardEffect(), (0.0, 2.5)
        else:
            effect = HazardEffect(damage_dice=rng.randint(2, 4), damage_type="energy",
                                  status_inflicted="on_fire")
            elev = (0.0, 3.0)
        hazards.append(Hazard(
            id=kind, name=kind, polygon_xy=_rect(cx, cy, hw, hh),
            elevation_range_m=elev, trigger="every_segment", effect=effect,
        ))

    starts = _start_positions(rng, fighter_count, h, walls, tiers, hazards)
    furnishings: list[Furnishing] = []
    if generator is ArenaGenerator.WITH_COVER:
        furnishings = _furnishings(rng, fighter_count, h, walls, tiers, hazards, starts)
    scene = Scene(
        id=name, name=name,
        bounds=SceneBounds(-h, -h, -5.0, h, h, 20.0),
        surfaces=surfaces, walls=walls, hazards=hazards,
        ambient=AmbientConditions(), combatant_positions={},
        furnishings=furnishings,
    )
    return Arena(scene=scene, start_positions=starts)


def _start_positions(rng, fighter_count, h, walls, tiers, hazards):
    """Evenly spaced on a circle, randomly rotated, nudged until clear.

    Circle placement is what guarantees fighters open APART rather than on
    top of each other.
    """
    radius = 0.7 * h
    offset = rng.uniform(0.0, math.tau)
    starts: list[tuple[float, float, float]] = []
    for i in range(fighter_count):
        base = offset + math.tau * i / fighter_count
        for attempt in range(PLACEMENT_ATTEMPTS):
            # THE SEARCH WIDENS with each attempt. A fixed narrow jitter can
            # never escape a wall lying along the circle at this angle: at 50
            # fixed tries that failed for 0.63% of arenas -- one button press
            # in 160. By the last attempt this sweeps most of the way round.
            spread = 0.06 + 0.06 * attempt
            jitter = rng.uniform(-spread, spread) if attempt else 0.0
            r = radius * (1.0 - 0.010 * attempt)
            x, y = math.cos(base + jitter) * r, math.sin(base + jitter) * r
            if any(_near_segment((x, y), (w.segment[0].x, w.segment[0].y),
                                 (w.segment[1].x, w.segment[1].y)) for w in walls):
                continue
            z = 0.0
            for tier in tiers:
                if _in_polygon((x, y), tier.polygon_xy):
                    z = float(tier.elevation_m)
            if any(hz.elevation_range_m[0] <= z <= hz.elevation_range_m[1]
                   and _in_polygon((x, y), hz.polygon_xy) for hz in hazards):
                continue
            starts.append((round(x, 2), round(y, 2), z))
            break
        else:
            raise ArenaUnplaceable(
                f"no clear start position for fighter {i} after "
                f"{PLACEMENT_ATTEMPTS} attempts"
            )
    return starts


def _furnishing_count(fighter_count: int) -> int:
    """One piece per two fighters, at least four (the RULING above)."""
    return max(4, fighter_count // 2)


def _footprint(cx: float, cy: float, length: float, width: float,
               angle: float) -> list[tuple[float, float]]:
    """A CCW rectangle of length x width centred on (cx, cy), turned by angle."""
    c, s = math.cos(angle), math.sin(angle)
    corners = [(-length / 2, -width / 2), (length / 2, -width / 2),
               (length / 2, width / 2), (-length / 2, width / 2)]
    return [(round(cx + x * c - y * s, 2), round(cy + x * s + y * c, 2))
            for x, y in corners]


def _segment_distance(p: tuple[float, float], a: tuple[float, float],
                      b: tuple[float, float]) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _polygons_overlap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    """Whether two footprints share ground.

    Corner containment both ways, plus the centre of each: sufficient for
    the convex, roughly-square pieces and zones placed here, and it keeps
    this on the engine's own containment test rather than a second
    intersection routine.
    """
    def centre(poly):
        return (sum(x for x, _ in poly) / len(poly), sum(y for _, y in poly) / len(poly))

    return (any(_in_polygon(p, b) for p in [*a, centre(a)])
            or any(_in_polygon(p, a) for p in [*b, centre(b)]))


def _furnishings(rng, fighter_count, h, walls, tiers, hazards, starts):
    """Place the cover: crates, cars, barriers and trees on the open ground.

    Each piece keeps FURNISHING_START_CLEARANCE_M from every start, off the
    hazards and the raised tiers (a car does not stand on a rooftop drawn at
    ground level), clear of walls and of the pieces already placed. Ids
    follow placement order, so a seed names its furniture the same way each
    time.
    """
    placed: list[Furnishing] = []
    for i in range(_furnishing_count(fighter_count)):
        for _attempt in range(PLACEMENT_ATTEMPTS):
            kind, material, length, width, height = rng.choice(FURNISHING_KINDS)
            cx, cy = rng.uniform(-h * 0.9, h * 0.9), rng.uniform(-h * 0.9, h * 0.9)
            polygon = _footprint(cx, cy, length, width, rng.uniform(0.0, math.pi))
            reach = math.hypot(length, width) / 2.0
            if any(max(abs(x), abs(y)) > h for x, y in polygon):
                continue
            if any(math.hypot(sx - cx, sy - cy) < reach + FURNISHING_START_CLEARANCE_M
                   for sx, sy, _z in starts):
                continue
            if any(_polygons_overlap(polygon, hz.polygon_xy) for hz in hazards):
                continue
            if any(_polygons_overlap(polygon, t.polygon_xy) for t in tiers):
                continue
            if any(_segment_distance((cx, cy), (w.segment[0].x, w.segment[0].y),
                                     (w.segment[1].x, w.segment[1].y)) < reach + 0.5
                   for w in walls):
                continue
            if any(_polygons_overlap(polygon, f.polygon_xy) for f in placed):
                continue
            placed.append(Furnishing(
                id=f"furnishing_{i}", name=f"{kind}_{i}", polygon_xy=polygon,
                height_m=height, material=material,
            ))
            break
        else:
            raise ArenaUnplaceable(
                f"no clear place for furnishing {i} after {PLACEMENT_ATTEMPTS} attempts"
            )
    return placed


def arena_for(rng: random.Random, combatants, *, generator: ArenaGenerator) -> Scene:
    """A generated Scene with the combatants already standing on it.

    The convenience a caller wants: `generate_arena` decides the ground and
    `_start_positions` decides where people begin, so putting them together
    is not a third decision.
    """
    arena = generate_arena(
        rng, fighter_count=len(list(combatants)), generator=generator,
    )
    for combatant, (x, y, z) in zip(combatants, arena.start_positions):
        arena.scene.combatant_positions[combatant.id] = Position(x, y, z)
    return arena.scene

# Changelog

## 0.2.1

- **A runner stopped by a wall ends on his side of it, not on its line.** A
  man is a point here, and a point on a wall's line is on neither side: every
  sight line to him crossed the wall, so nobody could see him. He now stops
  `WALL_FACE_CLEARANCE_M` (1 cm, a numerical clearance, not a rule) back along
  his own path, never behind where he started.
- New `geometry.short_of_the_wall(start, impact)` and `WALL_FACE_CLEARANCE_M`,
  so kirby-combat's Knockback stops the same way.

## 0.2.0

**BREAKING: `generator` is required on `generate_arena` and `arena_for`.** It is
a keyword-only `ArenaGenerator` with no default; a missing value is a
`TypeError`, and so is a plain string. Every caller must name one.

- `ArenaGenerator.WALLS_ONLY` is the 0.1.1 generator unchanged, held to a golden
  (seeds 1-5, 4 and 31 fighters): a stored `scene_seed` rebuilds the same map.
  A consumer that rebuilds maps from seeds must store the generator beside the
  seed and pass `WALLS_ONLY` for every existing row.
- `ArenaGenerator.WITH_COVER` makes the same draws, then places one furnishing
  per two fighters (at least four): crates, cars, armored cars, concrete
  barriers and trees, off the starts, hazards and tiers. Same seed, a different
  map from `WALLS_ONLY`.
- Needs `kirby-terrain>=0.4.0` for the new Objects Table rows (6E2 p.173).
- The `Furnishing` error for a missing material no longer says the table
  "covers walls, doors and glass".

## 0.1.1

**Long falls take the velocity at impact (6E2 p.142).** `compute_falling_damage`
charged 1d6 per 2m for every fall and capped it at 20d6. A Short Fall (20m or
less) is still 1d6 per full 2m. A Long Fall is now 1d6 per 2m/Segment of velocity
when the faller hits the ground, read off the Falling Table: +10m each Segment, to
60m/Segment, so 30d6 at most. A 50m fall drops from 25d6 to 15d6, a
150m fall is the book's own 25d6, and a fall from orbit is 30d6. New:
`impact_velocity`.

## 0.1.0

Split out of kirby-combat 0.19.0's `kirby_combat/scene/` and
`kirby_combat/world.py`, the files moved unchanged apart from import paths
and three seams where a place had been reaching into a fight:

- `movement_reach` takes `mover_can_move: bool = True` instead of a
  `session`; the caller asks whether the mover is Stunned.
- `constructs_in` takes `damage: Mapping[str, int]` (BODY lost, by object)
  instead of a `session`; the fight folds that from its own event log.
- `Scene.encounter` is typed `object | None`; nothing here reads it.

`position_of` and `blocked_by_furnishing` moved here from combat's
placement module, as `kirby_world.occupancy`; committing a move stays in
the fight. `effects.py` (a hazard's effect on the person in it --- drowning,
Life Support) stayed in kirby-combat: it is a rule about the occupant.

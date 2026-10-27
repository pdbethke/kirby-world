# Changelog

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

# Changelog

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

# kirby-world

Places for the Kirby HERO System platform: a `World` of `Scene`s, and the
geometry inside them — surfaces, walls, furnishings, hazards, constructs,
cover, falling, line of sight and per-mode movement reachability.

A place is not a fight. A house with five people doing chores, and what is
reachable from the kitchen, needs nothing but this package:

```python
from kirby_world import AmbientConditions, Position, Scene, SceneBounds
from kirby_world.movement_legality import movement_reach

house = Scene(id="house", name="Safehouse", bounds=SceneBounds(0, 0, 0, 20, 20, 4),
              surfaces=[], walls=[], hazards=[], ambient=AmbientConditions())
house = house.place_combatant("ana", Position(1.0, 0.0, 0.0))
movement_reach("flight", Position(0, 0, 1), Position(5, 0, 1), 10.0, house).reachable
```

## Where it sits

```
kirby-terrain   what a thing is made of     no deps
kirby-world     places                      -> kirby-terrain
kirby-combat    the fight                   -> kirby-world, kirby-cost, kirby-dice
```

Questions about the person moving rather than the place — is he Stunned,
what has this building already absorbed — belong to the fight. They arrive
here as plain values (`mover_can_move`, a `damage` ledger), never as the
fight itself. `tests/test_a_place_without_a_fight.py` enforces that by
making the fight engine unimportable and building a house anyway.

Split out of kirby-combat at 0.20.0, where `kirby_combat.scene` remains as a
re-export of this package.

## License

PolyForm Noncommercial 1.0.0. Not affiliated with or endorsed by Hero Games.

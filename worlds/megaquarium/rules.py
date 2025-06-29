'''
Rules:

- fish only appear when minimum rank is met
- tank objective only fulfillable if fish are avaiable
- tank objective only fulfillable if large enough tank is available
- tank objective only fulfillable if food sources required by fish are available
- animals can only be rewards for objectives, figure out how to unlock other things separately.
'''
from worlds.generic.Rules import add_rule, set_rule
from BaseClasses import CollectionState
from typing import TYPE_CHECKING, Callable, Dict
from .data import TankWithAnimalsCondition, Animal, Tank, MegaquariumDB, Requirements


def get_animal_requirements(db, animal):
    if not animal.food is None:
        yield [db.food_sources[animal.food].to_item_id()]

    if Requirements.is_tropical in animal.requirements:
        yield list(map(lambda h: h.gameId, db.get_equipment(lambda e: not e.heating is None)))

    if Requirements.is_coldwater in animal.requirements:
        yield list(map(lambda h: h.gameId, db.get_equipment(lambda e: not e.chilling is None)))

    if Requirements.tank_rounded_corners in animal.requirements:
        yield list(map(lambda h: h.gameId, db.get_tanks(lambda t: t.hasRoundedCorners)))

    if Requirements.tank_kriesel in animal.requirements:
        yield list(map(lambda h: h.gameId, db.get_tanks(lambda t: t.isKriesel)))


    return []

def add_objective_ruleset(db,world, conditions,location):
    required_items = []
    for cond in conditions:
        if isinstance(cond, TankWithAnimalsCondition):
            for item, count in cond.items:
                required_items.append(item.to_item_id())
                if isinstance(item, Animal):
                    for req in get_animal_requirements(db,item):
                        required_items.append(req)


    print(location, required_items) 
    set_rule(location, lambda state: state.has_all(required_items, world.player))

def set_rules(db, world):

    def get_entrance(entrance: str):
        return world.multiworld.get_entrance(entrance, world.player)

    def get_location(location: str):
        return world.multiworld.get_location(location, world.player)


    for tank in db.tank_objs.values():
        add_objective_ruleset(db, world, tank.conditions, get_location(tank.location))

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
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from dataclasses import dataclass

from .data import TankWithAnimalsCondition, Animal, Tank, MegaquariumDB, Requirements, MegaquariumItem, AnimalFilter


#TODO, make sure species count is enough
@dataclass
class MQRule:
    items: List[MegaquariumItem]

    def item_ids():
        return map(lambda i: i.item_id(), items)

@dataclass
class MQRuleOr(MQRule):


    def test(self, player: CollectionState):
        if state.has_any(self.item_ids(), player):
            return True
        return False

class MQRuleAll(MQRule):

    def test(self,state: CollectionState, player:int):
        if state.has_all(self.item_ids(), player):
            return True
        return False

@dataclass
class MQRuleAtLeast(MQRule):
    count: int

    def test(self, state:CollectionState, player: int):
        if state.has_from_list(self.item_ids(), player,self.count):
            return True
        return False

class MQRuleSet:
    rules: List[MQRule]

    def test(self, state, player):
        for rule in self.rules:
            if not rule.test(state,player):
                return False




def get_animal_requirements(db, animal):
    if not animal.food is None:
        yield MQRuleOr(db.food_sources[animal.food])

    if Requirements.is_tropical in animal.requirements:
        yield MQRuleOr(db.get_equipment(lambda e: not e.heating is None))

    if Requirements.is_coldwater in animal.requirements:
        yield MQRuleOr(db.get_equipment(lambda e: not e.chilling is None))

    if Requirements.tank_rounded_corners in animal.requirements:
        yield MQRuleOr(db.get_tanks(lambda t: t.hasRoundedCorners))

    if Requirements.tank_kriesel in animal.requirements:
        yield MQRuleOr(db.get_tanks(lambda t: t.isKriesel))


    return []

def add_objective_ruleset(db,world, obj ,location):
    required_items = []
    objective_rank = obj.rank
    for cond in obj.conditions:
        valid_animals = list(db.get_animals(lambda animal: animal.rank <= objective_rank))
        if isinstance(cond, TankWithAnimalsCondition):
            for item, count in cond.items:
                if isinstance(item, MegaquariumItem):
                    required_items.append(item.to_item_id())
                    if isinstance(item, Animal):
                        for req in get_animal_requirements(db,item):
                            required_items.append(MQRuleAll(req))

                elif isinstance(item, AnimalFilter):
                    any_animal = list(filter(lambda a: item.animal_satisfies(a), valid_animals))
                    required_items.append(MQRuleOr(any_animal))
        else:
            print("condition: {cond}")

    print(location, required_items) 
    set_rule(location, lambda state: state.has_all(required_items, world.player))



def set_rules(db, world):

    def get_entrance(entrance: str):
        return world.multiworld.get_entrance(entrance, world.player)

    def get_location(location: str):
        return world.multiworld.get_location(location, world.player)




    for tank in db.tank_objs.values():
        add_objective_ruleset(db, world, tank, get_location(tank.location))

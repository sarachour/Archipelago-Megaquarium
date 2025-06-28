
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from enum import IntEnum, Enum
import pkgutil
import pkg_resources
from dataclasses import dataclass
#from BaseClasses import ItemClassification
from BaseClasses import Location, Entrance, Item, ItemClassification

from .utils import load_json5_data

class MegaquariumLocation(Location):
    game = "Megaquarium"


class MegaquariumItem(Item):
    game = "Megaquarium"


class FishRequirements(Enum):
    is_tropical = "is_tropical"
    dislikes_lights = "dislikes_lights"
    dislikes_congeners = "dislikes_congeners"
    dislikes_conspecifics = "dislikes_conspecifics"
    wimp = "wimp"
    bully = "bully"
    eats_fish = "eats_fish"
    eats_crustaceans = "eats_crustaceans"

class TankRequirements(Enum):
    likes_caves = "likes_caves"
    likes_rocks = "likes_rocks"
    likes_plants = "likes_plants"


class MegaqCondition:
    gameId: str


class MegaqAction:
    pass

@dataclass
class MegaqItem:
    idNo: int
    gameId: str
    itemClass: ItemClassification

    def to_item_id(self)-> str:
        return f"AITEM_{self.gameId}"

    def to_item(self,player) -> Item:
        return MegaquariumItem(name=self.to_item_id(), classification=self.itemClass, code=self.idNo, player=player)


@dataclass(kw_only=True)
class Animal(MegaqItem):
    rank: int
    genus: str
    food: str
    waterQuality: int
    defaultUnlocked: bool
    size: int
    fishRequirements: FrozenSet[str]
    tankRequirements: FrozenSet[str]
    itemClass: ItemClassification = ItemClassification.filler 


    def compatible(self, other) -> bool:
        if FishRequirements.wimp in self.fishRequirements and FishRequirements.bully in other.fishRequirements:
            return False

        if FishRequirements.dislikes_congeners in self.fishRequirements and other.genus == self.genus:
            return False

        return True

@dataclass(kw_only=True)
class Food(MegaqItem):
    food: str
    itemClass: ItemClassification = ItemClassification.filler

@dataclass(kw_only=True)
class Equipment(MegaqItem):
    itemClass: ItemClassification = ItemClassification.filler

    
@dataclass(kw_only=True)
class Tank(MegaqItem):
    itemClass: ItemClassification = ItemClassification.filler




@dataclass
class ReachRankCondition(MegaqCondition):
    rankNo: int
    gameId: str = "reachRankX"

    def to_json(self):
        return {"rank": {"value": self.rankNo, "insert": True}}


@dataclass
class TankWithAnimalsCondition(MegaqCondition):
    items: List[Tuple[MegaqItem, int]]
    filtered: bool = False
    gameId: str = "tankWithXAnimal"


    def required_items():
        return map(lambda x: x[0], self.items)

    def to_json(self):
        tankItems = list(map(lambda arg: {"id":arg[0].gameId,"quantity":arg[1]}, self.items))
        return {"tank": {"hostsMany":tankItems, "insert":True, "filtered":self.filtered} }


@dataclass
class AddMoneyAction(MegaqAction):
    amount: str

    def to_json(self):
        return {"money": self.amount}


@dataclass
class UnlockItemAction(MegaqAction):
    item: str

    def to_json(self):
        return {"unlock": self.item.gameId}

@dataclass 
class VisitLocationAction(MegaqAction):
    locationId: str

    def to_json(self):
        return {"popupMessage": self.locationId}

@dataclass 
class MoveSectionAction(MegaqAction):
    sectionId: str

    def to_json(self):
        return {"moveOnToSection": self.sectionId}


@dataclass
class MegaqTrigger:
    idNo: int
    location: str 
    conditions: List[MegaqCondition]
    actions: List[MegaqAction]

    def to_json(self):
        conds_json = list(map(lambda c: c.to_json(), self.conditions))
        acts_json = list(map(lambda c: c.to_json(), self.actions))
        return {
            "conditions": conds_json,
            "doOnTrigger": acts_json
        }

    def to_location(self, player, region) -> Location:
        return MegaquariumLocation(name=self.location, player=player, parent=region)

@dataclass
class MegaqObjective:
    objectiveId: str
    conditions: List[MegaqCondition]
    

    def to_json(self):
        return {
            "id": self.objectiveId,
            "conditions": list(map(lambda c: c.to_json(), self.conditions))
        }

@dataclass
class Section:
    sectionId: str
    triggers: List[MegaqTrigger]
    reward: MegaqAction 
    doOnComplete: List[MegaqAction]
    objectives: List[MegaqObjective]
    mainSection: bool = True

    def to_json(self):
        return {
            "sectionId": self.sectionId,
            "reward": self.reward.to_json(),
            "mainSection": self.mainSection,
            "objectives": list(map(lambda o: o.to_json(), self.objectives)),
            "triggers": list(map(lambda t: t.to_json(), self.triggers)),
            "doOnComplete": list(map(lambda a: a.to_json(), self.doOnComplete))
        }

'''
Any scenario objectives involving excluded fish are automatically removed.
'''
@dataclass
class UnlockableManager:
    excluded: List[MegaqItem]
    available: List[MegaqItem]


    def to_json(self):
        return {
            "currentResearch": {},
            "unlockedSpecs": list(map(lambda x: x.gameId, self.available)),
            "excludedSpecs": list(map(lambda x: x.gameId, self.excluded))
        }

@dataclass(kw_only=True)
class MegaqScenario:
    startSection: Section
    sections: List[Section]
    startRank: int = -1
    money: int = 10000
    unlockables: UnlockableManager

    def write(self, filename):
        import json5
        MEGAQUARIUM_BASE_MAP = load_json5_data("base_map.json")
        new_save = dict(MEGAQUARIUM_BASE_MAP)
        for sec in self.sections:
            new_save["playerData"]["scenario"]["sections"].append(sec.to_json())

        new_save["playerData"]["scenario"]["startSection"] = self.startSection.sectionId
        
        new_save["playerData"]["unlockableManager"] = self.unlockables.to_json()

        new_save["playerData"]["resources"]["money"] = self.money
        new_save["playerData"]["resources"]["rankNumber"] = self.startRank


        with open(filename,"w") as fh:
            fh.write(json5.dumps(new_save))



class MegaquariumDB:

    def __init__(self):
        self.animals = {}
        self.food_sources = {}
        self.equipment = {}
        self.tanks = {}
        # goals that unlock items
        self.tank_objs= {}
        self.rank_objs= {}

        self.item_groups = {"animals":[], "equipment": [], "food_sources": []}
        self.location_groups = {"tanks":[], "ranks": []}
        self.item_name_to_id = {}
        self.loc_name_to_id = {}

        self.loc_id_to_obj = {}
        self.item_id_to_item = {}
        
        self._count = 1234

    def get_id(self):
        ident = self._count
        self._count += 1
        return ident 

    def add_rank_objective(self, rank: int) -> None:
        idNo = self.get_id()
        location_id = f"ALOC_RANK_{rank}"
        cond = ReachRankCondition(rank)
        act = VisitLocationAction(location_id)
        trigger = MegaqTrigger(idNo=idNo, location=location_id, conditions=[cond], actions=[act])
        self.rank_objs[cond.rankNo] = trigger 
        self.location_groups["ranks"].append(trigger.location)
        self.loc_name_to_id[trigger.location] = trigger.idNo
        self.loc_id_to_obj[trigger.location] =  trigger

    def add_tank_objective(self, tankid:str, conditions: List[MegaqCondition]) -> None:
        idNo = self.get_id()
        location_id = f"ALOC_TANK_{tankid}"
        act = VisitLocationAction(location_id)
        trigger = MegaqTrigger(idNo=idNo, location=location_id, conditions=conditions, actions=[act])
        self.tank_objs[tankid] = trigger
        self.location_groups["tanks"].append(trigger.location)
        self.loc_name_to_id[trigger.location] = trigger.idNo
        self.loc_id_to_obj[trigger.location] =  trigger

    def add_animal(self, animal: Animal) -> None:
        self.animals[animal.gameId] = animal
        self.item_groups["animals"].append(animal.to_item_id())
        self.item_name_to_id[animal.to_item_id()] = animal.idNo
        self.item_id_to_item[animal.to_item_id()] = animal  

    def add_tank(self, tank: Tank) -> None:
        self.food_sources[food_source.gameId] = tank
    
        self.item_groups["tank"].append(tank.to_item_id())
        self.item_name_to_id[tank.to_item_id()] = tank.idNo
        self.item_id_to_item[tank.to_item_id()] = tank 


    def add_food_source(self, food_source: Food) -> None:
        self.food_sources[food_source.gameId] = food_source
    
        self.item_groups["food_sources"].append(food_source.to_item_id())
        self.item_name_to_id[food_source.to_item_id()] = food_source.idNo
        self.item_id_to_item[food_source.to_item_id()] = food_source 


    def add_equipment(self, equipment: Equipment) -> None:
        self.equipment[equipment.gameId] = equipment
        
        self.item_groups["equipment"].append(equipment.to_item_id())
        self.item_name_to_id[equipment.to_item_id()] = equipment.idNo
        self.item_id_to_item[equipment.to_item_id()] = equipment

    def get_objective_by_location_id(self, locid):
        return self.loc_id_to_obj.get(locid, None)

    def get_item_by_item_id(self, itemid):
        return self.item_id_to_item.get(itemid, None)



    def all_items(self,player):
        for animal in self.animals.values():
            yield animal.to_item(player)

        '''
        for equip in self.equipment.values():
            yield equip.to_item(player)

        for tank in self.tanks.values():
            yield tank.to_item(player)

        for food in self.food_sources.values():
            yield food.to_item(player)
        '''
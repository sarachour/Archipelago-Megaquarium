import json
import orjson
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from enum import IntEnum, Enum
import pkgutil
import pkg_resources
import json5 

#from BaseClasses import ItemClassification
from BaseClasses import Location, Entrance, Item, ItemClassification


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


class AnimalData(NamedTuple):
    idNo: int
    gameId: str
    rank: int
    genus: str
    food: str
    waterQuality: int
    defaultUnlocked: bool
    size: int
    fishRequirements: FrozenSet[str]
    tankRequirements: FrozenSet[str]


class Animal(AnimalData):

    def compatible(self,other: AnimalData) -> bool:
        if FishRequirements.wimp in self.fishRequirements and FishRequirements.bully in other.fishRequirements:
            return False

        if FishRequirements.dislikes_congeners in self.fishRequirements and other.genus == self.genus:
            return False

        return True

    def to_item_id(self)-> str:
        return f"AITEM_FISH_{self.gameId}"

    def to_item(self,player) -> Item:
        return MegaquariumItem(name=self.to_item_id(), classification=ItemClassification.filler, code=self.idNo, player=player)

class FoodData(NamedTuple):
    idNo: int
    gameId: str
    food: str


class Food(FoodData):

    def to_item_id(self)-> str:
        return f"AITEM_FOOD_{self.gameId}"

    def to_item(self,player) -> Location:
        return MegaquariumItem(name=self.to_item_id(), classification=ItemClassification.filler, code=self.idNo, player=player)




class EquipmentData(NamedTuple):
    idNo: int
    gameId: str

class Equipment(EquipmentData):

    def to_item_id(self)-> str:
        return f"AITEM_EQUIP_{self.gameId}"

    def to_location(self,player) -> Location:
        return MegaquariumLocation(name=self.to_location_id(), player=player)

    def to_item(self,player) -> Item:
        return MegaquariumItem(name=self.to_item_id(), classification=ItemClassification.filler, code=self.idNo, player=player)


class ReachRankData(NamedTuple):
    idNo: int
    rankNo: int


class ReachRank(ReachRankData):
    def to_location_id(self)-> str:
        return f"ALOC_RANK_{self.rankNo}"

    def to_location(self,player,region) -> Location:
        return MegaquariumLocation(name=self.to_location_id(), player=player, parent=region)

    def to_json(self):
        return {
            "conditions":[
                {"rank":{"value":self.rankNo,"insert":True}}
            ],
            "doOnTrigger":[{"moveOnToSection":self.to_location_id()}],
        }


class SectionData(NamedTuple):
    sectionId: str
    triggers: FrozenSet[NamedTuple]


class  Section(SectionData):


    def to_json(self):
        triggers_json = []
        for trig in self.triggers:
            triggers_json.append(trig.to_json())

        return {	
			"sectionId":self.sectionId,
			"reward":{"money":10000},
			"mainSection":True,
			"doOnStart":[],
			"objectives":[
				{
					"id":"reachRankX",
					"conditions":[
						{"rank":{"value":12,"insert":True}}
					]
				},
			],
			"triggers":triggers_json,
            "doOnComplete":[{"money":10000}]	
		}



class MegaquariumDB:

    def __init__(self):
        self.animals = {}
        self.food_sources = {}
        self.equipment = {}
        # goals that unlock items
        self.tank_objs= {}
        self.rank_objs= {}

        self.item_groups = {"animals":[], "equipment": [], "food_sources": []}
        self.location_groups = {"tanks":[], "ranks": []}
        self.item_name_to_id = {}
        self.loc_name_to_id = {}
        self._count = 1234

    def get_id(self):
        ident = self._count
        self._count += 1
        return ident 

    def add_rank_objective(self, rank: ReachRank) -> None:
        self.rank_objs[rank.rankNo] = rank
        self.location_groups["ranks"].append(rank.to_location_id())
        self.loc_name_to_id[rank.to_location_id()] = rank.idNo


    def add_animal(self, animal: AnimalData) -> None:
        self.animals[animal.gameId] = animal
        self.item_groups["animals"].append(animal.to_item_id())
        self.item_name_to_id[animal.to_item_id()] = animal.idNo

    def add_food_source(self, food_source: FoodData) -> None:
        self.food_sources[food_source.gameId] = food_source
    
        self.item_groups["food_sources"].append(food_source.to_item_id())
        self.item_name_to_id[food_source.to_item_id()] = food_source.idNo


    def add_equipment(self, equipment: EquipmentData) -> None:
        self.equipment[equipment.gameId] = equipment
        
        self.item_groups["equipment"].append(equipment.to_item_id())
        self.item_name_to_id[equipment.to_item_id()] = equipment.idNo


    def get_item_groups(self):
        items = {}
        items["animals"] = []
        for animal in self.animals:
            items["animals"].append(animal.to_item())

        items["equipment"] = []
        for equipment in self.equipment:
            items["equipment"].append(equipment.to_item())

    def get_location_groups(self):

        items["food_sources"] = []
        for food_source in self.food_sources:
            items["food_sources"].append(food_source.to_item())


    def all_items(self,player):
        for animal in self.animals.values():
            yield animal.to_item(player)

        for equip in self.equipment.values():
            yield equip.to_item(player)

    def all_locations(self,player):
        for animal in self.animals.values():
            yield animal.to_location(player)

        for equip in self.equipment.values():
            yield equip.to_location(player)

        for food in self.food_sources.values():
            yield food.to_location(player)





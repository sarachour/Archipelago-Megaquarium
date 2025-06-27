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


    def to_location_id(self)-> str:
        return f"ALOC_FISH_{self.gameId}"


    def to_location(self,player) -> Location:
        return MegaquariumLocation(name=self.to_location_id(), player=player)

    def to_item(self,player) -> Item:
        return MegaquariumItem(name=self.to_item_id(), classification=ItemClassification.filler, code=self.idNo, player=player)

class FoodData(NamedTuple):
    idNo: int
    gameId: str
    food: str


class Food(FoodData):

    def to_location_id(self)-> str:
        return f"ALOC_FOOD_{self.gameId}"

    def to_location(self,player) -> Location:
        return MegaquariumLocation(name=self.to_location_id(), )




class EquipmentData(NamedTuple):
    idNo: int
    gameId: str

class Equipment(EquipmentData):

    def to_item_id(self)-> str:
        return f"AITEM_EQUIP_{self.gameId}"


    def to_location_id(self)-> str:
        return f"ALOC_EQUIP_{self.gameId}"

    def to_location(self,player) -> Location:
        return MegaquariumLocation(name=self.to_location_id(), player=player)

    def to_item(self,player) -> Item:
        return MegaquariumItem(name=self.to_item_id(), classification=ItemClassification.filler, code=self.idNo, player=player)



def load_json_data(data_name: str) -> Union[List[Any], Dict[str, Any]]:
    return orjson.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))

def load_json5_data(data_name: str):
    return json5.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))

def load_items_from_json(dataname) -> None:
    items_json = load_json_data(dataname)
    items = {}
    class_map = {"PROGRESSION": ItemClassification.progression, "USEFUL": ItemClassification.useful, "FILLER": ItemClassification.filler, "TRAP": ItemClassification.trap}
    for item_constant_name, attributes in items_json.items():
        item_classification = None
        if attributes["classification"] in class_map:
            item_classification = class_map[attributes["classification"]]
        else:
            raise ValueError(f"Unknown classification {attributes['classification']} for item {item_constant_name}")

        items[item_constant_name] = ItemData(
            attributes["label"],
            item_classification,
            frozenset(attributes["tags"])
        )
    return items


class MegaquariumDB:

    def __init__(self):
        self.animals = {}
        self.food_sources = {}
        self.equipment = {}

        self.item_groups = {"animals":[], "equipment": []}
        self.location_groups = {"animals":[], "equipment": [], "food_sources": []}
        self.item_name_to_id = {}
        self.loc_name_to_id = {}
        self._count = 1234

    def get_id(self):
        ident = self._count
        self._count += 1
        return ident 

    def add_animal(self, animal: AnimalData) -> None:
        self.animals[animal.gameId] = animal
        self.item_groups["animals"].append(animal.to_item_id())
        self.item_name_to_id[animal.to_item_id()] = animal.idNo
        self.location_groups["animals"].append(animal.to_location_id())
        self.loc_name_to_id[animal.to_item_id()] = animal.idNo

    def add_food_source(self, food_source: FoodData) -> None:
        self.food_sources[food_source.gameId] = food_source
    
        self.location_groups["food_sources"].append(food_source.to_location_id())
        self.loc_name_to_id[food_source.to_location_id()] = food_source.idNo


    def add_equipment(self, equipment: EquipmentData) -> None:
        self.equipment[equipment.gameId] = equipment
        
        self.location_groups["equipment"].append(equipment.to_location_id())
        self.loc_name_to_id[equipment.to_location_id()] = equipment.idNo

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




def load_animals_from_json(db,dataname) -> None:
    data = load_json5_data(dataname)
    for json_animal in data["objects"]:
        json_animal_stats = json_animal["animal"]["stats"]
        requirements= []
        if "isTropical" in json_animal_stats:
            requirements.append(FishRequirements.is_tropical)

        if "dislikesLights" in json_animal_stats:
            requirements.append(FishRequirements.dislikes_lights)
         
        if "dislikesCongeners" in json_animal_stats:
            requirements.append(FishRequirements.dislikes_congeners)
        
        if "dislikesConspecifics" in json_animal_stats:
            requirements.append(FishRequirements.dislikes_conspecifics)
        
        if "wimp" in json_animal_stats:
            requirements.append(FishRequirements.wimp)
     
        if "bully" in json_animal_stats:
            requirements.append(FishRequirements.bully)
        
        if "eater" in json_animal_stats:
            if "fishEater" in json_animal_stats["eater"]:
                requirements.append(("eats_fish"))
            if "crustaceanEater" in json_animal_stats["eater"]:
                requirements.append(("eats_crustaceans"))
        

        fishRequirements = requirements

        requirements = []

        if "likesCave" in json_animal_stats:
            requirements.append(("likes_caves", json_animal_stats["likesCave"]["value"]))

        if "likesRocks" in json_animal_stats:
            requirements.append(("likes_rocks", json_animal_stats["likesRocks"]["value"]))

        if "likesPlants" in json_animal_stats:
            requirements.append(("likes_plants", json_animal_stats["likesPlants"]["value"]))

        unlocked_at_start_of_rank = ("unlockedAtStartOfRank" in json_animal["unlockable"])

        tankRequirements = requirements

        ident = db.get_id()
        animal = Animal(idNo=ident, gameId=json_animal["id"], \
            rank=json_animal["unlockable"]["availableLevel"], \
            food=json_animal["animal"]["stats"]["eats"]["item"] if "eats" in json_animal["animal"]["stats"] else None, \
            waterQuality=json_animal["animal"]["stats"]["waterQuality"]["value"], 
            defaultUnlocked=unlocked_at_start_of_rank,
            genus=json_animal["tags"][-1],
            size=json_animal["animal"]["stages"][-1]["size"],
            fishRequirements=fishRequirements,
            tankRequirements=tankRequirements)

        db.add_animal(animal)

def load_food_sources_from_json(db,dataname) -> None:
    data = load_json5_data(dataname)
    for json_food in data["objects"]:
        if not "foodDispenser" in json_food["tags"]:
            continue
        
        ident = db.get_id()
        food = Food(idNo=ident, gameId=json_food["id"],  food=json_food["itemBox"]["items"][0])
        db.add_food_source(food)

def load_equipment_from_json(db,dataname) -> None:
    data = load_json5_data(dataname)
    for json_equipment in data["objects"]:
        ident = db.get_id()
        equipment = Equipment(idNo=ident,gameId=json_equipment["id"])
        db.add_equipment(equipment)


def to_group_set(items: Dict[str, object]) -> Dict[str, Set[str]]:
    ITEM_GROUPS: Dict[str, Set[str]] = {}

    for item in items.values():
        for tag in item.tags:
            if tag not in ITEM_GROUPS:
                ITEM_GROUPS[tag] = set()
            ITEM_GROUPS[tag].add(item.label)

    return ITEM_GROUPS


MEGAQUARIUM_DB = MegaquariumDB()
# load game data into database
load_animals_from_json(MEGAQUARIUM_DB , "animals.data")
load_food_sources_from_json(MEGAQUARIUM_DB, "fishFood.data")
load_equipment_from_json(MEGAQUARIUM_DB, "equipment.data")


MEGAQUARIUM_BASE_MAP = load_json5_data("base_map.json")

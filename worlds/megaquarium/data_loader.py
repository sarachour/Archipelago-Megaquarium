import json
import orjson
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from enum import IntEnum, Enum
import pkgutil
import pkg_resources
import json5 

from .data import MegaquariumDB, FishRequirements, TankRequirements, Animal, Food, Equipment


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

def load_json_data(data_name: str) -> Union[List[Any], Dict[str, Any]]:
    return orjson.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))

def load_json5_data(data_name: str):
    return json5.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))




MEGAQUARIUM_DB = MegaquariumDB()
# load game data into database
load_animals_from_json(MEGAQUARIUM_DB , "animals.data")
load_food_sources_from_json(MEGAQUARIUM_DB, "fishFood.data")
load_equipment_from_json(MEGAQUARIUM_DB, "equipment.data")


MEGAQUARIUM_BASE_MAP = load_json5_data("base_map.json")

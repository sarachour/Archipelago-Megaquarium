import json
import orjson
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from enum import IntEnum, Enum
import pkgutil
import pkg_resources
import json5 

from .data import MegaquariumDB, Requirements, Animal, Food, Equipment, Tank
from .utils import load_json5_data

def existsOrTrue(dicti, field):
    if field in dicti:
        return dicti[field]
    return False

def load_animals_from_json(db,dataname) -> None:
    data = load_json5_data(dataname)
    for json_animal in data["objects"]:
        json_animal_stats = json_animal["animal"]["stats"]
        requirements= []
        if "isTropical" in json_animal_stats:
            requirements.append(Requirements.is_tropical)

        if "dislikesLights" in json_animal_stats:
            requirements.append(Requirements.dislikes_lights)
         
        if "dislikesCongeners" in json_animal_stats:
            requirements.append(Requirements.dislikes_congeners)
        
        if "dislikesConspecifics" in json_animal_stats:
            requirements.append(Requirements.dislikes_conspecifics)
        
        if "wimp" in json_animal_stats:
            requirements.append(Requirements.wimp)
     
        if "bully" in json_animal_stats:
            requirements.append(Requirements.bully)
        
        if "eater" in json_animal_stats:
            if "fishEater" in json_animal_stats["eater"]:
                requirements.append(("eats_fish"))
            if "crustaceanEater" in json_animal_stats["eater"]:
                requirements.append(("eats_crustaceans"))
        

        caves,plants,rocks = 0,0,0
        if "likesCave" in json_animal_stats:
            requirements.append(Requirements.likes_caves)
            caves = json_animal_stats["likesCave"]["value"]

        if "likesRocks" in json_animal_stats:
            requirements.append(Requirements.likes_rocks)
            rocks = json_animal_stats["likesRocks"]["value"]

        if "likesPlants" in json_animal_stats:
            requirements.append((Requirements.likes_plants))
            plants = json_animal_stats["likesPlants"]["value"]

        unlocked_at_start_of_rank = ("unlockedAtStartOfRank" in json_animal["unlockable"])

        tankRequirements = requirements

        ident = db.get_id()
        animal = Animal(idNo=ident, gameId=json_animal["id"], \
            rank=json_animal["unlockable"]["availableLevel"], \
            food=json_animal["animal"]["stats"]["eats"]["item"] if "eats" in json_animal["animal"]["stats"] else None, \
            waterQuality=json_animal["animal"]["stats"]["waterQuality"]["value"], 
            autoUnlock=unlocked_at_start_of_rank,
            genus=json_animal["tags"][-1],
            size=json_animal["animal"]["stages"][-1]["size"],
            requirements=requirements,
            num_rocks=rocks,
            num_plants=plants,
            num_caves=caves)

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

        heating_score = None
        chilling_score= None
        filter_score = None
        light_score = None
        skimming_score = None
        nitrateReactingScore = None
        uvSterilizingScore = None

        if "chemistry" in json_equipment:
            heating_score = json_equipment["chemistry"]["heating"] if "heating" in json_equipment["chemistry"] else None
            chilling_score= json_equipment["chemistry"]["chilling"] if "chilling" in json_equipment["chemistry"] else None
            filter_score = json_equipment["chemistry"]["mechanical"] if "mechanical" in json_equipment["chemistry"] else None
            light_score = json_equipment["chemistry"]["light"] if "light" in json_equipment["chemistry"] else None
            skimming_score = json_equipment["chemistry"]["skimming"] if "skimming" in json_equipment["chemistry"] else None
            nitrate_reacting_score = json_equipment["chemistry"]["nitrateReacting"] if "nitrateReacting" in json_equipment["chemistry"] else None
            uv_sterilizing_score = json_equipment["chemistry"]["uvSterilizing"] if "uvSterilizing" in json_equipment["chemistry"] else None

        equipment = Equipment(idNo=ident, 
            gameId=json_equipment["id"],
            rank=json_equipment["unlockable"]["availableLevel"],    
            autoUnlock=existsOrTrue(json_equipment["unlockable"], "autoUnlock"), 
            heating=heating_score, filtering=filter_score,skimming=skimming_score, 
            light=light_score, nitrateReacting=nitrate_reacting_score, chilling=chilling_score,
            isPump="pump" in json_equipment["tags"])

        db.add_equipment(equipment)

def load_tanks_from_json(db,dataname) -> None:
    data = load_json5_data(dataname)
    for json_tank in data["objects"]:
        ident = db.get_id()
        tank = Tank(idNo=ident,gameId=json_tank["id"], 
            volumePerTile=json_tank["tank"]["volumePerTile"],
            autoUnlock=existsOrTrue(json_tank["unlockable"], "autoUnlock"),
            rank=json_tank["unlockable"]["availableLevel"] if "availableLevel" in json_tank["unlockable"] else None,
            hasRoundedCorners= existsOrTrue(json_tank["tank"], "isRounded"),
            isKriesel = existsOrTrue(json_tank["tank"], "isKreisel"),
            unlockTag=json_tank["id"] if not "unlockedBy" in json_tank["unlockable"] else json_tank["unlockable"]["unlockedBy"])
        db.add_tank(tank)



MEGAQUARIUM_DB = MegaquariumDB()
# load game data into database
load_animals_from_json(MEGAQUARIUM_DB , "animals.data")
load_food_sources_from_json(MEGAQUARIUM_DB, "fishFood.data")
load_equipment_from_json(MEGAQUARIUM_DB, "equipment.data")
load_tanks_from_json(MEGAQUARIUM_DB, "tanks.data")


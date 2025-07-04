
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union 
from enum import IntEnum, Enum
import pkgutil
import pkg_resources
from dataclasses import dataclass
#from BaseClasses import ItemClassification
from BaseClasses import Location, Entrance, Item, ItemClassification

from .utils import load_json5_data

class ArchiMegaquariumLocation(Location):
    game = "Megaquarium"


class ArchiMegaquariumItem(Item):
    game = "Megaquarium"


class Requirements(Enum):
    is_tropical = "is_tropical"
    is_coldwater = "is_coldwater"
    dislikes_lights = "dislikes_lights"
    dislikes_congeners = "dislikes_congeners"
    dislikes_conspecifics = "dislikes_conspecifics"
    wimp = "wimp"
    bully = "bully"
    shoaler = "shoaler"
    eats_fish = "eats_fish"
    eats_crustaceans = "eats_crustaceans"

    likes_caves = "likes_caves"
    likes_rocks = "likes_rocks"
    likes_plants = "likes_plants"
    tank_rounded_corners = "tank_rounded_corners"
    tank_kriesel = "tank_kriesel"

class PointsType(Enum):
    prestige = "Prestige"

class MegaqCondition:
    gameId: str


class MegaqAction:
    pass

@dataclass
class MegaqItem:
    idNo: int
    gameId: str
    name: str
    description: str
    itemClass: ItemClassification
    autoUnlock: bool = False

    def to_item_id(self)-> str:
        return f"AITEM_{self.gameId}"

    def to_item(self,player) -> Item:
        item = ArchiMegaquariumItem(name=self.to_item_id(), classification=self.itemClass, code=self.idNo, player=player, )
        item._hint_text = self.name
        return item


    def __hash__(self):
        return hash(self.gameId)

@dataclass(kw_only=True)
class Animal(MegaqItem):
    rank: int
    nameLatin : str 
    namePlural: str
    genus: str
    food: str
    waterQuality: int
    size: int
    requirements: FrozenSet[str]
    itemClass: ItemClassification = ItemClassification.filler 
    num_rocks: int = 0
    num_plants: int = 0
    num_caves: int = 0

    def _compatible_with(self, other) -> bool:
        IMPLICATIONS = [(Requirements.is_tropical, Requirements.is_tropical), (Requirements.is_coldwater, Requirements.is_coldwater)]
        INCOMPATIBILITIES = [(Requirements.bully, Requirements.wimp)]
        for req1, implies_req1 in IMPLICATIONS:
            if req1 in self.requirements and implies_req1 not in other.requirements:
                return False
        
        for req1, req2 in INCOMPATIBILITIES:
            if req1 in self.requirements and req2 in other.requirements:
                return False
            if req2 in self.requirements and req1 in other.requirements:
                return False


        if (Requirements.dislikes_congeners in self.requirements or Requirements.dislikes_congeners in other.requirements) and other.genus == self.genus:
            return False
        
        if (Requirements.dislikes_conspecifics in self.requirements or Requirements.dislikes_conspecifics in other.requirements) and other.gameId == self.gameId:
            return False

        return True
    
    def compatible_with(self,other) -> bool:
        if isinstance(other, Animal):
            return self._compatible_with(other)
        else:
            return all(map(lambda x: self._compatible_with(x), other))

@dataclass(kw_only=True)
class Food(MegaqItem):
    food: str
    itemClass: ItemClassification = ItemClassification.filler
    rank: int = 0
    foodName: str
    description: str

@dataclass(kw_only=True)
class Equipment(MegaqItem):
    itemClass: ItemClassification = ItemClassification.filler
    rank: int 
    
    chilling: Optional[int] = False
    heating: Optional[int] = False
    filtering: Optional[int] = False
    skimming: Optional[int] = False
    light: Optional[int] = False
    nitrateReacting: Optional[int] = False
    uvSterilizing: Optional[int] = False
    chilling: Optional[int] = False
    isPump:bool = True


@dataclass(kw_only=True)
class Tank(MegaqItem):
    itemClass: ItemClassification = ItemClassification.filler
    rank : int
    volumePerTile: float
    hasRoundedCorners : bool = False
    isKriesel: bool = False
    unlockTag: Optional[str] = None

    def to_item_id(self)-> str:
        return f"AITEM_{self.unlockTag}"


@dataclass(kw_only=True)
class AnimalFilter:
    # filter by genus
    genus: str = None
    # filter by what it eats
    eats: str = None
    # filter by shoaler
    shoaler: bool = False
    # different species
    numSpecies: int = 1


    def trivially_satisfies(self, other):
        satisfied = self.genus == other.genus and \
                self.eats == other.eats and \
                self.shoaler == other.shoaler and \
                self.numSpecies >= other.numSpecies

        # this is an any species tank
        satisfied |= other.genus is None and other.eats is None and \
            not other.shoaler and self.numSpecies >= other.numSpecies

        return satisfied 

    def animal_satisfies(self, anim):
        if not self.genus is None:
            if anim.genus != self.genus:
                return False

        if not self.eats is None:
            if anim.food != self.eats:
                return False

        if self.shoaler:
            if not Requirements.shoaler in anim.requirements:
                return False

        return True
        
    def content_id(self) -> str:
        tagIds = []
        
        for key in ["genus", "eats", "numSpecies"]:
            value = getattr(self, key, None)
            if not value is None:
                tagIds.append(f"{key}-{value}")
        
        for key in ["shoaler"]:
            value = getattr(self, key, None)
            if getattr(self,key, False) is True:
                tagIds.append(f"{key}")


        tags = ":".join(tagIds)

        return f"animFilter:{tags}"


    def to_json(self):
        obj = {}
        obj["tag"] = "animal" if self.genus is None else self.genus
        if not self.numSpecies is None:
            obj["differentSpec"] = True 
            obj["quantity"] = self.numSpecies
        if not self.eats is None:
            assert(not "insertOverride" in obj)
            obj["eats"] = self.eats
            obj["insertOverride"] = self.eats
        if self.shoaler:
            assert(not "insertOverride" in obj)
            obj["shoaler"] = True
            obj["insertOverride"] = "shoaler"
        return obj

@dataclass
class UnlockItemCondition(MegaqCondition):
    item: MegaqItem

    def to_json(self):
        return {"unlocked": {"id": self.item.gameId}}


@dataclass
class ReachRankCondition(MegaqCondition):
    rankNo: int
    gameId: str = "reachRankX"

    def to_json(self):
        return {"rank": {"value": self.rankNo, "insert": True}}


class HavePointsCondition(MegaqCondition):
    points: PointsType
    amount: int

    def to_json(self):
        return {"havePoints": {"id": self.points.name, "quantity": self.amount}}

class TimerCondition(MegaqCondition):
    ticks: int

    def to_json(self):
        return {"timer":{"ticksRemaining": self.ticks, "insert": True}}

# todo, make this an objective that generates objectives, not a condition.
@dataclass
class TankWithAnimalsCondition(MegaqCondition):
    # specific item or fish, or a tag
    items: List[Tuple[Union[MegaqItem, AnimalFilter], int]]
    rank: int
    compatGraph : List[List[Animal]] = None
    filtered: bool = False
    heated: bool = False
    lit: bool = False

    def get_mutually_valid_solution(self,other):
        pset = list(map(lambda xs: set(map(lambda x: x.gameId, xs)), self.compatGraph))
        cset = list(map(lambda xs: set(map(lambda x: x.gameId, xs)), other.compatGraph))
        idmap = {}
        for tank in self.compatGraph + other.compatGraph:
            for anim in tank:
                idmap[anim.gameId] = anim

        result_ids = []
        for cs in cset:
            slns = list(filter(lambda x: len(x) > 0, map(lambda x:  cs.intersection(x), pset)))
            if len(slns) == 0:
                return None
            result_ids += slns 

        result = []
        for tank_ids in result_ids:
            tank = list(map(lambda tank_id: idmap[tank_id], tank_ids))
            result.append(tank)
        return result

    def has_mutually_valid_solution(self,other):
        return not self.get_mutually_valid_solution(other) is None

    def merge(self,other):
        compatTanks = self.get_mutually_valid_solution(other)
        return TankWithAnimalsCondition(
            compatGraph=compatTanks,
            rank=max(self.rank, other.rank),
            items=self.items+other.items,
            filtered=self.filtered or other.filtered, 
            heated=self.heated or other.heated, 
            lit=self.lit or other.lit)

    def trivially_satisfies(self,other):
        for item,qty in other.items:

            satisfied = False
            for item2,qty2 in self.items: 
                if isinstance(item2,AnimalFilter) and isinstance(item,AnimalFilter):
                    satisfied |= item2.trivially_satisfies(item)
                elif isinstance(item2,MegaqItem) and isinstance(item,MegaqItem):
                    satisfied |= (item.gameId == item2.gameId and qty2 >= qty)
            
            if not satisfied:
                return False
        
        if satisfied:
            return True


    def required_items():
        return map(lambda x: x[0], self.items)

    def content_id(self):
        # translate each requirement to a key
        species = list(map(lambda itm: itm[0].gameId if isinstance(itm[0], MegaqItem) else itm[0].content_id(), self.items))
        species.sort()
        species_str = ":".join(species)
        return f"tankWAnimals_{species_str}"

    def generate_progressive_conditions(self):
        for i in range(len(self.items)):
            if isinstance(self.items[i], Animal):
                yield "tankWithXAnimal", TankWithAnimalsCondition(items=items[:i+1])
            else:
                yield "tankWithXDecoration", TankWithAnimalsCondition(rank=self.rank,items=self.items[:i+1])

        if self.filtered:
            yield "tankWithWaterQuality",TankWithAnimalsCondition(rank=self.rank,items=self.items, filtered=self.filtered)
        
        if self.heated:
            yield "tankWithHeating",TankWithAnimalsCondition(rank=self.rank,items=self.items, filtered=self.filtered, heated=self.heated)
         
        if self.lit:
            yield "tankWithSufficientLighting",TankWithAnimalsCondition(rank=self.rank,items=self.items, filtered=self.filtered, heated=self.heated, lit=self.lit)
        

       


    def to_json(self):
        def convert_item(arg):
            if isinstance(arg[0], AnimalFilter):
                return arg[0].to_json()
            else:
                return {"id": arg[0].gameId, "quantity": arg[1]}

        tankItems = list(map(lambda arg: convert_item(arg), self.items))
        data = {"tank": {"hostsMany":tankItems} }
        if self.filtered:
            data["tank"]["isFiltered"] = True
        if self.lit:
            data["tank"]["isLit"] = True
        if self.lit:
            data["tank"]["isHeated"] = True

        data["tank"]["insert"] = True

        return data

@dataclass
class AddMoneyAction(MegaqAction):
    amount: str

    def to_json(self):
        return {"money": self.amount}


@dataclass
class UnlockItemAction(MegaqAction):
    item: str

    def to_json(self):
        if not isinstance(self.item, Tank):
            return {"unlock": self.item.gameId}
        else:
            return {"unlock": self.item.unlockTag}

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

class YouWinAction(MegaqAction):
    def to_json(self):
        return {"youWin": True}

@dataclass
class MegaqTrigger:
    idNo: int
    location: str 
    conditions: List[MegaqCondition]
    actions: List[MegaqAction]
    rank: int

    def to_json(self):
        conds_json = list(map(lambda c: c.to_json(), self.conditions))
        acts_json = list(map(lambda c: c.to_json(), self.actions))
        return {
            "conditions": conds_json,
            "doOnTrigger": acts_json
        }

    def to_location(self, player, region) -> Location:
        return ArchiMegaquariumLocation(name=self.location, player=player, parent=region)

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
class SideObjectiveAvailableAction(MegaqAction):
    sideSectionId: str

    def to_json(self):
        #{"sideObjectiveAvailable":self.sideSectionId}
        return {"sideObjectiveAvailable":self.sideSectionId}


@dataclass
class SideObjectiveStartAction(MegaqAction):
    sideSectionId: str

    def to_json(self):
        #{"sideObjectiveAvailable":self.sideSectionId}
        return {"sideObjectiveStart":self.sideSectionId}

class SponsoredExhibitQuest:
    pass


class TradeQuest:
    want : List[MegaqItem]
    give : List[MegaqItem]



    pass



@dataclass
class Section:
    sectionId: str
    triggers: List[MegaqTrigger] 
    reward: MegaqAction 
    doOnComplete: List[MegaqAction]
    doOnStart: List[MegaqAction]
    objectives: List[MegaqObjective] 
    mainSection: bool = True

    def to_json(self):
        return {
            "sectionId": self.sectionId,
            "reward": self.reward.to_json(),
            "mainSection": self.mainSection,
            "objectives": list(map(lambda o: o.to_json(), self.objectives)),
            "triggers": list(map(lambda t: t.to_json(), self.triggers)),
            "doOnComplete": list(map(lambda a: a.to_json(), self.doOnComplete)),
            "doOnStart": list(map(lambda a: a.to_json(), self.doOnStart))
        }

def createBuildTankSection(name: str, tankRequirements: TankWithAnimalsCondition, reward: MegaqAction, timer: Optional[TimerCondition]=None, mainSection: bool = False ):
    sec = Section(sectionId=name, mainSection=mainSection, reward=reward, doOnComplete=[], doOnStart=[], triggers=[], objectives=[])

    sec.objectives.append(MegaqObjective(objectiveId=f"tankWithParameters", conditions=[]))

    for condName,cond in tankRequirements.generate_progressive_conditions():
        sec.objectives.append(MegaqObjective(objectiveId=condName, conditions=[cond]))
    
    unlockReqs = []
    for req,_ in filter(lambda x: isinstance(x[0], MegaqItem), tankRequirements.items):
        unlockReqs.append(UnlockItemCondition(req))

    if len(unlockReqs) == 0:
        trig = None
    else:
        trig=MegaqTrigger(idNo=-1, location=None, rank=tankRequirements.rank, conditions=unlockReqs, actions=[SideObjectiveAvailableAction(sec.sectionId)])

    return trig,sec


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

        self.item_groups = {"animals":[], "equipment": [], "food_sources": [], "tanks": []}
        self.location_groups = {"tanks":[], "ranks": []}
        self.item_name_to_id = {}
        self.loc_name_to_id = {}

        self.loc_id_to_obj = {}
        self.item_id_to_item = {}
        
        self._count = 1234

    def num_items(self):
        return len(list(self.item_id_to_item.keys()))

    def num_locations(self):
        return len(list(self.loc_id_to_obj.keys()))

    def get_id(self):
        ident = self._count
        self._count += 1
        return ident 

    def add_tank_objective(self, tankid:str, rank: int, conditions: List[MegaqCondition]) -> None:
        idNo = self.get_id()
        # TODO: objective, not trigger
        location_id = f"ALOC_TANK_{rank}_{tankid}"
        act = VisitLocationAction(location_id)
        trigger = MegaqTrigger(idNo=idNo, location=location_id, conditions=conditions+[ReachRankCondition(rank)], rank=rank,  actions=[act])
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
        self.tanks[tank.gameId] = tank
    
        self.item_groups["tanks"].append(tank.to_item_id())
        self.item_name_to_id[tank.to_item_id()] = tank.idNo
        self.item_id_to_item[tank.to_item_id()] = tank 


    def add_food_source(self, food_source: Food) -> None:
        assert(not food_source.food in self.food_sources), f"Food source {food_source.food} already exists in database"
        self.food_sources[food_source.food] = food_source
    
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



    def all_items(self):
        for animal in self.animals.values():
            yield animal

        for equip in self.equipment.values():
            yield equip

        for tank in self.tanks.values():
            yield tank

        for food in self.food_sources.values():
            yield food

    def get_items(self,filterfn=None):
        if not filterfn is None:
            return filter(lambda it: filterfn(it), self.all_items())
        else:
            return self.all_items()

    def get_equipment(self,filterfn):
        if filterfn is None:
            return self.equipment.values()
        else:
            return filter(lambda e: filterfn(e), self.equipment.values())



    def get_tanks(self,filterfn=None):
        if filterfn is None:
            return self.tanks.values()
        else:
            return filter(lambda e: filterfn(e), self.tanks.values())

    def get_animals(self, filterfn=None):
        if filterfn is None:
            return self.animals.values()
        else:
            return filter(lambda e: filterfn(e), self.animals.values())
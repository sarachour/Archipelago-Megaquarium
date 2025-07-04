from collections import Counter
import copy
import logging
import os
import pkgutil
from typing import Any, Set, List, Dict, Optional, Tuple, ClassVar, TextIO, Union

from BaseClasses import CollectionState, ItemClassification, MultiWorld, Tutorial, LocationProgressType
from Fill import FillError, fill_restrictive
from Options import OptionError, Toggle
import settings
from worlds.AutoWorld import WebWorld, World
from Options import (Choice, DeathLink, DefaultOnToggle, OptionSet, NamedRange, Range, Toggle, FreeText,
                     PerGameCommonOptions, OptionGroup, StartInventory)
from BaseClasses import CollectionState, ItemClassification, Region
from .data_loader import MEGAQUARIUM_DB
from .data import Section, UnlockItemAction, AddMoneyAction, MegaqObjective, ReachRankCondition, UnlockableManager, MegaqScenario, TankWithAnimalsCondition, ArchiMegaquariumLocation, MoveSectionAction, SideObjectiveAvailableAction, Tank, ArchiMegaquariumItem, YouWinAction, createBuildTankSection 
import random

from .randomizer import random_tank, generate_random_tank_set
from .rules import set_rules 
from .options import MegaquariumOptions, OPTION_GROUPS
import itertools

class MegaquariumWebWorld(WebWorld):
    """
    Webhost info for Megaquarium 
    """
    theme = "ocean"

    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to playing Megaquarium with Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["fanciful"]
    )

    tutorials = [setup_en]
    option_groups = [] 



class MegaquariumSettings(settings.Group):
    pass 



class MegaquariumWorld(World):
    game = "Megaquarium"
    web = MegaquariumWebWorld()
    topology_present = True

    settings_key = "megaquarium_settings"
    settings: ClassVar[MegaquariumSettings]

    options_dataclass = MegaquariumOptions 
    options: MegaquariumOptions 

    item_name_to_id = MEGAQUARIUM_DB.item_name_to_id 
    location_name_to_id = MEGAQUARIUM_DB.loc_name_to_id
    item_name_groups : Dict[str, Set[str]] = MEGAQUARIUM_DB.item_groups
    location_name_groups : Dict[str, Set[str]] = MEGAQUARIUM_DB.location_groups

    required_client_version = (0, 4, 6)


    def __init__(self, multiworld, player):
        super(MegaquariumWorld, self).__init__(multiworld, player)

    def _get_unlockable_items(self) -> List[ArchiMegaquariumItem]:
        return MEGAQUARIUM_DB.get_items(lambda it: (it.rank is None or it.rank <= self.max_rank) and not isinstance(it, Tank))

    def generate_early(self) -> None:
        self.unlocked_items_per_rank = 8
        self.min_rank = 1 
        self.max_rank = 6 
        TOTAL_ITEMS = len(list(self._get_unlockable_items()))

        N_RANDOM_TANKS =  TOTAL_ITEMS- self.unlocked_items_per_rank*(self.max_rank-self.min_rank + 1)
        generated_tanks = generate_random_tank_set(MEGAQUARIUM_DB,self.min_rank,self.max_rank, 50)

           
        for i,(content_id,new_tank) in filter(lambda t: t[0] < N_RANDOM_TANKS, enumerate(generated_tanks.items())):
            print(f"TANK {content_id}")
            MEGAQUARIUM_DB.add_tank_objective(tankid=f"tank{i}-{content_id}",rank=new_tank.rank,conditions=[new_tank])

    def create_regions(self) -> None:
        # locations = tanks built with requirement, rank ups, full_grown_fish
        # regions = sections
        # regions = objectives
        menu_region = Region("Menu", self.player, self.multiworld)
        rank_regions = {}
        for i in range(self.min_rank,self.max_rank+1):
            rank_regions[i] = Region(f"Rank {i}", self.player, self.multiworld)
            for idx in range(self.unlocked_items_per_rank):
                free_item = ArchiMegaquariumLocation(self.player, f"FreeItem_R{i}_{idx}", None, rank_regions[i])
                rank_regions[i].locations.append(free_item)

        for tank_obj in MEGAQUARIUM_DB.tank_objs.values():
            region = rank_regions[tank_obj.rank]
            region.locations.append(tank_obj.to_location(self.player,region))


        self.multiworld.regions.extend([menu_region] + list(rank_regions.values()))


    def create_items(self) -> None:
        self.item_pool =  map(lambda it: it.to_item(self.player), 
            self._get_unlockable_items())

        self.multiworld.itempool += self.item_pool 


    def set_rules(self) -> None:
        set_rules(MEGAQUARIUM_DB, self)


    def generate_output(self, output_directory: str) -> None:

        filled_locs = self.multiworld.get_filled_locations(self.player)
        precollected_items = self.multiworld.precollected_items[self.player]
        
        for item in precollected_items:
            item = MEGAQUARIUM_DB.get_item_by_item_id(item)
            unlockables.unlocked.append(item)


        unlockables = UnlockableManager(excluded=[], available=[])
        last_objective = None
        sectionsByRank = {}
        sections = []
        
        for i in range(self.min_rank, self.max_rank + 1):
            obj = MegaqObjective(objectiveId=f"reachRank{i}", conditions=[ReachRankCondition(rankNo=i)])
            if i == self.max_rank:
                reward = YouWinAction()
            else:
                reward = AddMoneyAction(1000)
            rankUpSection = Section(sectionId=f"Reach Rank {i}", triggers=[], reward=reward, doOnStart=[], doOnComplete=[], objectives=[obj])
            rankUpSection.mainSection=True
            sectionsByRank[i] = [rankUpSection]
            if i >= self.min_rank + 1:
                sectionsByRank[i-1][0].doOnComplete.append(MoveSectionAction(rankUpSection.sectionId)) 
            sections.append(rankUpSection)


        for idx,loc in enumerate(filter(lambda loc: loc.item.game == "Megaquarium" and loc.item.player == self.player, filled_locs)):
            if "FreeItem" in loc.name:
                unlockables.available.append(MEGAQUARIUM_DB.get_item_by_item_id(loc.item.name))

            else:
                item = MEGAQUARIUM_DB.get_item_by_item_id(loc.item.name)
                unlockedItem = UnlockItemAction(item)

                objective = MEGAQUARIUM_DB.get_objective_by_location_id(loc.name)
                #objective.actions.append(MoveSectionAction(f"section{idx+1}"))
                trig,sec = createBuildTankSection(f"Tank {idx}", reward=unlockedItem, tankRequirements=objective.conditions[0])
                sec.doOnComplete.append(unlockedItem)
                #obj = MegaqObjective(objectiveId="tankWithXAnimal",conditions=[objective.conditions[0]])
                #sec = Section(sectionId=f"Tank {idx}", mainSection=False, triggers=[], reward=unlockedItem, doOnStart=[], doOnComplete=objective.actions, objectives=[obj])
                sectionsByRank[objective.rank].append(sec)
                unlockables.excluded.append(item)
                sections.append(sec)

                if not trig is None:
                    sectionsByRank[objective.rank][0].triggers.append(trig)
                else:
                    sectionsByRank[objective.rank][0].doOnStart.append(SideObjectiveAvailableAction(sec.sectionId))

        #reachRankX
        campaign = MegaqScenario(startSection=sections[0], sections=sections, unlockables=unlockables, startRank=self.min_rank, money=10000)

        output_file = output_directory + os.path.sep + "archipelago_map.sav"
        campaign.write(output_file)


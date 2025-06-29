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
from .data import Section, UnlockItemAction, AddMoneyAction, MegaqObjective, ReachRankCondition, UnlockableManager, MegaqScenario, TankWithAnimalsCondition, MegaquariumLocation, MoveSectionAction 
import random

from .rules import set_rules 

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
        ["Zunawe"]
    )

    tutorials = [setup_en]
    option_groups = [] 



class MegaquariumSettings(settings.Group):
    pass 


class MegaquariumOptions(PerGameCommonOptions):
    pass

class MegaquariumWorld(World):
    game = "Megaquarium"
    web = MegaquariumWebWorld()
    topology_present = True

    settings_key = "pokemon_emerald_settings"
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
        self.FREE_ITEMS = 30

    def generate_early(self) -> None:


        for i in range(2,12):
            MEGAQUARIUM_DB.add_rank_objective(i)

        random_animals = list(MEGAQUARIUM_DB.animals.keys())
        random.shuffle(random_animals)

        N_RANDOM_TANKS =  150 - self.FREE_ITEMS
        for i in range(N_RANDOM_TANKS):
            target_animal = random_animals[i % len(random_animals)]
            animal = MEGAQUARIUM_DB.animals[target_animal]
            condition = TankWithAnimalsCondition(items=[(animal,1)], filtered=False)
            MEGAQUARIUM_DB.add_tank_objective(tankid=f"tank{i}",conditions=[condition])
        

    def create_regions(self) -> None:
        num_regions = 2
        num_locations = 2
        # locations = tanks built with requirement, rank ups, full_grown_fish
        # regions = sections
        # regions = objectives
        menu_region = Region("Menu", self.player, self.multiworld)
        
        #for rank_obj in MEGAQUARIUM_DB.rank_objs.values():
        #    menu_region.locations.append(rank_obj.to_location(self.player,menu_region))

        for tank_obj in MEGAQUARIUM_DB.tank_objs.values():
            menu_region.locations.append(tank_obj.to_location(self.player,menu_region))


        # 
        N_FREE_LOCS = self.FREE_ITEMS
        print(f"number of free locations: {N_FREE_LOCS}")
        for idx in range(N_FREE_LOCS):
            freeItem = MegaquariumLocation(self.player, f"FreeItem_{idx}", None, menu_region)
            menu_region.locations.append(freeItem)

        self.multiworld.regions.extend([menu_region])

    def create_items(self) -> None:
        self.item_pool =  MEGAQUARIUM_DB.all_items(self.player)
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
        sections = []
        for idx,loc in enumerate(filter(lambda loc: loc.item.game == "Megaquarium" and loc.item.player == self.player, filled_locs)):
            if "FreeItem" in loc.name:
                unlockables.available.append(MEGAQUARIUM_DB.get_item_by_item_id(loc.item.name))

            else:
                item = MEGAQUARIUM_DB.get_item_by_item_id(loc.item.name)
                unlockedItem = UnlockItemAction(item)

                objective = MEGAQUARIUM_DB.get_objective_by_location_id(loc.name)
                objective.actions.append(unlockedItem)
                objective.actions.append(MoveSectionAction(f"section{idx+1}"))
                obj = MegaqObjective(objectiveId="tankWithXAnimal",conditions=[objective.conditions[0]])
                sec = Section(sectionId=f"section{idx}", triggers=[], reward=unlockedItem, doOnComplete=objective.actions, objectives=[obj])
                sec.mainSection = True
                sections.append(sec)

                # make this fish not unlockable via research
                unlockables.excluded.append(item)


        #reachRankX
        sections[0].mainSection = True
        campaign = MegaqScenario(startSection=sections[0], sections=sections, unlockables=unlockables, startRank=10, money=10000)

        output_file = output_directory + os.path.sep + "archipelago_map.sav"
        campaign.write(output_file)


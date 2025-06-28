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
from .data_loader import MEGAQUARIUM_DB, MEGAQUARIUM_BASE_MAP
from .data import Section, ReachRank


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


def set_rules(world: "MegaquariumWorld") -> None:
    """
    Set rules for Megaquarium.
    """
    pass 



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

    def generate_early(self) -> None:
        for i in range(2,12):
            idx = MEGAQUARIUM_DB.get_id()
            MEGAQUARIUM_DB.add_rank_objective(ReachRank(idNo=idx, rankNo=i))

        

    def create_regions(self) -> None:
        num_regions = 2
        num_locations = 2
        # locations = tanks built with requirement, rank ups, full_grown_fish
        # regions = sections
        # regions = objectives
        menu_region = Region("Menu", self.player, self.multiworld)
        for rank_obj in MEGAQUARIUM_DB.rank_objs.values():
            menu_region.locations.append(rank_obj.to_location(self.player,menu_region))


        self.multiworld.regions.extend([menu_region])

    def create_items(self) -> None:
        self.item_pool = []
        for item in MEGAQUARIUM_DB.all_items(self.player):
            self.item_pool.append(item)

        self.multiworld.itempool += self.item_pool


    def set_rules(self) -> None:
        set_rules(self)


    def generate_output(self, output_directory: str) -> None:
        import json5
        output_file = output_directory + os.path.sep + "archipelago_map.sav"

        filled_locs = self.multiworld.get_filled_locations(self.player)
        precollected_items = self.multiworld.precollected_items[self.player]
        print(filled_locs)
        print(precollected_items)

        sec = Section("mainSection", triggers=list(map(lambda x: x, MEGAQUARIUM_DB.rank_objs.values())))

        new_save = dict(MEGAQUARIUM_BASE_MAP)
        new_save["playerData"]["scenario"]["sections"].append(sec.to_json())
        new_save["playerData"]["scenario"]["startSection"] = sec.sectionId

        with open(output_file,"w") as fh:
            fh.write(json5.dumps(MEGAQUARIUM_BASE_MAP))

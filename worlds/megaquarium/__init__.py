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
from .data import MEGAQUARIUM_ITEM_GROUPS, MEGAQUARIUM_LOCATION_GROUPS 


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

    item_name_to_id = {} 
    location_name_to_id = {} 
    item_name_groups : Dict[str, Set[str]] = MEGAQUARIUM_ITEM_GROUPS
     
    location_name_groups : Dict[str, Set[str]] = MEGAQUARIUM_LOCATION_GROUPS

    required_client_version = (0, 4, 6)


    def __init__(self, multiworld, player):
        super(MegaquariumWorld, self).__init__(multiworld, player)

    def generate_early(self) -> None:
        pass

    def create_regions(self) -> None:
        pass

    def create_items(self) -> None:
        pass

    def set_rules(self) -> None:
        set_rules(self)

import json
import orjson
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
from enum import IntEnum
import pkgutil
import pkg_resources

from BaseClasses import ItemClassification



class ItemData(NamedTuple):
    label: str
    classification: ItemClassification
    tags: FrozenSet[str]


class LocationCategory(IntEnum):
    POINTS = 0
    TANK = 1




class LocationData(NamedTuple):
    name: str
    label: str
    category: LocationCategory
    tags: FrozenSet[str]


def load_json_data(data_name: str) -> Union[List[Any], Dict[str, Any]]:
    return orjson.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))


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


def load_locations_from_json(dataname) -> None:
    items_json = load_json_data(dataname)

    return {}

def to_group_set(items: Dict[str, object]) -> Dict[str, Set[str]]:
    ITEM_GROUPS: Dict[str, Set[str]] = {}

    for item in items.values():
        for tag in item.tags:
            if tag not in ITEM_GROUPS:
                ITEM_GROUPS[tag] = set()
            ITEM_GROUPS[tag].add(item.label)

    return ITEM_GROUPS



MEGAQUARIUM_ITEMS : Dict[str, ItemData] = load_items_from_json("items.json")
MEGAQUARIUM_LOCATIONS : Dict[str, LocationData] = load_locations_from_json("locations.json")

MEGAQUARIUM_LOCATION_GROUPS = to_group_set(MEGAQUARIUM_LOCATIONS)
MEGAQUARIUM_ITEM_GROUPS = to_group_set(MEGAQUARIUM_ITEMS)
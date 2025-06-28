import json
import orjson
import json5 
from typing import Dict, List, NamedTuple, Optional, Set, FrozenSet, Tuple, Any, Union
import pkgutil

def load_json_data(data_name: str) -> Union[List[Any], Dict[str, Any]]:
    return orjson.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))

def load_json5_data(data_name: str):
    return json5.loads(pkgutil.get_data(__name__, "data/" + data_name).decode("utf-8-sig"))


# Auxiliary module for setting and getting module symble table.
from typing import Dict

type_map: Dict = {}

def setTypeMap(tmap: Dict) -> None:
    global type_map
    type_map = tmap

def getTypeMap() -> Dict:
    return type_map

from . import data_types, functions
from ..types import Dict

# add builtin data types and functions to global symbol table.
def add_to_type_map(type_map: Dict) -> None:
    data_types.add_to_type_map(type_map)
    functions.add_to_type_map(type_map)

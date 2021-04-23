import ast
from typing import Dict, List, Any as AnyType

from . import imports
from collections import namedtuple
from . import scope

DEBUG = True
srcdata = namedtuple('srcdata', ['src', 'filename'])

# return the ast of the file object.
def parse_module(input: AnyType) -> AnyType:
    """ Parse a Python source file and return it with the source info package (used in error handling)"""
    src = input.read()
    return ast.parse(src), srcdata(src=src, filename=input.name)

def check(file_, module_env=None) -> None:
    pass

# return the symbol table string representation.
def getTypeMapInfo(type_map: Dict) -> Dict:
    temp = ""
    for super_namespace in type_map.current_namespace.iter_super_namespaces():
        for key in super_namespace.keys():
            temp += key
            temp += " : "
            temp += repr(super_namespace[key])
            temp += '\n'

    return temp

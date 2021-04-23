"""
convert collected types to self-defined types. So we can type check these types.
"""
from typing import List, Dict, Any as AnyType

from .builtins import data_types
from .types import Dict, List, Set, Tuple, FuncType, Union
from .coordinator.typemap import getTypeMap
from .coordinator.union_type import UnionType
from collections import abc
import logging

# convert string-formatted types to self-defined basic types.
builtin_types: Dict = {
    'bool': data_types.Bool,
    'int': data_types.Int,
    'float': data_types.Float,
    'complex': data_types.Complex,
    'bytes': data_types.Bytes,
    'None': data_types.None_,
    'str': data_types.Str,
    'dict': Dict,
    'list': List,
    'set': Set,
    'tuple': Tuple,
}

# Union type:
# <<{dict | str}>>  
# <<ValidationError -> {ErrorDefinition | str}>>
# <<{() | str}>>
# <<{? | str}>> <<PARAMETER>>
# <<{({? | str}, ?) | str}>> <<PARAMETER>>
# {<UnconcernedValidator> | <Validator>}
# {<date> | <datetime> | <dict> | <float> | <int> | <str> | <time> | <timedelta> | ? -> bool}
# {<float> | <str> | ? -> ? | ? -> ? | ? -> ? | ? -> list}

# convert Union string representation to our builtin Union type.
def convertUnion(type_map: Dict, prob_type: str, node: AnyType) -> UnionType:
    prob_type = prob_type.strip('{}')
    tlist = prob_type.split('|') if "|" in prob_type else prob_type.split("|")
    tlist[:] = [t.strip(" ") for t in tlist]
    tlist[:] = [t.strip("<>") for t in tlist]
    elts = []    
    for telt in tlist:
        elt = getConcretType(type_map, telt, node)
        elts.append(elt)
    return Union(type_map, elts)

# convert Any String representation type to our builtin types in symbol table.
def getConcretType(type_map: Dict, prob_type: str, node: AnyType) -> AnyType:
    type_map = getTypeMap()
    if isinstance(prob_type, data_types.Any):
        return prob_type
    elif prob_type is data_types.Any or prob_type == 'Any':
        return data_types.Any()
    elif prob_type == 'defaultdict' or prob_type == 'dict' or prob_type == "{}" or prob_type == {}:
        return Dict(type_map, [], [])
    elif prob_type == "[]" or "[]" in prob_type:
            return builtin_types['list']
    elif '[' in prob_type and ']' in prob_type:
        elts_types = []
        prob_type = prob_type.strip("[]")
        elts = prob_type.split(', ')

        for elt in elts:
            if elt == '?':
                elts_types.append(data_types.Any())
            elif elt in builtin_types:
                elts_types.append(builtin_types[elt])
            else:
                elts_types.append(elt)
        return List(type_map, elts_types)
    
    elif isinstance(prob_type, list) or isinstance(prob_type, tuple):
        new_types = []
        
        for t in prob_type:
            if t in builtin_types:
                new_types.append(builtin_types[t])
            else:
                new_types.append(t)
        if not new_types:
            if isinstance(prob_type, list):
                return builtin_types['list']
            if isinstance(prob_type, tuple):
                return builtin_types['tuple']
        else:
            if isinstance(prob_type, list):
                return List(type_map, new_types)
            if isinstance(prob_type, tuple):
                return Tuple(type_map, new_types)
        return new_types
    elif prob_type == "()":
            return builtin_types['tuple']
    elif '(' in prob_type and ')' in prob_type:
        elts_types = []
        prob_type = prob_type.strip("()")
        elts = prob_type.split(', ')

        for elt in elts:
            if elt == '?':
                elts_types.append(data_types.Any())
            elif elt in builtin_types:
                elts_types.append(builtin_types[elt])
            else:
                elts_types.append(elt)
        return Tuple(type_map, elts_types)
    elif isinstance(prob_type, UnionType):
        return Union(type_map, prob_type.elts, prob_type.probs)
    elif isinstance(prob_type, str) and prob_type.startswith("{") and prob_type.endswith("}") or "|" in prob_type:
        return convertUnion(type_map, prob_type, node)
    elif '->' in prob_type:
        params, r_type, *rest = prob_type.split('->')
        params = params.strip()
        params = params.strip("()")
        args = params.split(', ')
        p_types = []
        for arg in args:
            if arg == '?':
                p_types.append(data_types.Any())
            elif arg in builtin_types:
                p_types.append(builtin_types[arg])
            else:
                p_types.append(arg)
        r_type = r_type.strip()
        
        if r_type in builtin_types:
            r_type = builtin_types[r_type]
        name = node.name if hasattr(node, 'name') else node.id
        return FuncType(name, p_types, r_type, type_map)
    elif prob_type in builtin_types:
        return builtin_types[prob_type]
    elif type_map.in_typemap(prob_type):
        prob_type = type_map.find(prob_type)
        return prob_type
    elif hasattr(abc, prob_type):
        return getattr(abc, prob_type)
    else:
        return prob_type
        

if __name__ == '__main__':
    convertType = getConcretType(None, '{dict | str}', None)

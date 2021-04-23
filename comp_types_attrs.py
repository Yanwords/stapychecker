from .builtins.data_types import (List, Dict, Union, Tuple, Set, None_,  Int, Str, Any, Bool, BaseType as BaseClass)
from .builtins.functions import BuiltinFunction as Fun

basic_attributes: Dict = {
        '__class__': BaseClass,
        '__dir__': Fun('__dir__', [Any], Dict),
        '__doc__': Str,
        '__eq__': Fun('__eq__', [Any], Bool),
        '__format__': Fun('__format__', [Any], Str),
        '__ge__': Fun('__ge__', [Any], Bool),
        '__gt__': Fun('__gt__', [Any], Bool),
        '__hash__': Fun('__hash__', [Any], Int),
        '__le__': Fun('__le__', [Any], Bool),
        '__lt__': Fun('__lt__', [Any], Bool),
        '__ne__': Fun('__ne__', [Any], Bool),
        '__repr__': Fun('__repr__', [Any], Bool),
        '__sizeof__': Fun('__sizeof__', [Any], Int),
        '__str__': Fun('__str__', [Any], Str),
}

function_attributes: Dict = {
        '__annotations__': Dict,
        '__dict__': Dict,
        '__name__': Str,
        '__qualname__': Str,
        '__module__': Str,

}

class_attributes: Dict = {
        '__class__': BaseClass,
        '__dict__': Dict,
        '__module__': Str,
        '__mro__': Tuple,
}

module_attributes: Dict = {
        '__builtins__': Fun('__builtins__', [], Dict),
        '__doc__': Union(None, [Str, None]),
        '__file__': Str,
        '__name__': Str,
        '__package__': Str,
}

list_attributes: Dict = {
        '__add__': Fun('__add__', [List], List),
        '__doc__': Str,
        '__eq__': Fun('__eq__', [List], Bool),
        '__ge__': Fun('__ge__', [List], Bool),
        '__gt__': Fun('__gt__', [List], Bool),
        '__le__': Fun('__le__', [List], Bool),
        '__len__': Fun('__len__', [List], Int),
        '__lt__': Fun('__lt__', [List], Bool),
        '__mul__': Fun('__mul__', [Int], List),
        '__ne__': Fun('__ne__', [List], Bool),
 
        'append': Fun('append', [Any], None_),   
        'copy': Fun('copy', [], List),
        'clear': Fun('clear', [], None_),
        'count': Fun('count', [], Int),
        'extend': Fun('extend', [Any], None_),
        'index': Fun('index', [Any], Any),
        'insert': Fun('insert', [Int, Any], None_),
        'pop': Fun('pop', [Union(None, [Int, None_])], Any),
        'remove': Fun('remove', [Any], None_),
        'reverse': Fun('reverse', [], None_),
        'sort': Fun('sort', [], None_),
}

# add additional attributes for list object to our List type.
_listobj: List = ['l', 'i', 's', 't']
for _attr in dir(_listobj):
    if _attr not in list_attributes:
        list_attributes[_attr] = Any()

dict_attributes: Dict = {
        '__doc__': Str,
        '__eq__': Fun('__eq__', [Dict], Bool),
        '__ge__': Fun('__ge__', [Dict], Bool),
        '__gt__': Fun('__gt__', [Dict], Bool),
        '__le__': Fun('__le__', [Dict], Bool),
        '__len__': Fun('__len__', [Dict], Int),
        '__lt__': Fun('__lt__', [Dict], Bool),
        '__ne__': Fun('__ne__', [Tuple], Bool),
        
        'copy': Fun('copy', [], Dict),
        'clear': Fun('clear', [], None_),
        'fromkeys': Fun('fromkeys', [Any], Dict),
        'get': Fun('get', [Any], Any),
        'items': Fun('items', [], List),
        'keys': Fun('keys', [], List),
        'pop': Fun('pop', [Any], Any),
        'popitem': Fun('popitem', [], Tuple),
        'setdefault': Fun('setdefault', [Any], None_),
        'update': Fun('update', [Any], None_),
        'values': Fun('values', [], List)
}

# add additional attributes for dict object to our Dict type.
_dictobj: Dict = {'di':'ct'}
for _attr in dir(_dictobj):
    if _attr not in dict_attributes:
        dict_attributes[_attr] = Any()

set_attributes: Dict = {
        '__and__': Fun('__and__', [Set], Set),
        '__doc__': Str,
        '__eq__': Fun('__eq__', [Set], Bool),
        '__ge__': Fun('__ge__', [Set], Bool),
        '__gt__': Fun('__gt__', [Set], Bool),
        '__le__': Fun('__le__', [Set], Bool),
        '__len__': Fun('__len__', [Set], Int),
        '__lt__': Fun('__lt__', [Set], Bool),
        '__ne__': Fun('__ne__', [Set], Bool),
        '__or__': Fun('__or__', [Set], Set),
        '__sub__': Fun('__sub__', [Set], Set),
        '__xor__': Fun('__xor__', [Set], [Set]),
 
        'add': Fun('add', [Any], None_),   
        'copy': Fun('copy', [], Set),
        'clear': Fun('clear', [], None_),
        'difference': Fun('difference', [Any], Set),
        'difference_update': Fun('difference_update', [Any], None_),
        'discard': Fun('discard', [Any], None_),
        'intersection': Fun('intersection', [Any], Set),
        'intersection_update' : Fun('intersection_update', [Any], None_),
        'isdisjoint' : Fun('isdisjoint', [Any], Bool),
        'issubset' : Fun('issubset', [Any], Bool),
        'issuperset' : Fun('issuperset', [Any], Bool),
        'pop' : Fun('pop', [], Any),
        'remove': Fun('remove', [Any], None_),
        'symmetric_difference': Fun('symmetric_difference', [Any], Set),
        'symmetric_difference_update': Fun('symmetric_difference_update', [Any], None_),
        'union': Fun('reverse', [Any], Set),
        'update': Fun('update', [Any], None_),
}

# add additional attributes for set object to Set type.
_setobj: Set = {'set'}
for _attr in dir(_setobj):
    if _attr not in set_attributes:
        set_attributes[_attr] = Any()

tuple_attributes: Dict = {
        '__add__': Fun('__add__', [Tuple], Tuple),
        '__doc__': Str,
        '__eq__': Fun('__eq__', [Tuple], Bool),
        '__ge__': Fun('__ge__', [Tuple], Bool),
        '__gt__': Fun('__gt__', [Tuple], Bool),
        '__le__': Fun('__le__', [Tuple], Bool),
        '__len__': Fun('__len__', [Tuple], Int),
        '__lt__': Fun('__lt__', [Tuple], Bool),
        '__mul__': Fun('__mul__', [Int], Tuple),
        '__ne__': Fun('__ne__', [Tuple], Bool),
        
        'count': Fun('count', [], Int),
        'index': Fun('index', [Any], Any),
}

# add additional attributes for tuple object to Tuple type.
_tupleobj: Tuple = ('tu', 'p', 'le')
for _attr in dir(_tupleobj):
    if _attr not in tuple_attributes:
        tuple_attributes[_attr] = Any()

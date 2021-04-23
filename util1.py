# utility moduel for checking the issubclass function.
from typing import List as ListType, Dict as DictType, Any as AnyType, Optional as OptionalType, Union as UnionType, Tuple as TupleType
import ast
AST = ast.AST

from .builtins import data_types
from .exceptions import NotYetSupported, NoSuchAttribute, NotIterable
from .builtins.functions import BuiltinFunction
from .types import (Union, List, Set, Dict, Tuple, BaseType, Class, Instance)
from .builtins.data_types import None_, NoneType
import logging

debug = logging.debug
num_types: ListType = [data_types.Any, data_types.Bool, data_types.Int, data_types.Float, data_types.Complex]
str_types: ListType = [data_types.Any, data_types.Bytes, data_types.Str]
data_type: ListType = [data_types.Any, data_types.BoolType, data_types.IntType,
             data_types.FloatType, data_types.ComplexType,
             data_types.BytesType, data_types.StrType]

# return the module name, and remove the suffix.
def getModuleName() -> str:
    from . import config
    import os
    mname = config.getFileName()
    mname = mname.replace(".pyi", "")
    mname = mname.replace(".py", "")
    mname = mname.replace(os.path.sep + "__init__", "")
    mname = mname.split(os.path.sep)[-1]
    return mname

# return the abbreviated name of the object.
def getName(oper: AST) -> OptionalType[str]:
    if hasattr(oper, 'id'):
        return oper.id
    elif hasattr(oper, 'n'):
        return oper.n
    elif hasattr(oper, 's'):
        return oper.s
    else:
        print(type(oper))
        return None

# check two type if is subtype.
def issub(ftype: BaseType, subtype: BaseType) -> bool:
    # 'here subtype is mytypes.List it should be an instance not a class'
    left = convertType(ftype)
    right = convertType(subtype)
    if left is right:
        return True
    # return True if one type is Any.
    if left is data_types.Any or right is data_types.Any or left is data_types.UnDefined or right is data_types.UnDefined or isinstance(left, data_types.UnDefined) or isinstance(right, data_types.UnDefined):
        return True
    # two types are all builtin data types.
    if left in data_type and right in data_type:
        lindex = data_type.index(left)
        rindex = data_type.index(right)
        return True if lindex >= rindex and rindex >=0 and (lindex < 5 or rindex > 4) \
                     else False
    import types
    # handle the compound types.
    if left is Union or isinstance(left, Union):
        tmp_flag = []
        for item in ftype.elts:
            if not hasattr(item, '__iter__') or item is type:
                continue
            elif hasattr(item, 'iter'):
                _elts = [issub(el, subtype) for el in item]
                if all(_elts):
                    return True
            else:
                #here we must check all the types in the Union :-)
                tmp_flag.append(issub(item, subtype))
        return any(tmp_flag)      
    # check the Tuple type. 
    if left is Tuple or isinstance(left, Tuple):
        if isinstance(ftype, type):
            return isinstance(subtype, type) and (subtype is Tuple or isinstance(subtype, Tuple))
        atype = ftype.elts[0] if ftype.elts else data_types.Any
        atype = [el for el in atype] if hasattr(atype, '__iter__') and isinstance(atype.__iter__, types.MethodType) else atype
        flag = False
        if not hasattr(subtype, 'elts'):
            if hasattr(atype, '__iter__') and isinstance(atype.__iter__, types.MethodType):
                for el in atype:
                    if subtype is el or issub(el, subtype):
                        flag = True
                        break
                    else:
                        flag = False
            elif isinstance(atype, BuiltinFunction):
                if subtype is atype.return_type or issub(atype.return_type, subtype):
                    flag = True
                    return flag
                else:
                    flag = False
            return flag
        if subtype.elts is None:
            return flag
        for item in subtype.elts:
            itype = convertType(item)
            if hasattr(atype, '__iter__') and isinstance(atype, types.MethodType):
                for el in atype:
                    if itype is el or issub(el, item):
                        flag = True
                        break
                    else:
                        flag = False
            elif isinstance(atype, BuiltinFunction):
                if itype is atype.return_type or issub(atype.return_type, item):
                    flag = True
                    break
                else:
                    flag = False

        return flag
    # check the Set type, similar with Tuple type.
    if left is Set or isinstance(left, Set):
        if isinstance(ftype, type):
            return isinstance(subtype, type) and (subtype is Set or isinstance(subtype, Set))
        atype = ftype.elts
        atype = [el for el in atype]
        flag = False
        if not hasattr(subtype, 'elts'):
            if hasattr(atype, '__iter__') and isinstance(atype, types.MethodType):
                for el in atype:
                    if subtype is el or issub(el, subtype):
                        flag = True
                        break
                    else:
                        flag = False
            elif isinstance(atype, BuiltinFunction):
                if subtype is atype.return_type or issub(atype.return_type, subtype):
                    flag = True
                    return flag
                else:
                    flag = False
            return flag
        for item in subtype.elts:
            itype = convertType(item)
            for el in atype:
                if itype is el or issub(el, item):
                    flag = True
                    break
                else:
                    flag = False

        return flag
    # check the List type, similar with Tuple type.
    if left is List or isinstance(left, List):
        if ftype is List or isinstance(ftype, List):
            return True
        atype = ftype.elts
        atype = [el for el in atype]
        flag = False
        if not hasattr(subtype, 'elts'):
            if hasattr(atype, '__iter__') and isinstance(atype, types.MethodType):
                for el in atype:
                    if subtype is el or issub(el, subtype):
                        flag = True
                        break
                    else:
                        flag = False
            elif isinstance(atype, BuiltinFunction):
                if subtype is atype.return_type or issub(atype.return_type, subtype):
                    flag = True
                    return flag
                else:
                    flag = False
            return flag
        if not subtype or not hasattr(subtype, 'elts'):
            return False
        for item in subtype.elts:

            itype = convertType(item)
            for el in atype:
                if itype is el or issub(el, item):
                    flag = True
                    break
                else:
                    flag = False

        return flag
    # check the Dict type, and keys and values are checked.
    if  left is Dict or isinstance(left, Dict):
        if subtype is not Dict or not isinstance(subtype, Dict):
            return False
        if not hasattr(subtype, 'key_types'):                                          
            return False
        length = len(ftype.key_types)
        atype = [(ftype.key_types[i], ftype.value_types[i]) for i in range(length)]
        length = len(subtype.key_types)
        vtype = [(subtype.key_types[i], subtype.value_types[i]) for i in range(length)]
        flag = False
        for item in vtype:
            itype = (convertType(item[0]), convertType(item[1]))
            for el in atype:
                if (itype[0] is el[0] or issub(el[0], item[0])) and \
                    (itype[1] is el[1] or issub(el[1], item[1])):
                    flag = True
                    break
                else:
                    flag = False
        return flag
    # checking the class subtype.
    if isinstance(left, Class):
        if isinstance(right, Class) \
            and left.name and right.name:
            return left.name == right.name
        elif isinstance(right, Instance):
            if right.class_ and left.name and right.class_.name:
                return left.name == right.class_.name
            

    return False

"""
# one object is a class or instance, we can use isinstance(obj, type)
# for class, isinstance(obj, type) is True.
# for instance, isinstance(obj, type) is False.


"""
# return the class type of one object.
def convertType(t: AnyType) -> BaseType:

    if t is True or t is False:
        return data_type[1]
    if t is None or t is None_ or t is NoneType \
            or isinstance(t, None_) or isinstance(t, NoneType):
        return data_types.NoneType
    if t in num_types:
        index = num_types.index(t)
        return data_type[index]
    if isinstance(t, tuple(num_types)):
        for idx in range(len(num_types)):
            if isinstance(t, num_types[idx]):
                return data_type[idx]
    if t in str_types:
        index = str_types.index(t) + 4
        return data_type[index]
    if isinstance(t, tuple(str_types)):
        for idx in range(len(str_types)):
            if isinstance(t, str_types[idx]):
                return data_type[idx + 4]
    if type(t) in num_types:
        index = num_types.index(type(t))
        return data_type[index]
    if type(t) in str_types:
        index = str_types.index(type(t)) + 4
        return data_type[index]
    if type(t) in data_type:
        return type(t)

    return t

# return the objtype if it's numberic or string type.
def gettype(objtype: BaseType) -> BaseType:
    t = type(objtype)

    if t in data_type:
        index = data_type.index(t)
        if index < 5:
            return num_types[index]
        else:
            return str_types[index - 4]
    return objtype

# merge two same type into one type, we merge the elts instead.
def mergeTypes(ltype: UnionType[Tuple, List, Dict], rtype: UnionType[Tuple, List, Dict]) -> BaseType:
    if isinstance(ltype, Tuple) and isinstance(rtype, Tuple):
        new_elts = ltype.elts + rtype.elts
        return Tuple(None, new_elts)
    if isinstance(ltype, List) and isinstance(rtype, List):
        return List(None, ltype.elts + rtype.elts)
    if isinstance(ltype, Set) and isinstance(rtype, Set):
        new_elts = set(ltype.elts + rtype.elts)
        return Set(None, new_elts)
    if isinstance(ltype, Dict) and isinstance(rtype, Dict):
        new_elts = set(ltype.elts, rtype.elts)
        return Union(None, list(new_elts))

    return data_type[0]

# return the variable'type in the namespace.
def _get_type_from_ns(_type: ListType, PROB: bool = False) -> TupleType:
    if isinstance(_type, list):
        if PROB:
            assert len(_type) == 2
            return _type[0], _type[1]
        # Here is we return the _type directly, it will be endless loop.
        # so if _type is empty, we return List() instead.
        #return _type[0] if _type else List(None, [])
        return _type[0] if _type else data_types.Any()
    else:
        return _type

# get attribute node content.
def _getAttribute(node: AST) -> str:
    import ast

    value = node.value
    attr = node.attr
    if isinstance(value, ast.Attribute):
        value_string = _getAttribute(value)
    elif isinstance(value, ast.Name):
        value_string = value.id
    else:
        value_string = ""
    return value_string + attr

# get class or function decorater content.
def getDecorator(node: AST) -> str:
    import ast
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute):
            return _getAttribute(func)

    return ""

def _same_type(obj1: BaseType, obj2: BaseType) -> bool: 
    if not isinstance(obj1, type): 
        obj1 = type(obj1) 
    if not isinstance(obj2, type): 
        obj2 = type(obj2) 
    return obj1 is obj2 

def _update_class_attributes_from_bases(_cls: BaseType, bases: ListType, type_map: DictType) -> None:
    if bases is None or isinstance(_cls, type):
        return
    for base in bases: 
        base_name = base.id if hasattr(base, 'id') else repr(base) 
        bclass = type_map.find(base_name) 
        bclass = _get_type_from_ns(bclass)
        if hasattr(bclass, 'attributes'):
            for key in bclass.attributes.keys():
                if key not in _cls.attributes:
                    _cls.attributes[key] = bclass.attributes[key]
    

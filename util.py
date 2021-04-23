# utility module of the binary operator checking.

from typing import List as ListType, Dict as DictType, Tuple as TupleType, Any as AnyType, Union as UnionType

from .builtins import data_types
from .exceptions import NotYetSupported, NoSuchAttribute, NotIterable
from .types import (Union, List, Set, Dict, Tuple, Intersection, BaseType)
import logging
from .util1 import (getName, issub, convertType, mergeTypes)
debug = logging.debug

anno_type: DictType = {
            'int': data_types.IntType,
            'float': data_types.FloatType,
            'complex': data_types.ComplexType,
            'str': data_types.StrType,
            'Any': data_types.Any,
            'bool': data_types.BoolType,
            'Fun': data_types.Fun,
        }

num_types: ListType = [data_types.Any, data_types.Bool, data_types.Int, data_types.Float, data_types.Complex]
str_types: ListType = [data_types.Any, data_types.Bytes, data_types.Str]
data_type: ListType = [data_types.Any, data_types.BoolType, data_types.IntType,
             data_types.FloatType, data_types.ComplexType,
             data_types.BytesType, data_types.StrType]

# binary operator checking, and return the appropriate type of the result.
def binop_check(left: BaseType, right: BaseType, op_name: str, left_prob: float = 0.95, right_prob: float = 0.95) -> AnyType:
    op_list = ['__add__', '__sub__', '__mul__', '__div__', '__truediv__', '__mod__', '__pow__']
    if op_name in op_list:
        if isinstance(left, list) and len(left) == 2:
            t, p = left
            left = t
        if isinstance(right, list) and len(right) == 2:
            t, p = right
            right = t
        if isinstance(left, Intersection) and len(left.types) == 1:
            left = left.types[0]
        if isinstance(right, Intersection) and len(right.types) == 1:
            right = right.types[0]
        if not isinstance(right, type) \
            and left is type(right):
            return True
        ltype = convertType(left)
        rtype = convertType(right)
        
        lindex = -1
        rindex = -1
        if ltype in data_type:
            lindex = data_type.index(ltype)
        if rtype in data_type:
            rindex = data_type.index(rtype)
        if lindex >= 0 and rindex >= 0:
            if lindex < 5 and rindex < 5 or lindex > 4 and rindex > 4:
                return data_type[max(lindex, rindex)]
        if not issub(ltype, rtype) and not issub(rtype, ltype) and not (ltype is data_types.NoneType or rtype is data_types.NoneType):
            if _special_binop_check(op_name, ltype, rtype):
                return data_types.Any()
            from . import config
            from . import error_cache
            from .error_condition import _type_error_checking
            terror_name = repr(ltype) + op_name + repr(rtype)
            if _type_error_checking(config, error_cache, terror_name):
                logging.error("[Type Error]: Expr left_type:%r(with prob:<<%f>>) %r rigth_type:%r(with prob:<<%f>>) in file: [[%r:%d]]",
                     ltype, 1- left_prob, op_name, rtype, 1-right_prob, config.getFileName(), config.getLineNo())
            return "TypeError"
        else:
            temp = mergeTypes(ltype, rtype)
            return temp

    else:
        return "Expression {} {} {} is not supported now".format(left, op_name, right)

# check that two type is consistent.
def is_consistent(left: UnionType[ListType, BaseType], right: UnionType[ListType, BaseType]) -> bool:
    if isinstance(left, list) and len(left) == 2:
        t, p = left
        left = t
    if isinstance(right, list) and len(right) == 2:
        t, p = right
        right = t
    ltype = convertType(left)
    rtype = convertType(right)
    lindex = -1
    rindex = -1
    if ltype in data_type:
        lindex = data_type.index(ltype)
    if rtype in data_type:
        rindex = data_type.index(rtype)
    if lindex >= 0 and rindex >= 0:
        if lindex < 5 and rindex < 5 or lindex > 4 and rindex > 4:
            return data_type[max(lindex, rindex)]
    if not issub(ltype, rtype) and not issub(rtype, ltype):
        return "TypeError"
    else:
        temp = mergeTypes(ltype, rtype)
        return temp

# modular and multiplication operators checking.
def _special_binop_check(op_name: str, ltype: BaseType, rtype: BaseType) -> AnyType:
    if op_name == '__mod__' and (ltype is data_types.StrType or isinstance(ltype, data_types.Str)):
        return True
    if op_name == '__mul__' and isinstance(ltype, (Tuple, List)) and (rtype is data_types.IntType or isinstance(rtype, data_types.Int)):
        return True
    return False

# auxiliary function call checking.
def function_check(func: AnyType, args: ListType, return_anno_type: BaseType) -> None:
    return_type = func.check_call(args)
    if return_type.__class__ is return_anno_type or return_type.__class__ is \
            type(return_anno_type):
        logging.info("return_type_annotation %r EQ return_type %r",
                     return_anno_type, return_type)
    else:
        from . import config
        logging.warn("return_type_annotation %r NE return_type %r in file: %r",
                     return_anno_type, return_type, config.getFileName())


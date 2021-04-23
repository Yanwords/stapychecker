from logging import debug
from typing import Any as AnyType, Union as UnionType

from ..exceptions import NoSuchAttribute, CantSetBuiltinAttribute
from ..types import BaseType, Instance
from ..builtins.functions import BuiltinFunction as Fun
from ..types import (Dict, List, Set, Tuple, Union, Class, BaseType, _get_prob)



class BuiltinDataType(BaseType):
    def __init__(self: 'BuiltinDataType') -> None:
        self.attributes: Dict = {
            # '__class__': BaseType(),
            # '__delattr__',
            # '__dir__': Fun('__dir__', [], List(Str)),
            '__doc__': Str,
            '__eq__': Fun('__eq__', [Any], Bool),
            '__format__': Fun('__format__', [Str], Str),
            '__ge__': Fun('__ge__', [Any], Bool),
            # '__getattribute__',
            '__gt__': Fun('__gt__', [Any], Bool),
            '__hash__': Fun('__hash__', [], Int),
            # '__init__': Fun('__init__', [...], ...),
            '__le__': Fun('__le__', [Any], Bool),
            '__lt__': Fun('__lt__', [Any], Bool),
            '__ne__': Fun('__ne__', [Any], Bool),
            # '__new__',
            '__reduce__': Fun('__reduce__', [], Str),
            '__reduce_ex__': Fun('__reduce_ex__', [Int], Str),
            '__repr__': Fun('__repr__', [Any], Str),
            # '__setattr__',
            '__sizeof__': Fun('__sizeof__', [], Int),
            '__str__': Fun('__str__', [], Str),
            '__subclasshook__': Fun('__subclasshook__', [Any], Bool),
        }

    def check(self: 'BuiltinDataType') -> 'BuiltinDataType':
        #debug('checking type %r', self)
        return self

    def istypeof(self: 'BuiltinDataType', object_: AnyType) -> bool:
        if isinstance(object_, self.__class__):
            return True

    def get_attribute(self: 'BuiltinDataType', name: str, *probs: List) -> AnyType:
        try:
            import sys
            # here the self is 'isdigit', maybe in the convert function, it's converted to the data_types.Str.
            if isinstance(self, str):
                return Any()
            return self.attributes[name]
        except (KeyError, AttributeError):
             
            import logging
            from .. import config
            from .. import error_cache
            if name in type_op_methods:
                return Fun(name, [self], Any)
            
            if error_cache.addError("[KeyError]", config.getFileName(), config.getLineNo(), name):
                node = config.getCurNode()
                if probs:
                    prob = probs[0]
                else:
                    prob = 0.5
                prob = _get_prob(prob)
                if not isinstance(prob, (int, float)):
                    prob = 0.5
                logging.error("[KeyError] %r has no attribute %r in file: [[%r:%d]] <<%f>>", self, name, config.getFileName(), config.getLineNo(), 1 - prob)
            return Any()
            # raise NoSuchAttribute(self, name)

    def set_attribute(self: 'BuiltinDataType', name: str, value: AnyType) -> None:
        raise CantSetBuiltinAttribute(self)

    def __repr__(self: 'BuiltinDataType') -> str:
        return 'type.' + self.__str__()

    def __str__(self: 'BuiltinDataType') -> str:
        return 'object'

    def __iter__(self: 'BuiltinDataType') -> 'BuiltinDataType':
        yield self

    def istypeof(self: 'BuiltinDataType', object_: AnyType) -> bool:
        if self.__class__ == object_.__class__ or object_.__class__ is Any:
            return True
        return False

    # if we want to use set() to remove duplicate elts in the compound types
    # such as Union, we need to define three methods __hash__, __eq__, __ne__
    # if the elt is a class not an instance, we only need to define __hash__.
    def __hash__(self: 'BuiltinDataType') -> int:
        return hash("_butilin_type_" + str(self) + "_data_type")
    
    def __eq__(self: 'BuiltinDataType', other: 'BuiltinDataType') -> bool:
        return self.__class__.__name__ == other.__class__.__name__

    def __ne__(self: 'BuiltinDataType', other: 'BuiltinDataType') -> bool:
        return not self.__class__.__name__ == other.__class__.__name__
    

# IntType, and add many int fileds.
class IntType(BuiltinDataType):
    def __init__(self: 'IntType') -> None:
        super().__init__()
        self.attributes.update({
            '__abs__': Fun('__abs__', [], Int),
            '__add__': Fun('__add__', [Int], Int),
            '__and__': Fun('__and__', [Any], Int),
            '__bool__': Fun('__bool__', [], Bool),
            '__ceil__': Fun('__ceil__', [], Int),
            # '__divmod__': Fun('__divmod__', [Int], Tuple(Int, Int)),
            # '__float__': Fun('__float__', [], Float),
            '__floor__': Fun('__floor__', [], Int),
            '__floordiv__': Fun('__floordiv__', [Int], Int),
            # '__getnewargs__': Fun('__getnewargs__', [Int], Int),
            '__index__': Fun('__index__', [], Int),
            '__int__': Fun('__int__', [], Int),
            '__invert__': Fun('__invert__', [], Int),
            '__lshift__': Fun('__lshift__', [Int], Int),
            '__mod__': Fun('__mod__', [Int], Int),
            '__mul__': Fun('__mul__', [Union(None, [Int, Str, Float, Bool, Complex])], Int),
            '__neg__': Fun('__neg__', [], Int),
            '__or__': Fun('__or__', [Any], Int),
            '__pos__': Fun('__pos__', [], Int),
            '__pow__': Fun('__pow__', [Int, Union(None, [Int, None])], Int),
            '__radd__': Fun('__radd__', [Int], Int),
            '__rand__': Fun('__rand__', [Any], Int),
            # '__rdivmod__': Fun('__rdivmod__', [Int], Tuple(Int, Int)),
            '__rfloordiv__': Fun('__rfloordiv__', [Int], Int),
            '__rlshift__': Fun('__rlshift__', [Int], Int),
            '__rmod__': Fun('__rmod__', [Int], Int),
            '__rmul__': Fun('__rmul__', [Int], Int),
            '__ror__': Fun('__ror__', [Any], Int),
            '__round__': Fun('__round__', [], Int),
            '__rpow__': Fun('__rpow__', [Int], Int),
            '__rrshift__': Fun('__rrshift__', [Int], Int),
            '__rshift__': Fun('__rshift__', [Int], Int),
            '__rsub__': Fun('__rsub__', [Int], Int),
            '__rtruediv__': Fun('__rtruediv__', [Int], Int),
            '__rxor__': Fun('__rxor__', [Any], Int),
            '__sub__': Fun('__sub__', [Int], Int),
            '__truediv__': Fun('__truediv__', [Int], Int),
            '__trunc__': Fun('__trunc__', [], Int),
            '__xor__': Fun('__xor__', [Any], Int),
            'bit_length': Fun('bit_length', [], Int),
            # 'conjugate': Fun('conjugate', [], Complex),
            'denominator': Int,
            # 'from_bytes': Fun('from_bytes', [Bytes], Int),
            'imag': Int,
            'numerator': Int,
            'real': Int,
            # 'to_bytes': Fun('to_bytes', [Int, Str], Bytes),
        })

        # add additional attributes for int object to our self-defined int type.
        _intobj = 1
        for attr in dir(_intobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'IntType', args: List, *probs: UnionType[List, None]) -> 'IntType':
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'IntType'):
        return 'inttype'
# builtin float type.
class FloatType(BuiltinDataType):
    def __init__(self: 'FloatType') -> None:
        super().__init__()
        self.attributes.update({
            '__abs__': Fun('__abs__', [], Float),
            '__add__': Fun('__add__', [Float], Float),
            # '__and__': Fun('__and__', [Any], Int),
            '__bool__': Fun('__bool__', [], Bool),
            # '__ceil__': Fun('__ceil__', [], Int),
            # '__divmod__': Fun('__divmod__', [Int], Tuple(Int, Int)),
            '__float__': Fun('__float__', [], Float),
            # '__floor__': Fun('__floor__', [], Int),
            '__floordiv__': Fun('__floordiv__', [Float], Float),
            # '__getnewargs__': Fun('__getnewargs__', [Int], Int),
            # '__index__': Fun('__index__', [], Int),
            '__int__': Fun('__int__', [], Int),
            # '__invert__': Fun('__invert__', [], Int),
            # '__lshift__': Fun('__lshift__', [Int], Int),
            '__mod__': Fun('__mod__', [Float], Float),
            '__mul__': Fun('__mul__', [Float], Float),
            '__neg__': Fun('__neg__', [], Float),
            # '__or__': Fun('__or__', [Any], Int),
            '__pos__': Fun('__pos__', [], Float),
            # '__pow__': Fun('__pow__', [Int, Optional(Int)], Int),
            '__radd__': Fun('__radd__', [Float], Float),
            # '__rand__': Fun('__rand__', [Any], Int),
            # '__rdivmod__': Fun('__rdivmod__', [Int], Tuple(Int, Int)),
            '__rfloordiv__': Fun('__rfloordiv__', [Float], Float),
            # '__rlshift__': Fun('__rlshift__', [Int], Int),
            '__rmod__': Fun('__rmod__', [Float], Float),
            '__rmul__': Fun('__rmul__', [Float], Float),
            # '__ror__': Fun('__ror__', [Any], Int),
            '__round__': Fun('__round__', [], Int),
            '__rpow__': Fun('__rpow__', [Int], Float),
            # '__rrshift__': Fun('__rrshift__', [Int], Int),
            # '__rshift__': Fun('__rshift__', [Int], Int),
            '__rsub__': Fun('__rsub__', [Float], Float),
            '__rtruediv__': Fun('__rtruediv__', [Float], Float),
            # '__rxor__': Fun('__rxor__', [Any], Int),
            '__sub__': Fun('__sub__', [Float], Float),
            '__truediv__': Fun('__truediv__', [Float], Float),
            '__trunc__': Fun('__trunc__', [], Int),
            # '__xor__': Fun('__xor__', [Any], Int),
            # 'bit_length': Fun('bit_length', [], Int),
            'conjugate': Fun('conjugate', [], Float),
            'fromhex': Float,
            'hex': Float,
            # 'from_bytes': Fun('from_bytes', [Bytes], Int),
            'imag': Float,
            'is_integer': Bool,
            'real': Float,
            # 'to_bytes': Fun('to_bytes', [Int, Str], Bytes),
        })

        # add additional attributes for float object to our self-defined float type.
        _floatobj = 1.0
        for attr in dir(_floatobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'FloatType', args: List, *probs: UnionType[List, None]):
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'FloatType') -> str:
        return 'floattype'
# builtin complex type.
class ComplexType(BuiltinDataType):
    def __init__(self: 'ComplexType') -> None:
        super().__init__()
        self.attributes.update({
            '__abs__': Fun('__abs__', [], Complex),
            '__add__': Fun('__add__', [Complex], Complex),
            # '__and__': Fun('__and__', [Any], Int),
            '__bool__': Fun('__bool__', [], Bool),
            # '__ceil__': Fun('__ceil__', [], Int),
            # '__divmod__': Fun('__divmod__', [Int], Tuple(Int, Int)),
            # '__float__': Fun('__float__', [], Float),
            # '__floor__': Fun('__floor__', [], Int),
            '__floordiv__': Fun('__floordiv__', [Complex], Complex),
            # '__getnewargs__': Fun('__getnewargs__', [Int], Int),
            # '__index__': Fun('__index__', [], Int),
            '__int__': Fun('__int__', [], Int),
            # '__invert__': Fun('__invert__', [], Int),
            # '__lshift__': Fun('__lshift__', [Int], Int),
            '__mod__': Fun('__mod__', [Complex], Complex),
            '__mul__': Fun('__mul__', [Complex], Complex),
            '__neg__': Fun('__neg__', [], Complex),
            # '__or__': Fun('__or__', [Any], Int),
            '__pos__': Fun('__pos__', [], Complex),
            # '__pow__': Fun('__pow__', [Int, Union[Int]], Int),
            '__radd__': Fun('__radd__', [Complex], Complex),
            # '__rand__': Fun('__rand__', [Any], Int),
            # '__rdivmod__': Fun('__rdivmod__', [Int], Tuple(Int, Int)),
            '__rfloordiv__': Fun('__rfloordiv__', [Complex], Complex),
            # '__rlshift__': Fun('__rlshift__', [Int], Int),
            '__rmod__': Fun('__rmod__', [Complex], Complex),
            '__rmul__': Fun('__rmul__', [Complex], Complex),
            '__ror__': Fun('__ror__', [Any], Complex),
            # '__round__': Fun('__round__', [], Int),
            '__rpow__': Fun('__rpow__', [Complex], Complex),
            # '__rrshift__': Fun('__rrshift__', [Int], Int),
            # '__rshift__': Fun('__rshift__', [Int], Int),
            '__rsub__': Fun('__rsub__', [Complex], Complex),
            '__rtruediv__': Fun('__rtruediv__', [Complex], Complex),
            # '__rxor__': Fun('__rxor__', [Any], Int),
            '__sub__': Fun('__sub__', [Complex], Complex),
            '__truediv__': Fun('__truediv__', [Complex], Complex),
            # '__trunc__': Fun('__trunc__', [], Int),
            # '__xor__': Fun('__xor__', [Any], Int),
            # 'bit_length': Fun('bit_length', [], Int),
            # 'conjugate': Fun('conjugate', [], Complex),
            # 'denominator': Int,
            # 'from_bytes': Fun('from_bytes', [Bytes], Int),
            'imag': Int,
            # 'numerator': Int,
            'real': Int,
            # 'to_bytes': Fun('to_bytes', [Int, Str], Bytes),
        })

        # add additional attributes for complex object to our self-defined complex type.
        _complexobj = 1 + 1j
        for attr in dir(_complexobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'ComplexType', args:List, *probs: UnionType[List, None]) -> 'ComplexType':
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'ComplexType') -> str:
        return 'complextype'
# builtin bool type.
class BoolType(IntType):
    def __init__(self: 'BoolType') -> None:
        super().__init__()
        self.attributes.update({
            '__abs__': Fun('__abs__', [], Int),
            '__add__': Fun('__add__', [Union(None, [Int, Bool])], Int),
            '__and__': Fun('__and__', [Any], Bool),
            '__bool__': Fun('__bool__', [], Bool),
            '__ceil__': Fun('__ceil__', [], Int),
            # '__divmod__': Fun('__divmod__', [Int], Tuple(Int, Int)),
            '__float__': Fun('__float__', [], Float),
            '__floor__': Fun('__floor__', [], Int),
            '__floordiv__': Fun('__floordiv__', [Bool], Int),
            # '__getnewargs__': Fun('__getnewargs__', [Int], Int),
            '__index__': Fun('__index__', [], Int),
            '__int__': Fun('__int__', [], Int),
            '__invert__': Fun('__invert__', [], Int),
            '__lshift__': Fun('__lshift__', [Int], Int),
            '__mod__': Fun('__mod__', [Int], Int),
            '__mul__': Fun('__mul__', [Int], Int),
            '__neg__': Fun('__neg__', [], Int),
            '__or__': Fun('__or__', [Any], Int),
            '__pos__': Fun('__pos__', [], Int),
            # '__pow__': Fun('__pow__', [Int, Optional(Int)], Int),
            '__radd__': Fun('__radd__', [Int], Int),
            '__rand__': Fun('__rand__', [Any], Int),
            # '__rdivmod__': Fun('__rdivmod__', [Int], Tuple(Int, Int)),
            '__rfloordiv__': Fun('__rfloordiv__', [Int], Int),
            '__rlshift__': Fun('__rlshift__', [Int], Int),
            '__rmod__': Fun('__rmod__', [Int], Int),
            '__rmul__': Fun('__rmul__', [Int], Int),
            '__ror__': Fun('__ror__', [Any], Int),
            '__round__': Fun('__round__', [], Int),
            '__rpow__': Fun('__rpow__', [Int], Int),
            '__rrshift__': Fun('__rrshift__', [Int], Int),
            '__rshift__': Fun('__rshift__', [Int], Int),
            '__rsub__': Fun('__rsub__', [Int], Int),
            '__rtruediv__': Fun('__rtruediv__', [Int], Int),
            '__rxor__': Fun('__rxor__', [Any], Int),
            '__sub__': Fun('__sub__', [Int], Int),
            '__truediv__': Fun('__truediv__', [Int], Int),
            '__trunc__': Fun('__trunc__', [], Int),
            '__xor__': Fun('__xor__', [Any], Int),
            'bit_length': Fun('bit_length', [], Int),
            # 'conjugate': Fun('conjugate', [], Complex),
            'denominator': Int,
            # 'from_bytes': Fun('from_bytes', [Bytes], Int),
            'imag': Int,
            'numerator': Int,
            'real': Int,
            # 'to_bytes': Fun('to_bytes', [Int, Str], Bytes),
        })

        # add additional attributes for bool object to our self-defined bool type.
        _boolobj = True
        for attr in dir(_boolobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'BoolType', args: List, *probs: UnionType[List, None]):
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'BoolType') -> str:
        return 'booltype'

# builtin string type.
class StrType(BuiltinDataType):
    def __init__(self: 'StrType') -> None:
        super().__init__()
        # TODO
        self.attributes.update({
            '__add__': Fun('__add__', [Str], Str),
            '__contains__': Fun('__contains__', [Str], Bool),
            '__getitem__': Fun('__getitem__', [Int], Str),
            # '__getnewargs__',
            # '__iter__',
            '__len__': Fun('__len__', [], Int),
            '__mod__': Fun('__mod__', [Str], Str),
            '__mul__': Fun('__mul__', [Int], Str),
            # '__rmod__',
            '__rmul__': Fun('__rmul__', [Int], Str),
            'capitalize': Fun('capitalize', [], Str),
            'casefold': Fun('casefold', [], Str),
            # 'center': Fun('center', [Int], Str),
            'center': Fun('center', [Union(Int, [Int, Str])], Str),
            'count': Fun('count', [Str], Int),
            'encode': Fun('encode', [Any], Bytes),
            'endswith': Fun('endswith', [Str], Bool),
            'expandtabs': Fun('expandtabs', [], Str),
            'find': Fun('find', [Str], Int),
            'format': Fun('format', [Any], Str),
            # 'format_map',
            'index': Fun('index', [Int], Str),
            'isalnum': Fun('isalnum', [], Bool),
            'isalpha': Fun('isalpha', [], Bool),
            'isdecimal': Fun('isdecimal', [], Bool),
            'isdigit': Fun('isdigit', [], Bool),
            'isidentifier': Fun('isidentifier', [], Bool),
            'islower': Fun('islower', [], Bool),
            'isnumeric': Fun('isnumeric', [], Bool),
            'isprintable': Fun('isprintable', [], Bool),
            'isspace': Fun('isspace', [], Bool),
            'istitle': Fun('istitle', [], Bool),
            'isupper': Fun('issuper', [], Bool),
            'join': Fun('join', [Any], Str),
            # 'ljust': Fun('ljust', [], ),
            'lower': Fun('lower', [], Str),
            # 'lstrip': Fun('lstrip', [], List),
            # 'maketrans': Fun('maketrans', [Dict], Str),
            # 'partition': Fun('partition', [Str], Tuple[Str]),
            'replace': Fun('replace', [Str, Str], Str),
            'rfind': Fun('rfind', [Str], Int),
            'rindex': Fun('rindex', [Str], Int),
            # 'rjust': Fun('rjust', [], ),
            # 'rpartition': Fun('rpartition', [Str], Tuple[Str]),
            # 'rsplit': Fun('rsplit', [Str], Tuple[Str]),
            # 'rstrip': Fun('rstrip', [Str], Tuple[Str]),
            'split': Fun('split', [Union(None, [Str,None])], List(None, [Str])),
            # 'splitlines': Fun('splitlines', [], List[Str]),
            'startswith': Fun('startswith', [Str], Bool),
            'strip': Fun('strip', [Union(None, [Str,None])], Str),
            'swapcase': Fun('swapcase', [], Str),
            'title': Fun('title', [Any], Str),
            'translate': Fun('translate', [Str], Str),
            'upper': Fun('upper', [], Str),
            'zfill': Fun('zfill', [Int], Str),
        })

        # add additional attributes for string object to our self-defined string type. 
        _strobj = 'string object'
        for attr in dir(_strobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()
                #pass

    def check_call(self: 'StrType', args: List, *probs: UnionType[List, None]):
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'StrType') -> str:
        return 'strtype'

# builtin bytes type.
class BytesType(BuiltinDataType):
    def __init__(self: 'BytesType') -> None:
        super().__init__()
        # TODO
        self.attributes.update({
            '__add__': Fun('__add__', [Bytes], Bytes),
            '__contains__': Fun('__contains__', [Bytes], Bool),
            '__getitem__': Fun('__getitem__', [Int], Bytes),
            # '__getnewargs__',
            # '__iter__',
            '__len__': Fun('__len__', [], Int),
            # '__mod__',
            '__mul__': Fun('__mul__', [Int], Bytes),
            # '__rmod__',
            '__rmul__': Fun('__rmul__', [Int], Bytes),
            'capitalize': Fun('capitalize', [], Bytes),
            'casefold': Fun('casefold', [], Bytes),
            'center': Fun('center', [Int], Bytes),
            'count': Fun('count', [Bytes], Int),
            'decode': Fun('decode', [], Str),
            'endswith': Fun('endswith', [Bytes], Bool),
            'expandtabs': Fun('expandtabs', [], Bytes),
            'find': Fun('find', [Bytes], Int),
            'format': Fun('format', [Any], Bytes),
            # 'format_map',
            'index': Fun('index', [Int], Bytes),
            'isalnum': Fun('isalnum', [], Bool),
            'isalpha': Fun('isalpha', [], Bool),
            'isdecimal': Fun('isdecimal', [], Bool),
            'isdigit': Fun('isdigit', [], Bool),
            'isidentifier': Fun('isidentifier', [], Bool),
            'islower': Fun('islower', [], Bool),
            'isnumeric': Fun('isnumeric', [], Bool),
            'isprintable': Fun('isprintable', [], Bool),
            'isspace': Fun('isspace', [], Bool),
            'istitle': Fun('istitle', [], Bool),
            'isupper': Fun('issuper', [], Bool),
            # 'join': Fun('join', [List], Bytes),
            # 'ljust': Fun('ljust', [], ),
            'lower': Fun('lower', [], Bytes),
            # 'lstrip': Fun('lstrip', [], List),
            # 'maketrans': Fun('maketrans', [Dict], Bytes),
            # 'partition': Fun('partition', [Bytes], Tuple[Bytes]),
            'replace': Fun('replace', [Bytes, Bytes], Bytes),
            'rfind': Fun('rfind', [Bytes], Int),
            'rindex': Fun('rindex', [Bytes], Int),
            # 'rjust': Fun('rjust', [], ),
            # 'rpartition': Fun('rpartition', [Bytes], Tuple[Bytes]),
            # 'rsplit': Fun('rsplit', [Bytes], Tuple[Bytes]),
            # 'rstrip': Fun('rstrip', [Bytes], Tuple[Bytes]),
            # 'split': Fun('split', [Bytes], Tuple[Bytes]),
            # 'splitlines': Fun('splitlines', [], List[Bytes]),
            'startswith': Fun('startswith', [Bytes], Bool),
            # 'strip': Fun('strip', [], Tuple[Bytes]),
            'swapcase': Fun('swapcase', [], Bytes),
            'title': Fun('title', [], Bytes),
            'translate': Fun('translate', [Bytes], Bytes),
            'upper': Fun('upper', [], Bytes),
            'zfill': Fun('zfill', [Int], Bytes),
        })

        # add additional attributes for bytes object to our self-defined bytes type.
        _bytesobj = b'bytes'
        for attr in dir(_bytesobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'BytesType', args: List, *probs: UnionType[List, None]) -> 'BytesType':
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'BytesType') -> str:
        return 'bytestype'

    @staticmethod
    def istypeof(object_: AnyType) -> bool:
        return True

# builtin constant None type.
class NoneType(BuiltinDataType):
    def __init__(self: 'NoneType') -> None:
        super().__init__()
        self.attributes.update({
            '__bool__': Fun('__bool__', [], Bool),
        })
        
        # add additional attributes for None object to our self-defined None type.
        _noneobj = None
        for attr in dir(_noneobj):
            if attr not in self.attributes:
                self.attributes[attr] = Any()

    def check_call(self: 'NoneType', args: List, *probs: UnionType[List, None]) -> 'NoneType':
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'NoneType') -> str:
        return 'NoneType'

    def __bool__(self: 'NoneType') -> bool:
        return False   
    
# dynamic type Any.
class Any(BuiltinDataType):  # Not really builtin type, but behaves like it
    def __init__(self: 'Any') -> None:
        super().__init__()
        self.attributes.update({
            '__add__': Fun('__add__', [Any], Any),
            '__mul__': Fun('__mul__', [Int], Any),
            '__or__': Fun('__or__', [Any], Any),
            '__radd__': Fun('__radd__', [Any], Any),
            '__rmul__': Fun('__rmul__', [Any], Any),
            '__ror__': Fun('__ror__', [Any], Any),
            '__sub__': Fun('__sub__', [Any], Any),
        })

    def get_attribute(self: 'Any', name: str, *probs: List) -> AnyType:
        # return Any()
        try:
            if isinstance(self, str):
                self = Any()
            return self.attributes[name]
        except KeyError:

            return Any()
        except AttributeError:
            return Any()

    def set_attribute(self: 'Any', name: str, value: AnyType) -> None:
        try:
            self.attributes[name] = value
        except KeyError:
            CantSetBuiltinAttribute(self)

    def __getitem__(self: 'Any', key: str, **kwargs: Dict):
        return Any()

    @staticmethod
    def istypeof(object_: AnyType) -> bool:
        return True


    """ If we don't define __eq__ method, the checker may be infinite loop. 
        That's a bug. When we redefine __eq__, the while loop(./scope.py) would
        end normally.
     """
    def __eq__(self: 'Any', other: AnyType) -> bool:
        return isinstance(other, Any) or other is Any

    def __hash__(self: 'Any') -> int:
        return hash("builtins")

    def __str__(self: 'Any') -> str:
        return '<any>'

    def __call__(self: 'Any') -> 'Any':
        return self

    def check_call(self: 'Any', args: List, *probs: List) -> 'Any':
        return self

    def __iter__(self: 'Any') -> 'Any':
        # return self
        yield self

# auxiliary type undefined. Before checking, all symbols we collected is UnDefined type in all visitors.
class UnDefined(BuiltinDataType):  # Not really builtin type, but behaves like it
    def __init__(self: 'UnDefined') -> None:
        super().__init__()

    def get_attribute(self: 'UnDefined', name: str, *probs: List) -> 'UnDefined':
        return self

    @staticmethod
    def istypeof(object_: AnyType) -> bool:
        return False

    """ If we don't define __eq__ method, the checker may be infinite loop. 
        That's a bug. When we redefine __eq__, the while loop(./scope.py) would
        end normally.
     """
#    def __eq__(self, other):
#        return isinstance(other, UnDefined)

    def check_call(self: 'UnDefined', args: List, *probs:List) -> 'UnDefined':
        # TODO Check args = (Optional(Intersect(Num, string, bytes, of has __int__)), Optional(Integer))
        return self

    def __str__(self: 'UnDefined') -> str:
        return 'undefined'


class BuiltinDataInstance(Instance):
    def set_attribute(self: 'BuilintDataInstance', name: str, value: AnyType) -> None:
        self.attributes[name] = value
    
    def __eq__(self: 'BuiltinDataInstance', other: AnyType) -> bool:
        return isinstance(other, self.__class__)

    def __repr__(self: 'BuiltinDataInstance') -> str:
        # return self.__class__.__name__
        return 'type.' + self.__str__()
    # return string representation for Builtin data instance to print information in log file.
    def __str__(self: 'BuiltinDataInstance') -> str:
        return 'instance'

    def __iter__(self: 'BuiltinDataInstance') -> 'BuiltinDataInstance':
        yield self

    def istypeof(self: 'BuiltinDataInstance', object_: AnyType) -> bool:
        if self.__class__ == object_.__class__ or object_.__class__ is Any:
            return True
        return False

    # To remove duplicate elts in the compound types, we need to define
    # __hash__, __eq__, __ne__.
    def __hash__(self: 'BuiltinDataInstance') -> int:
        return hash("_butilin_type" + str(self) + "instance")
    def __eq__(self: 'BuiltinDataInstance', other: 'BuiltinDataInstance') -> bool:
        return self.__class__.__name__ == other.__class__.__name__
    def __ne__(self: 'BuiltinDataInstance', other: 'BuiltinDataInstance') -> bool:
        return not self.__class__.__name__ == other.__class__.__name__


class Int(BuiltinDataInstance):

    def __init__(self: 'Int') -> None:
        super().__init__(IntType())
    
    def __str__(self: 'Int') -> str:
        return '_int_'


class Bool(BuiltinDataInstance):

    def __init__(self: 'Bool') -> None:
        super().__init__(BoolType())
    
    def __str__(self):
        return '_bool_'

class Float(BuiltinDataInstance):

    def __init__(self: 'Float') -> None:
        super().__init__(FloatType())

    def __str__(self: 'Float') -> str:
        return '_float_'

class Complex(BuiltinDataInstance):
    
    def __init__(self: 'Complex') -> None:
        super().__init__(ComplexType())

    def __str__(self: 'Complex') -> str:
        return '_complex_'

class Str(BuiltinDataInstance):
    
    def __init__(self: 'Str') -> None:
        super().__init__(StrType())

    def __str__(self: 'Str') -> None:
        return '_str_'

class Bytes(BuiltinDataInstance):

    def __int__(self: 'Bytes') -> None:
        super.__init__(BytesType())

    def __str__(self: 'Bytes') -> None:
        return '_bytes_'

class ByteArray(BuiltinDataInstance):

    def __init__(self: 'ByteArray') -> None:
        super().__init__(BytesType())
        self.attributes.update({                         
            'append': Fun('append', [Any], Bytes), 
            'clear': Fun('clear', [], None_), 
            'extend': Fun('extend', [Any], Bytes), 
            'insert': Fun('insert', [Any], Bytes), 
            'pop': Fun('pop', [], Bytes), 
            'remove': Fun('remove', [Any], Bytes), 
            'reverse': Fun('reverse', [], Bytes), 
        })

    def __str__(self: 'ByteArray') -> None:
        return '_bytearray_'

class None_(BuiltinDataInstance):

    def __init__(self: 'None_') -> None:
        super().__init__(NoneType())

    def get_attribute(self: 'None_', name: str, *probs: List) -> AnyType:
        # return Any()
        try:
            return self.attributes[name]
        except KeyError:
            import logging
            logging.warn("[keyerror], None_ type has no attr:%r, return Any() instead!", name)
            return Any()
        except AttributeError:
            return Any()

    def __getitem__(self: 'None_', key: str, **kwargs: Dict) -> 'None_':
        return self

    @staticmethod
    def istypeof(object_: AnyType) -> bool:
        return True


    def __str__(self: 'None_') -> str:
        return '_none_'

    def __call__(self: 'None_') -> 'None_':
        return self

    def check_call(self: 'None_', args: List, *probs: UnionType[None, List]) -> 'None_':
        return self

    def __iter__(self: 'None_') -> 'None_':
        yield self

# string representation for binary operator.
type_op_methods: Set = {
    '__add__',
    '__sub__',
    '__mul__',
    '__div__',
    '__truediv__',
    '__mod__',
    '__divmod__',
    '__floordiv__',
    '__pow__',
    '__matmul__',
    '__and__',
    '__or__',
    '__xor__',
    '__lshift__',
    '__rshift__',
}  # type: Final

# add builtin data types to global symbol table.
def add_to_type_map(type_map: dict) -> None:

    # butilin method  str, bool, int, float, complex, object,
    # method would overload the buitlin datatypes. so we remove it
    TYPES = [
        # ('bool', BoolType),
        # ('bytearray', Bytearray),
        ('bytes', BytesType),
        # ('classmethod', Classmethod),
        # ('complex', ComplexType),
        # ('dict', Dict),
        # ('enumerate', Enumerate),
        # ('filter', Filter),
        # ('float', FloatType),
        # ('frozenset', Frozenset),
        # ('int', IntType),
        # ('list', List),
        # ('map', Map),
        # ('memoryview', Memoryview),
        # ('object', BuiltinDataType),
        # ('property', Property),
        # ('range', Range),
        # ('reversed', Reversed),
        # ('set', Set),
        # ('slice', Slice),
        # ('staticmethod', Staticmethod),
        # ('str', StrType),
        # ('super', Super),
        # ('tuple', Tuple),
        # ('type', BaseType),
        # ('zip', Zip),
        ('Any', Any),
        ('UnDefined', UnDefined),
        #('None', NoneType),
    ]
    COM_TYPES = [
        ('Dict', Dict),
        ('List', List),
        ('Set', Set),
        ('Tuple', Tuple),
        ('Union', Union)
    ]
    # in functions.py builtin function bool int exists,
    # thus, there is an warning information
    # handle annotation is special
    for name, type_ in TYPES:
        type_map.add_variable(name, type_())

    for name, type_ in COM_TYPES:
        type_map.add_variable(name, type_)


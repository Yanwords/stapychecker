#!/usr/bin python3
# encoding: utf-8
import logging
from logging import debug, warn
import inspect
from typing import  Dict, List, Tuple, Any as AnyType

from ..types import BaseType, Instance
from ..exceptions import WrongBuiltinArgument, WrongArgumentsLength

# check builtin function call and check the parameters and arguments.
def builtin_attr(para_types: str, arg_len: int) -> Tuple[bool, AnyType]:
    if len(para_types) != arg_len:
        pl = len(para_types)
        # para_type = para_types[0]
        from ..types import Union
        from .data_types import Any
        for para_type in para_types:
            if isinstance(para_type, Union):
                for elt in para_type.elts:
                    if elt and pl + 1 == arg_len:
                        return (True, elt)
                    else:
                        if pl - 1 == arg_len:
                            return (True, elt)
                    if pl == arg_len:
                        return (True, elt)
            if isinstance(para_type, Any) \
                or para_type is Any:
                return (True, para_type)
        return (False, None)

    return (False, None)

# Builtin function class definition, represents print, str and so on.
class BuiltinFunction(BaseType):
    def __init__(self: 'BaseType', name: str, param_types: List, return_type: AnyType) -> None:
        self.name = name
        self.param_types = param_types
        self.return_type = return_type
        self._ckd_result = None

    def check_call(self, args: List, *probs: Tuple) -> AnyType:
        # For performance, we cache the builtin function check_call result.
        # If the cached result self._ckd_result is not None, we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        debug('call check %s %s %s', self.name, self.param_types, args)
        if len(self.param_types) != len(args):
            result = builtin_attr(self.param_types, len(args))
            if result[0]:
                self._ckd_result = self.return_type
                return self.return_type
            else:
                # Here we ignore the builtin func call and return the type directly. :-)
                logging.warning(f"[WrongArgsLen] builtin func:{self.name} is called with wrong number of arguments, expected:{len(self.param_types)}, actually is {len(args)}")
                self._ckd_result = self.return_type
                return self._ckd_result
        binop_list = ['__add__', '__sub__', '__mul__', '__div__', '__truediv__', '__mod__', '__pow__']
        if isinstance(args, list):
            tmp = []
            p = []
            for item in args:
                if isinstance(item, list) \
                    and len(item) == 2:
                    tmp.append(item[0])
                    p.append([0.95 if not hasattr(self, 'prob') else self.prob, item[1]])
            if tmp:
                args = tmp
            if p:
                probs = p
        if self.name in binop_list:
            from .. import util
            from .data_types import Any
            return_type = Any()
            for param_type, arg in zip(self.param_types, args):
                if isinstance(param_type, type):
                    try:
                        param_type = param_type()
                    except TypeError:
                        param_type = param_type(None, None)
                arg_prob = 0.5
                if probs:
                    return_type = util.binop_check(param_type, arg, self.name, *probs[0])
                    #return_type = util.is_consistent(param_type, arg)
                    arg_prob = probs.pop(0)
                else:
                    return_type = util.binop_check(param_type, arg, self.name)
                from .data_types import NoneType, Str
                if return_type == "TypeError" \
                    and not isinstance(arg, NoneType) \
                    and arg is not NoneType:
                    if isinstance(param_type, Str) \
                        and self.name == "__mod__":
                        self._ckd_result = Any()
                        return self._ckd_result
                        #return Any()
                    from ..config import getFileName, getLineNo
                    # If the return_type is TypeError, then we already report the TE.
                    logging.warning(f"[TE Warning]: {self.name} expects {param_type}, but actually is {arg} with prob <<{arg_prob}>> in file:{getFileName()}:{getLineNo()}")
                    self._ckd_result = Any()
                    return self._ckd_result
                    #return Any()
            # we should return self.return_type. this is a bug
            # return self.return_type().__repr__().replace('()', '')
            # if isinstance(return_type,)
                #self._ckd_result = return_type
                # For builtin functions, we return the default return type when the arg type is consistent with param type.
                self._ckd_result = self.return_type
                return self._ckd_result
                #return return_type
            if not isinstance(return_type, Any):
                self._ckd_result = return_type
                return self._ckd_result
                #return return_type
            self._ckd_result = self._return_type
            return self._ckd_result
            #return self.return_type
        # For compound type such as List, we need to handle the append method specially.
        if self.name == "append" and hasattr(self, 'elts'):
            for arg_type in args:
                self.elts.append(arg_type)
            self.ckd_result = self
            return self.ckd_result
        from ..util1 import gettype
        if len(args) == 1:
            from ..util1 import _get_type_from_ns, issub
            p_type = _get_type_from_ns(args[0])
            ret_type = self.return_type
            param_type = self.param_types[0]
            if not isinstance(ret_type, type):
                ret_type = type(self.return_type)
            if p_type is self.return_type \
                or isinstance(p_type, ret_type) \
                or issub(p_type, param_type):
                return ret_type

        for param_type, arg in zip(self.param_types, args):
            if inspect.isclass(param_type):
                try:
                    param_type = param_type()
                except TypeError:
                    from ..types import Dict
                    param_type = param_type(None, []) if param_type is not Dict else param_type(None, [], [])
            try:
                arg = gettype(arg)()
            except TypeError:
                pass

            if not param_type.istypeof(arg):
                warn("wrong butiltin argument. para: %r, arg: %r", param_type, arg)
        self._ckd_result = self.return_type
        return self._ckd_result
        #return self.return_type

    def __repr__(self: 'BuiltinFunction') -> str:
        return self.name + '()'

    def __str__(self: 'BuiltinFunction') -> str:
        return self.name

# add builtin functions to  global symbol table.
def add_to_type_map(type_map: Dict) -> None:
    from .data_types import Any, Str, Int, Bool, Bytes, Float, Complex, None_
    from .data_types import Class, List as ListType, Dict as DictType, Set as SetType, Tuple as TupleType

    FUNCTIONS: List[Tuple] = [

        # 'abs' should be converted to __abs__
        # ('all', [Iterable(Any)], Bool),
        # ('any', [Iterable(Any)], Bool),
        ('__typeof', [Any], Str),
        # Local
        ('__builtins__', [], Any),
        ('__package__', [], Any),
        ('__spec__', [], Any),
        ('__loader__',[], Any),
        ('__doc__', [], Str),
        ('__name__', [], Str),

        # Builtins
        ('BufferError', [], Str),
        ('divmod', [], Any),
        ('slice', [], Any),
        ('NotImplemented', [], Any),
        ('eval', [], Any),
        ('UnboundLocalError', [], Any),
        ('str', [Any], Str),
        ('type', [], Any),
        # ('__loader__', [], Any),
        ('reversed', [], Any),
        ('filter', [], Any),
        ('True', [], Bool),
        ('KeyboardInterrupt', [], Any),
        ('OSError', [], Any),
        ('UnicodeWarning', [], Any),
        ('globals', [], DictType),
        ('TabError', [], Any),
        ('ConnectionResetError', [], Any),
        ('TypeError', [], Any),
        ('list', [Any], ListType),
        #('list', [Any], Any),
        ('bool', [Any], Bool),
        ('dict', [], DictType),
        ('PendingDeprecationWarning', [], Any),
        ('IsADirectoryError', [], Any),
        ('__debug__', [], Bool),
        ('dir', [], List),
        #('issubclass', [], Any),
        ('UnicodeTranslateError', [], Any),
        ('float', [], Float),
        # ('__name__', [], Str),
        ('_', [], Any),
        # ('hex', [], Any),
        ('ImportWarning', [], Any),
        ('next', [], Any),
        ('property', [], Any),
        ('BytesWarning', [], Any),
        ('EnvironmentError', [], Any),
        ('bytes', [], Bytes),
        ('delattr', [], Any),
        ('ArithmeticError', [], Any),
        ('hasattr', [], Bool),
        #('issubclass', [], Bool),
        ('UnicodeDecodeError', [], Any),
        # ('id', [], Any),
        ('bytearray', [], Bytes),
        ('all', [], Bool),
        ('Ellipsis', [], Any),
        ('super', [], Any),
        ('SyntaxError', [], Any),
        ('KeyError', [], Any),
        #('map', [], Any),
        ('map', [Any, Any], Any),
        # ('print', [], Any),
        ('FloatingPointError', [], Any),
        ('open', [], Any),
        ('SyntaxWarning', [], Any),
        ('staticmethod', [], Any),
        ('any', [], Bool),
        ('help', [], Any),
        ('memoryview', [], Any),
        # ('ord', [], Any),
        ('NotImplementedError', [], Any),
        ('vars', [], Any),
        ('zip', [], Any),
        ('exec', [], Any),
        ('tuple', [], TupleType),
        ('GeneratorExit', [], Any),
        ('max', [], Int),
        ('LookupError', [], Any),
        ('None', [], None_),
        ('SystemExit', [], Any),
        # ('input', [], Any),
        ('raw_input', [], Any),
        ('MemoryError', [], Any),
        ('license', [], Any),
        # ('repr', [], Any),
        ('FileExistsError', [], Any),
        ('exit', [], Any),
        ('format', [Any], Str),
        # ('bin', [], Any),
        ('FileNotFoundError', [], Any),
        ('TimeoutError', [], Any),
        ('sorted', [], Any),
        #('object', [], object),
        ('object', [], Instance('object')),
        # ('__package__', [], Str),
        ('getattr', [], Any),
        # ('__spec__', [], Any),
        ('UserWarning', [], Any),
        ('InterruptedError', [], Any),
        ('IndexError', [], Any),
        ('compile', [], Any),
        ('FutureWarning', [], Any),
        ('AssertionError', [], Any),
        ('DeprecationWarning', [], Any),
        # ('oct', [], Any),
        # ('callable', [], Any),
        ('SystemError', [], Any),
        ('ValueError', [], Any),
        ('NameError', [], Any),
        # ('chr', [], Any),
        ('pow', [], Float),
        ('hash', [], Int),
        ('OverflowError', [], Any),
        ('Warning', [], Any),
        #('setattr', [], Any),
        ('setattr', [Any, Any, Any], Any),
        ('ChildProcessError', [], Any),
        ('StopIteration', [], Any),
        ('quit', [], Any),
        ('ImportError', [], Any),
        ('UnicodeEncodeError', [], Any),
        ('False', [], Bool),
        ('EOFError', [], Any),
        ('RuntimeWarning', [], Any),
        ('ConnectionAbortedError', [], Any),
        ('iter', [], Any),
        ('AttributeError', [], Any),
        ('min', [], Int),
        # ('__doc__', [], Str),
        ('ResourceWarning', [], Any),
        ('__build_class__', [], Any),
        ('IOError', [], Any),
        ('ConnectionError', [], Any),
        ('set', [], SetType),
        ('range', [Any], Any),
        ('NotADirectoryError', [], Any),
        # ('ascii', [], Any),

        ('isinstance', [Any, Any], Bool),
        ('copyright', [], Any),
        ('__import__', [], Any),
        ('credits', [], Any),
        ('ProcessLookupError', [], Any),
        ('sum', [], Int),

        ('BlockingIOError', [], Any),
        ('enumerate', [], Any),
        ('len', [Any], Int),
        ('BrokenPipeError', [], Any),
        ('ReferenceError', [], Any),
        ('Exception', [], Any),

        ('locals', [], DictType),
        ('complex', [], Complex),
        ('BaseException', [], Any),

        ('PermissionError', [], Any),
        ('ZeroDivisionError', [], Any),
        ('UnicodeError', [], Any),
        ('frozenset', [], SetType),
        ('int', [Any], Int),
        ('IndentationError', [], Any),
        ('classmethod', [], Any),
        ('RuntimeError', [], Any),

        ('abs', [], Int),
        ('ConnectionRefusedError', [], Any),
        ('round', [Any], Int),
        # ('Union', [Any], Any),

        ('ascii', [Any], Str),
        ('bin', [Int], Str),
        ('callable', [Any], Bool),
        ('chr', [Int], Str),
        # 'compile': types.CodeType,
        # 'delattr' should be converted to __delattr__
        # ('dir', [Optional(Any)], Iterable(Str)),
        # ('divmod', [Num, Num], Tuple((Num, Num))),
        # ('eval', [Str, Optional(Dict(Str, Any)), Optional(Dict(Str, Any))],
        #  Any),
        # ('exec', [Intersection(Str, Code), Optional(Dict(Str, Any)),
        #           Optional(Dict(Str, Any))], None_),
        # ('format', [Any, Optional(Str)], Str),
        # 'getattr' should be converted to __getattribute__
        # ('globals', [], Dict(Str, Any)),
        # ('hasattr', [Any, Str], Bool),
        # 'hash' should be converted to __hash__
        ('hex', [Int], Str),
        ('id', [Any], Int),
        ('input', [], Str),
        # TODO actually with prompt: ('input', [Optional(Str)], Str),
        ('isinstance', [Any, Class], Bool),
        ('issubclass', [Any, Any], Bool),
        # 'iter' should be converted to __iter__ or handled specially
        #    no support for iter-with-sentinel?
        # 'len' Should have been converted to __len__
        # ('locals', [], Dict(Str, Any)),
        # 'max' TODO multiple ways to call
        # 'min' TODO multiple ways to call
        # 'next' TODO should be handled in a special way
        ('oct', [Int], Str),
        # ('open', [Str, ...], FileObject),  # TODO
        ('ord', [Str], Int),
        # ('pow', [Num, Num, Optional(Num)], Num),
        ('print', [Any], None_),  # TODO handle multiple arguments
        ('repr', [Any], Str),
        # ('round', [Num, Optional(Num)], Num),
        # 'setattr' should be converted to __setattr__
        # 'sorted' TODO should be handled in a special way
        # 'sum' TODO convert Iterable(x) to x
        # ('vars', [Optional(Any)], Dict(Str, Any)),
    ]

    # Typy doesn't support the builtin printing functions:
    #   copyright(), credit(), help(), license()
    for function_name, arg_types, return_type in FUNCTIONS:
        function = BuiltinFunction(function_name, arg_types, return_type)
        type_map.add_variable(function_name, function, 1.0)

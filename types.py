"""
This module contains all logic on how builtin Python objects behave.

In short, this defines how they handle attributes, lexical scoping,
instantiation and how they handle being called.
"""

import ast
import logging
from typing import Dict as DictType, Set as SetType, Any as AnyType, List as ListType, Tuple as TupleType, Union as UnionType, Optional as OptionalType

from .exceptions import (NoSuchAttribute, NotCallable, NotYetSupported, WrongArgumentsLength)
import functools
import sys
import collections
import operator
debug = logging.debug
AST = ast.AST

base_op_methods: SetType[str] = {
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

FUNCTION_FLAG: bool = False
# Base class of our builtin types, and we define common interface such as get_attribute and set_attribute.
class BaseType:
    def __init__(self: 'BaseType', type_map: DictType, attributes: DictType = None) -> None:
        self.type_map = type_map
        self.attributes = attributes or {}
        self.prob = -1
        from .comp_types_attrs import basic_attributes
        self.attributes.update(basic_attributes)

        # Cache the check_call return result to avoid duplicate function call.
        self._ckd_result = None
    # for most types, we offter the  default get_attribute directly.
    
    def get_attribute(self: 'BaseType', name: str, *probs: TupleType) -> 'BaseType':
        try:
            if name == 'attributes':
                return self.attributes
            return self.attributes[name]
        except KeyError:
            # if the attribute is not in attributes, we need to handle it carefully for different types.
            from . import config
            from .builtins.data_types import Any, Str
            from os.path import sep
            from . import error_cache
            from .error_condition import _attr_error_checking
            if isinstance(self, Instance):
                # Here is a bug. we pass self in the method call :->.
                prob = _get_prob(probs)
            #    if not config.getAttrError() and error_cache.addError("[AttributeError]", config.getFileName(), config.getLineNo(), name) and not "site-packages" in config.getFileName():
                ClassNameNotNone = True
                if self.class_ and hasattr(self.class_, 'name') and not self.class_.name:
                    ClassNameNotNone = False
                
                if ClassNameNotNone and _attr_error_checking(config, error_cache, name):          
                    #raise GeneratorExit
                    if not isinstance(prob, (int, float)):
                        prob = 0.5
                    logging.error("[AttributeError] %r has no attribute [%r] in file:[[%r:%d]] <<%f>>",\
                         self, name, config.getFileName(), config.getLineNo(), 1 - prob)
                self.set_attribute(name, Any())
                return self.attributes[name]
            modname = config.getFileName().split(sep)[-1] 
            if modname in sys.builtin_module_names or \
            modname.startswith('_frozen'): 
                return Any() 
            if name is "__doc__": 
                return Str() 
            
            if name in base_op_methods:
                from .builtins.functions import BuiltinFunction
                return BuiltinFunction(name, [self], Any)

            # attribute error handles
            if _attr_error_checking(config, error_cache, name):    
                prob = _get_prob(probs)
                logging.error("[AttributeError] %r has no attribute [%r] in file:[[%r:%d]] <<%f>>", self, name, config.getFileName(), config.getLineNo(), 1 - prob)
            return Any()

            # raise NoSuchAttribute(self, name)
            # TODO check existence of getattribute method
        except AttributeError:
            from .util1 import convertType
            convert = convertType(self)
            if hasattr(convert, 'attributes') and name in convert.attributes:
                return convert.attributes[name]

    def set_attribute(self: 'BaseType', name: str, value: AnyType) -> None:
        # TODO check existence of setattribute method
        self.attributes[name] = value

    def check_call(self: 'BaseType', args: ListType, *probs: TupleType) -> None:
        # TODO check for existence of __call__ and call check_call on it
        raise NotCallable(self)
    
    # check the object_ arguemnt is same type of the self.
    def istypeof(self: 'BaseType', object_: 'BaseType') -> bool:
        if self.__class__ == object_.__class__:
            if hasattr(self, 'elts') and hasattr(object_, 'elts'):
                if len(self.elts) == len(object_.elts) and self.elts == object_.elts:
                    return True
                return False
            return True
        try:
            return isinstance(self, object_)
        except TypeError:
            pass
        return False
        raise NotYetSupported('istypeof call to', self)

# Module type corresponding to the python source file.
class Module(BaseType):
    def __init__(self: 'Module', type_map: DictType, exports: DictType = None) -> None:
        super().__init__(type_map, exports)
        self.exports = exports

    def __eq__(self: 'Module', other: 'Module') -> bool:
        return isinstance(other, Module) and self.exports == other.exports

    def __hash__(self: 'Module') -> int:
        return id(self)

    def __getitem__(self: 'Module', k: str) -> AnyType:
        try:
            return self.exports[k]
        except KeyError:
            # return builtin_fields.modfields(self)[k]
            logging.warning("module type:%r has no exports key:%r", self, k)

    def to_ast(self: 'Module', lineno: int, col_offset: int) -> ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self: 'Module') -> str:
        return 'Module[{}]'.format(self.exports)

    __repr__ = __str__

# excepttype of the except clauses.
class ExceptType(BaseType):
    def __init__(self: 'ExceptType', type_map: DictType) -> None:
        super().__init__(type_map)

    def to_ast(self: 'ExceptType', lineno: int, col_offset: int) -> ast.expr:
        return ast.Name(id='object', ctx=ast.Load(), lineno=lineno, col_offset=col_offset)

    def __str__(self) -> str:
        return 'Exception'

# simple function type when we extract static inferred types.
class FuncType(BaseType):
    def __init__(self: 'FuncType', name: str, params: ListType, r_type: AnyType, type_map: DictType) -> None:
        super().__init__(type_map)
        self.name = name
        self.params = params
        self.return_type = r_type

    def check_call(self: 'FuncType', args: ListType, *probs: TupleType) -> None:
        param_map = {}
        for param, arg in zip(self.params, args):
            if not isinstance(arg, tuple):
                param_map[param] = arg

        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2 and isinstance(arg[0], str) \
                    and (arg[0] in self.params or arg[0] in param_map):
                param_map[arg[0]] = arg[1]
                args.remove(arg)
        self.type_map.enter_function_scope(self.context, param_map)
        self.type_map.exit_function_scope()

    def __repr__(self: 'FuncType') -> str:
        temp = '' if len(self.params) == 0 else ','.join([str(arg) for arg in self.params])
        return self.name + '(' + temp + ')'

def _merge_return_type(rt: BaseType, rtlists: ListType):
    if not isinstance(rt, type):
        _rt = type(rt)
    else:
        _rt = rt
    for t in rtlists:
        if not isinstance(t, type):
            _t = type(t)
        else:
            _t = t
        if rt == t or _rt == _t:
            return True
        if hasattr(rt, 'elts') \
            and hasattr(t, 'elts') \
            and len(rt.elts) == len(t.elts):
            return all([_merge_return_type(t1, [t2]) for t1, t2 in zip(rt.elts, t.elts)])
        if _rt is Dict \
            and _t is Dict \
            and len(rt.key_types) == len(t.key_types) \
            and len(rt.value_types) == len(t.value_types):
            k = all([_merge_return_type(t1, [t2]) for t1, t2 in zip(rt.key_types, t.key_types)])
            v = all([_merge_return_type(t1, [t2]) for t1, t2 in zip(rt.value_types, t.value_types)])
            if k and v:
                return True
    return False

# Function type of the Function node in the nodes module.
class Function(BaseType):
    def __init__(self: 'Function', func_def: AST, type_map: DictType) -> None:
        super().__init__(type_map)
        # save neccesary fields of the function node.
        from .comp_types_attrs import function_attributes
        self.attributes.update(function_attributes)
        
        self.name = func_def.name
        self.location = func_def.location
        self.params = func_def.params
        self.ptargs = func_def.ptargs
        self.body = func_def.body
        self.defaults = func_def.defaults
        self.kwarg = func_def.kwarg
        self.kwonlyargs = func_def.kwonlyargs
        self.kw_defaults = func_def.kw_defaults
        self.vararg = func_def.vararg
        self.context = type_map.build_context_for(self.name)
        self.return_type = func_def.return_type
        self.returns = func_def.returns
        self.dec_list = func_def.dec_list
        self.return_anno_type = func_def.return_anno_type
        self.return_flag = func_def.return_flag
        self.lastReturn = func_def.lastReturn
        self.anno_args = func_def.anno_args
        self.lineno = func_def.lineno
        self.stmts_return_flag = func_def.stmts_return_flag
        if hasattr(func_def, '_classname'):
            self._classname = func_def._classname

    def check_call(self: 'Function', args: ListType, *probs: TupleType) -> AnyType:
        # For performance, we cache the check_call result.
        # If the checked result self._ckd_result is not None, we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result

        from .nodes import Ellipsis, Expr, FunctionDef
        from .config import getFileName, getLineNo, setFileName
        from .error_condition import _filename_checking
        from . import error_cache
        
        tmpFileName = getFileName()
        setFileName(self.location)
        # Skip stub file function body checking.
        if len(self.body) == 1 \
            and isinstance(self.body[0], (Expr, Ellipsis)):
            stmt = self.body[0]
            if isinstance(stmt, Ellipsis) \
                or isinstance(stmt.value, Ellipsis):
                setFileName(tmpFileName)
                self._ckd_result = self.return_anno_type
                return self._ckd_result
                #return self.return_anno_type
        # handle the function arguemnts and parameters.
        tmp_args = args
        if isinstance(args, dict):
            args = list(args.values())
        for arg in args:
            if isinstance(arg, list) \
                and len(arg) > 0 \
                and isinstance(arg[0], tuple) \
                and len(arg[0]) == 2 \
                and not self.kwarg:
                arg_name, arg_type = arg[0][0], arg[0][1]
                if isinstance(arg_name, (tuple, list)) \
                    and len(arg_name) > 0:
                    arg_name = arg_name[0]
                    if not isinstance(arg_name, str) and hasattr(arg_name, '__iter__'):
                        arg_name = arg_name[0]
                        
                if arg_name and \
                   _filename_checking(getFileName()) \
                   and arg_name not in self.params \
                   and error_cache.addError("[ArgTypeError]", getFileName(), getLineNo(), arg_name):
                    #if arg_name == "allow_pre_release":
                    #    import traceback
                    from .builtins.data_types import Any
                    logging.error(f"[Type Error]: argument: {arg_name} with type:{arg_type} not in parameters:{self.params} in file:{getFileName()}:{getLineNo()}")
                    setFileName(tmpFileName)
                    
                    self._ckd_result = Any()
                    return self._ckd_result
                    #return Any()
       
        if len(self.ptargs) < len(args) \
            and not self.vararg:
            _args = [isinstance(_a, list) and not isinstance(tmp_args, dict) and not isinstance(_a[0], tuple) for _a in args]
            if _filename_checking(getFileName()) \
               and all(_args) \
               and error_cache.addError("[ArgLenTypeError]", getFileName(), getLineNo(), self.name):
                from .builtins.data_types import Any
                logging.error(f"[Type Error]: positional arg:{[_a.arg for _a in self.ptargs]} is {len(self.ptargs)}, but passes {len(args)} in file:{getFileName()}:{getLineNo()}")
                setFileName(tmpFileName)
                self._ckd_result = Any()
                return self._ckd_result
                #return Any()
        tmp_args = args
        # Different kinds of arguemnts.
        if self.kwarg \
            and self.kwarg not in self.params:
            self.params.append(self.kwarg)
        if len(self.ptargs) != len(args) \
            and not self.defaults \
            and not self.vararg \
            and not self.kwarg \
            and not self.kw_defaults:     
            if self.dec_list:
                for dec in self.dec_list:
                    # check static method. cls is passed.
                    if dec == 'classmethod' \
                        and hasattr(self, '_classname'):
                        _cls = self.type_map.find(self._classname)
                        _cls = _get_type(_cls)
                        args.append([_cls, prob if hasattr(_cls, 'prob') else 0.5])
            length = len(self.ptargs) + len(self.kwonlyargs) if self.kwonlyargs else len(self.ptargs)
            if length != len(args) \
                and not 'self' in self.params:
                logging.error("[MISPATCH ARGS NUM]wrong arguments length while calling function:%r,, param:%d, args:%d", self.name, len(self.params),\
                             len(args))
                setFileName(tmpFileName)
                self._ckd_result = self.return_type
                return self._ckd_result
                #return self.return_type
        param_map = {}
        if self.defaults is not None:
            for param, arg in zip(self.params, self.defaults):
                param_map[param] = arg

        if self.vararg:
            for param in self.kwonlyargs:
                self.params.append(param)
            length = len(args) - len(self.kwonlyargs)

            var_args = tuple(args[len(self.params):length])

            kwonly_args = args[length:]
            args = args[0:len(self.params)]
            args.append([var_args, prob if hasattr(var_args, 'prob') else 0.5])
            self.params.append(self.vararg)
            for arg in kwonly_args:
                args.append([arg, arg.prob if hasattr(arg, 'prob') else 0.5])
        if self.kw_defaults:
            for arg, default in zip(self.kwonlyargs, self.kw_defaults):
                from .nodes import Node
                if isinstance(default, Node):
                    default = default.check()
                param_map[arg] = default if arg not in param_map.keys() else param_map[arg]
        for param, arg in zip(self.params, args):
            if not isinstance(arg, tuple):
                param_map[param] = arg
            else:
                param_map[param] = arg
        
        if self.kwarg:
            tmp_kw = {}
            for arg in args:
                t_arg = arg
                if isinstance(arg, list):
                    arg = arg[0]
                if isinstance(arg, tuple) \
                    and len(arg) == 2 \
                    and isinstance(arg[0], str) \
                    and not arg[0] in param_map:
                    tmp_kw[arg[0]] = arg[1]
                    args.remove(t_arg)
            param_map[self.kwarg] = tmp_kw
        
        for arg in args:
            t_arg = arg
            if isinstance(arg, list):
                arg = arg[0]
            if isinstance(arg, tuple) \
                and len(arg) == 2 \
                and isinstance(arg[0], str) \
                and (arg[0] in self.params or arg[0] in param_map):
                param_map[arg[0]] = arg[1]
                args.remove(t_arg)
        from .builtins.data_types import Any
        for param in self.params:
            if param not in param_map:
                param_map[param] = Any()
        args = tmp_args
        from . import config
        if self.anno_args:
            from .util1 import issub
            from .error_condition import _filename_checking, _anno_mismatch_checking
            for argName, annoType in self.anno_args.items():
                if argName not in param_map:
                    continue
                annoType = _get_type(annoType)
                argType = param_map[argName]
                prob = 0.5
                if isinstance(argType, list):
                    prob = argType[1]
                    argType = argType[0]
                if _anno_mismatch_checking(config, error_cache, argName) \
                    and not issub(annoType, argType[0] if isinstance(argType, list) else argType):
                    logging.error("[ValueAnnotationMismatch] arg_anno expects:%r,but paratype is :%r in file: [[%r:%d]] <<%f>>",annoType, argType, config.getFileName(), config.getLineNo(), 1 - prob)
        tmp_param_map = {}
        for key, value in param_map.items():
            if isinstance(value, list) \
                and len(value) == 2:
                tmp_param_map[key] = value[0]
            tmp_param_map[key] = value
        self.type_map.enter_function_scope(self.context, tmp_param_map)
        # Checking class constructor, and return an instance.
        if self.name is '__new__':
            stmt = self.body[0]
            stmt._class = args[0]
            new_type = stmt.check()
        rec_stmt = []
        return_flag = False

        from .nodes import Return, If, Yield, YieldFrom, Assign
        from .builtins.data_types import None_, Any, NoneType
        from .util1 import issub
        
        ret_lists = [NoneType] if not self.lastReturn else []
        if self.return_anno_type is not NoneType \
            and not isinstance(self.return_anno_type, (None_, NoneType)):
            ret_lists.append(self.return_anno_type)
        # check the function body, while we handle the arguemnts and parameters.
        idx = 0

        #from . import config
        #if FUNCTION_FLAG and "pydantic/pydantic" in config.getFileName():
        #    sys.stderr.write(f"function:{self.name, config.getFileName(), config.getLineNo()} \n") 
        for stmt in self.body:
            if self.name == "field_singleton_schema":
                field = self.type_map.find('field')
                if hasattr(field, 'attributes') and 'type_' in field.attributes:
                    sys.stderr.write(f"field:{field, field.attributes['type_'], stmt.lineno, self.type_map.find('field_type')}\n")
            
            if isinstance(stmt, Assign):
                # For assign statement, we don't cache the result.
                stmt._ckd_result = None
            if isinstance(stmt, Return):
                return_flag = True
                return_type = stmt.check()
                if not _merge_return_type(return_type, ret_lists) \
                    and return_type not in ret_lists:
                    ret_lists.append(return_type)
                tmp_type = return_type
            elif isinstance(stmt, If):
                stmt._ckd_result = None
                tmp_type = stmt.check()
                if self.name == "field_singleton_schema":
                    field = self.type_map.find('field')
                    if hasattr(field, 'attributes') and 'type_' in field.attributes:
                        sys.stderr.write(f"if stmt:{field, 'type_' in field.attributes, field.attributes['type_'], self.type_map.find('field_type')}\n")
                for rt in tmp_type:
                    if not _merge_return_type(rt, ret_lists) \
                        and rt not in ret_lists \
                        and not isinstance(rt, None_) \
                        and rt is not NoneType:
                        ret_lists.append(rt)
            elif isinstance(stmt, Expr):
                # Skip yield and yield statements checking. And set the return_flag True to avoid print error message.
                expr_value = stmt.value
                return_flag = True if isinstance(expr_value, (Yield, YieldFrom)) else return_flag
                if not return_flag:
                    stmt.check()
                tmp_type = None_
                return_type = self.return_type
            elif self.stmts_return_flag[idx] and not isinstance(stmt, FunctionDef):
                tmp_type = stmt.check()
                if not _merge_return_type(tmp_type, ret_lists) \
                    and tmp_type not in ret_lists \
                    and not isinstance(tmp_type, None_) \
                    and tmp_type is not NoneType:
                    #logging.warning(f"tmp_type:{tmp_type}")
                    ret_lists.append(tmp_type)
            else:
                stmt.check()
                tmp_type = None_
            if not(tmp_type, None_) \
                and not tmp_type \
                and not isinstance(tmp_type, Any) \
                and not issub(self.return_anno_type, tmp_type):
                from .config import getCurNode
                node = getCurNode()
                prob = node.prob if hasattr(node, 'prob') else -1
                logging.error("[ValueAnnotationMismatch] return_anno:%r NE return_type:%r in file: [[%r:%d]] <<%f>>", self.return_anno_type, tmp_type, config.getFileName(), config.getLineNo(),1 - prob)
            idx += 1
            #if self.name == "foo":
            #    logging.warning(f"ret_lists:{ret_lists, type(stmt)}")
        self.return_type = return_type if return_flag else self.return_type
        from . import error_cache
        from .error_condition import _return_value_checking
        if not return_flag \
            and not self.return_flag \
            and not isinstance(self.return_anno_type, None_) \
            and not isinstance(self.return_anno_type, NoneType) \
            and self.return_anno_type is not NoneType \
            and _return_value_checking(config, error_cache, self.name, self.lineno):
            logging.error("[ReturnValueMissing] function:%r missing return type. However, AnnoReturnType:%r in file:[[%r:%d]]",\
                self.name, self.return_anno_type, config.getFileName(), self.lineno)
        self.type_map.exit_function_scope()
        if self.name is '__new__':
            return_type = new_type
            self.return_type = return_type
        elif len(ret_lists) > 1:
            setFileName(tmpFileName)
            self._ckd_result = Union(self.type_map, ret_lists)
            return self._ckd_result
            #return Union(self.type_map, ret_lists)
        setFileName(tmpFileName)
        self._ckd_result = self.return_type
        return self._ckd_result
        #return self.return_type

    def __repr__(self: 'Function') -> str:
        temp = '' if len(self.params) == 0 else ','.join([str(arg) for arg in self.params])
        #return self.name + '(' + temp + ')' + str(self.attributes)
        return self.name + '(' + temp + ')'
# Function type, similar with the function type, but it's simple.
class Function1_1(BaseType):
    def __init__(self: 'Function1_1', func_def: AST, type_map: DictType) -> None:
        super().__init__(type_map)
        self.name = func_def.name
        self.params = [arg for arg in func_def.args.args]
        self.args = func_def.args
        self.type_map = type_map
        self.body = func_def.body

    def check_call(self: 'Function1_1', args: ListType, *probs: TupleType) -> AnyType:
        if len(self.params) != len(args):
            raise WrongArgumentsLength(self.name, len(self.params), len(args))

        param_map = {param: arg for param, arg in zip(self.params, args)}
        debug('  %r', param_map)
        self.type_map.enter_function_scope(self.context, param_map)
        for stmt in self.body:
            return_type = stmt.check()
        self.type_map.exit_function_scope()

        return return_type

    def __repr__(self: 'Function1_1') -> str:
        temp = '' if len(self.params) == 0 else ','.join([arg.arg+':'+repr(arg.retic_type) for arg in self.params])
        return self.name + '('+ temp +')'

# type of lambda function.
class LambdaFunction(BaseType):
    def __init__(self: 'LambdaFunction', params: ListType, retty: ListType, type_map: DictType) -> None: 
        super().__init__(type_map)
        self.params = params
        self.retty = retty

    def check_call(self: 'LambdaFunction', args: ListType, *probs: TupleType) -> AnyType:
        # For performance, we cache the check_call result.
        # If the checked result self._ckd_result is not None, we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result

        if len(self.params) != len(args):
            raise WrongArgumentsLength(self.name, len(self.params), len(args))

        param_map = {param: arg for param, arg in zip(self.params, args)}
        debug('  %r', param_map)
        self.type_map.enter_function_scope(self.context, param_map)

        for stmt in self.body:
            return_type = stmt.check()

        self.type_map.exit_function_scope()
        self._ckd_result = return_type
        return self._ckd_result
        #return return_type

    def __repr__(self: 'LambdaFunction') -> str:
        temp = '' if len(self.params) == 0 else ','.join([arg.arg+':'+repr(arg.retic_type) for arg in self.params])
        return self.name + '('+ temp +')'

# type of the class node in the nodes module, we need to handle the base classes.
class Class(BaseType):
    def __init__(self: 'Class', class_def: OptionalType[AST] = None, type_map: OptionalType[DictType] = None, class_namespace: OptionalType[DictType] = None):
        super().__init__(type_map, class_namespace)
        
        from .comp_types_attrs import class_attributes
        self.attributes.update(class_attributes)
        if class_namespace:
            self.attributes.update(class_attributes)
        self.BASES = False
        if class_def and type_map and class_namespace:
            self.name = class_def.name
            self.body = class_def.body
            self.bases = class_def.bases
            # update the attributes of the baseclasses.
            from .util1 import _update_class_attributes_from_bases
            _update_class_attributes_from_bases(self, self.bases, self.type_map)
            if len(self.bases) == 0:
                self.BASES = True
        else:
            self.name = None
            self.body = None
            self.bases = None

    def check_call(self: 'Class', args: ListType, *probs: TupleType) -> 'Instance':
        # For performance, we cache the check_call result.
        # If the checked result self._ckd_result is not None, we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        if not self.name and not self.body and not self.bases:
            self._ckd_result = Instance(self)
            return self._ckd_result
            #return Instance(self)
        from .builtins.data_types import Any, None_
        try:
            # check the __new__ and __init__ methods, and return the instance.
            new_func = self.get_attribute('__new__')
            new_func = _get_type(new_func)
            if isinstance(new_func, Any):
                raise NoSuchAttribute(self, '__new__')
            args.insert(0, self.name)
            from .recursion import _recursive_funccall
            #instance = new_func.check_call(args, *probs)
            instance = _recursive_funccall(new_func, args, probs)
            if isinstance(instance, None_):
                instance = Instance(self, self.type_map)
            args.pop(0)
        except NoSuchAttribute:
            instance = Instance(self, self.type_map)
        try:
            # TODO explicit __new__ call
            from . import recursion
            flag = recursion.getRecFunc(self.name + "__init__")
            if flag == 2:
                flag = recursion.setRecFunc(self.name + "__init__")
            if flag:
                recursion.setRecFunc(self.name + "__init__", False)
                #import sys                                   
                #from . import config
                #if "pydantic/pydantic" in config.getFileName():
                #    sys.stderr.write(f"instance:{self.name, config.getFileName(), config.getLineNo()} \n") 
                instance.call_magic_method('__init__', args, *probs)
                recursion.setRecFunc(self.name + "__init__")
                self._ckd_result = instance
                return self._ckd_result
                #return instance
            else:
                self._ckd_result = instance
                return self._ckd_result
                #return instance
        except NoSuchAttribute:
            # TODO check supertype inits
            logging.warning("class:%r has no __init__ constructor.", self.name)
        except AttributeError:
            logging.warning("class:%r has no __init__ constructor.", self.name)
        self._ckd_result = instance
        return self._ckd_result
        #return instance
    
    # override the get_attribute, we need to check the class attributes reference.
    def get_attribute(self: 'Class', name: str, *probs: TupleType) -> AnyType:
        try: 
            if name == 'attributes': 
                return self.attributes
            return self.attributes[name] 
        except KeyError: 
            from .builtins.data_types import Any, Str
            from .config import getFileName, getLineNo
            from .error_condition import _class_attr_error_checking
            from .import error_cache, config
            if not self.BASES: 
                from .util1 import _update_class_attributes_from_bases
                _update_class_attributes_from_bases(self, self.bases, self.type_map)
                self.BASES = True
            #if self.bases is not None:
            #    for base in self.bases:                      
            #        base_name = base.id if hasattr(base, 'id') else base 
            #        base_class = self.type_map.find(base_name) 
            #        base_class = _get_type(base_class) 
            #        #if "test_errors.py" in getFileName() and self.name == "Model":
            #        #    import sys
            #        #    sys.stderr.write(f"class base:{base_name, base_class.attributes}\n")
            #        if hasattr(base_class, 'attributes'):
            #            for key in base_class.attributes.keys():
            #                if key not in self.attributes:
            #                    self.attributes[key] = base_class.attributes[key]
            if name in self.attributes:
                return self.attributes[name]
            if probs:
                prob = _get_prob(probs)
            else:
                prob = 0.5
            if isinstance(prob, list):
                prob = prob[0] if prob else 0.5
            # we just check the fields that the bases are all Class instance.
            #single_field = True
            single_field = all([isinstance(_base, Class) or _base is Class for _base in self.bases]) if self.bases else True
            
            if self.name and _class_attr_error_checking(config, error_cache, name, single_field):    
                logging.error(f"[CLASS_AttributeError] class {self.name} has no attribute:{name} in file:[[{getFileName()}:{getLineNo()}]] with proba:<<{1-prob}>>.bases is None<<{single_field}>>")
            if name is "__doc__": 
                return Str() 
            return Any()  
        # TODO search var/meth in supertypes
        # TODO search in std class vars/meths
    def __hash__(self: 'Class') -> int:
        return hash("types_" + str(self) + "_instance") 

    def __eq__(self: 'Class', other: 'Class') -> bool: 
        return self.__class__.__name__ == other.__class__.__name__ 
    def __ne__(self: 'Class', other: 'Class') -> bool: 
        return not self.__class__.__name__ == other.__class__.__name__ 
      

    def __repr__(self: 'Class') -> str:
        if self.name:
            attrs = " {cls_fields, cls_methods}"
            return "class " + self.name + attrs
        return "Class Type"

# instance type of the class instance, we need to inherit the attributes of the class and add the instance parameter self while method call checking.
class Instance(BaseType):
    def __init__(self: 'Instance', class_: Class = None, type_map: DictType = None) -> None:
        if class_ and not isinstance(class_, str):
            super().__init__(type_map, class_.attributes.copy())
            self.attributes.update(class_.attributes)
        self.class_ = class_
            
    def call_magic_method(self: 'Instance', name: str, args: ListType, *probs: TupleType) -> 'Instance':
        if self.class_:
            magic_function = self.class_.get_attribute(name, probs)
            #logging.warning(f"magic_function:{magic_function}")
            #if isinstance(magic_function, data_types.Any()) \
            #    and (name == "__init__" or name == "__new__")
            magic_method = Method(self.type_map, self, magic_function)
            
            #from . import config
            #if "pydantic/pydantic" in config.getFileName():
            #    sys.stderr.write(f"magic:{self.class_.name, config.getFileName(), config.getLineNo(), name} \n") 
            magic_method.check_call(args, probs)
            return self
        else:
            logging.error(f"Instance of None class in types.py")

    # override the get_attribute, cause the instance support dynamic attributes updating.
    def get_attribute(self: 'Instance', name: str, *probs: TupleType) -> AnyType:
        from .builtins.data_types import Any
        if isinstance(self, str):
            return Any()
        # ignore the is and is not operator checking.
        if name == "__is__" or name == "__isnot__": 
            return Any()
        try:
            if name == 'attributes':   
                instance_attr =  self.attributes  
            if hasattr(self, 'attributes') and name in self.attributes:
                instance_attr =  self.attributes[name]
            else:
                #raise KeyError
                instance_attr = super().get_attribute(name, probs)
            instance_attr = _get_type(instance_attr)
            if isinstance(instance_attr, Function):
                return Method(self.type_map, self, instance_attr)
            else:
                return instance_attr
        except (KeyError, AttributeError):
            instance_attr = Any()
            if hasattr(self.class_, 'attribtutes') and name in self.class_.attributes:
                instance_attr =  self.class_.attributes[name]
                instance_attr=_get_type(instance_attr)
            if isinstance(instance_attr, Function):
                return Method(self.type_map, self, instance_attr)
            from .builtins.data_types import Any, Str, None_
            #if isinstance(self, None_) and name == "attributes":
            #    raise AttributeError
            from .config import getFileName, getLineNo
            if name is "__doc__":  
                return Str()  
            prob = _get_prob(probs)
            logging.error("[AttributeError] %r has no attribute [%r] in file:[[%r:%d]] <<%f>>", self, name, getFileName(), getLineNo(), 1 - prob)
            return Any()
        except TypeError:
            import traceback
            traceback.print_exc()
            return Any()
        except NoSuchAttribute:
            logging.warning("instance:%r has no attr:%r", self, name)
            attr = Any()
        try:
            attr = super().get_attribute(name)
        except NoSuchAttribute:
            logging.warning("instance:%r has no attr:%r", self, name)
            attr = Any()
        finally:
            if isinstance(attr, Any):
                return attr
            return Any()

    def set_attribute(self: 'Instance', name: str, value: AnyType) -> None:
        # TODO check existence of setattribute method
        old_type = None
        if name in self.attributes:
            old_type = self.attributes[name]
            value = _get_type(value)
            merge_type = Union(None, [old_type, value])
            value = merge_type
        self.attributes[name] = value

    def istypeof(self: 'Instance', object_: UnionType[Class, 'Instance']) -> bool:
        if not isinstance(object_, Instance) or isinstance(self.class_, str):
            return False
        return self.class_.istypeof(object_.class_)

    def check(self: 'Instance') -> 'Instance':
        return self

    def check_call(self: 'Instance', args: ListType, *probs: TupleType) -> AnyType:
        from .builtins.data_types import Any
        try:
            call_func = self.get_attribute('__call__')
            if isinstance(call_func, Any):
                raise NoSuchAttribute(self, '__call__')
            args.insert(0, self.class_)
            instance = call_func.check_call(args)
        except AttributeError:
            import sys
            return self
        except NoSuchAttribute:
            instance = Instance(self, self.type_map)

    def __repr__(self: 'Instance') -> str:
        if not isinstance(self.class_, str) and self.class_:
            attrs = "{obj_fields, obj_methods}"
            return "instance " + repr(self.class_.name) + repr(attrs)  
        return "instance " + repr(self.class_) + '()'

    def __str__(self: 'Instance') -> str:
        if not isinstance(self.class_, str):
            return '{} object'.format(self.class_.name)
        return "{} instance".format(self.class_)

# Method type of the isntance method, and we need to pass an instance obejct as the self parameter.
class Method(BaseType):
    """A method is represented as a wrapper around a function within a class"""
    def __init__(self: 'Method', type_map: DictType, object_: Instance, function: Function) -> None:
        super().__init__(type_map)
        self.object_ = object_
        self.function = function

    def __getattr__(self: 'Method', name: str) -> AnyType:
        return getattr(self.function, name)

    def check_call(self: 'Method', args: ListType, *probs: TupleType) -> AnyType:
        # For performance, we cache the check_call result.
        # If the checked result self._ckd_result is not None, we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result

        global FUNCTION_FLAG
        if isinstance(self.function, list):
            assert len(self.function) == 2
            self.function = self.function[0]
        if not isinstance(args, list):
            args = [args]
            
        #from . import config
        #if "pydantic/pydantic" in config.getFileName():
        #    FUNCTION_FLAG = True
        #    sys.stderr.write(f"method:{config.getFileName(), config.getLineNo(), self.function} \n") 
        self._ckd_result = self.function.check_call([self.object_] + args, probs)
        return self._ckd_result
        #return self.function.check_call([self.object_] + args, probs)

    def __repr__(self: 'Method') -> str:
        return "method:" + self.object_.class_.name + '.' + self.name + '()'


def _check_generic(cls: Class, parameters: ListType) -> None:
    """
    Check correct count for parameters of a generic cls (internal helper).
    This gives a nice error message in case of count mismatch.
    """
    if not cls.__parameters__:
        raise TypeError(f"{cls} is not a generic class")
    alen = len(parameters)
    elen = len(cls.__parameters__)
    if alen != elen:
        raise TypeError(f"Too {'many' if alen > elen else 'few'} parameters for {cls};"
                        f" actual {alen}, expected {elen}")

# Tuple type of the builtin type, we save the elements and probas.
class Tuple(BaseType):
    # if we use *elements, we may get a tuple not a list.
    # For example, Tuple([int, str]), elts = ([int, str],). So we need to use elements instead *elements.

    def __init__(self: 'Tuple', type_map: OptionalType[DictType] = None, elements: ListType = [], prob: ListType = []) -> None:
        super().__init__(type_map)
        from .comp_types_attrs import tuple_attributes
        self.attributes.update(tuple_attributes)

        self.elts = elements
        self.index = 0
        if self.elts: 
            self.prob = prob if prob else [1/len(self.elts)] * len(self.elts) 
        else: 
            self.prob = []
    def __repr__(self: 'Tuple') -> str:
        if self.prob: 
            return "Tuple" + '(' + ', '.join(repr(el) + ":" + str(prob) for el,prob in zip(self.elts, self.prob)) + ')' 
        else:
            if not self.elts:
                return "Tuple()"
            return 'Tuple'+'(' + ', '.join(repr(el) for el \
                                       in self.elts) + ')'
    def __str__(self: 'Tuple') -> str:
        return self.__repr__()

    def __iter__(self: 'Tuple') -> 'Tuple':
        return self

    def __next__(self: 'Tuple') -> AnyType:
        if self.index < len(self.elts):
            self.index = self.index + 1
            return self.elts[self.index - 1]
        else:
            self.index = 0
            raise StopIteration
    def check_call(self: 'Tuple', args: ListType, *probs: TupleType) -> 'Tuple':
        return self

# check the element if hashable.
def _unhash_check(elt: UnionType[ListType, DictType, TupleType]) -> bool:
    if elt is List or isinstance(elt, List):
        return True
    elif elt is dict or isinstance(elt, dict):
        return True
    elif elt is Dict or isinstance(elt, Dict):
        return True
    elif isinstance(elt, tuple):
        return True
    return False

# Union type, for our checker, it's used as probabilistic types. We print ProbType instead of Union when we print the instance.
class Union(BaseType):
    # if we use *type_elements, we may get a tuple not a list.
    # For example, Union([int, str]), elts = ([int, str],). So we need to use type_element instead *type_element.
    
    def __init__(self: 'Union', type_map: OptionalType[DictType] = None, type_elements: ListType = [], prob: ListType = []) -> None:
        super().__init__(type_map)
        self.elts = type_elements
        tmp_elts = []
        unhash = []
        elt_length = range(len(self.elts))
        from .builtins.data_types import Any, None_, NoneType, UnDefined
        # Union type elts is complex, we need to handle it for different types.
        for elt in self.elts:
        #    elt = _get_type(elt)
            if isinstance(elt, Any):
                elt = Any
            if isinstance(elt, (None_, NoneType)):
                elt = NoneType
            # skip the UnDefined type elt, it only for initialize the identifiers.
            if isinstance(elt, UnDefined):
                 continue
            if _unhash_check(elt) or not hasattr(elt, '__hash__'):
                unhash.append(elt)
            elif isinstance(elt, Intersection) and len(elt.types) == 1:
                tmp_elts.append(elt.types[0]) if not _unhash_check(elt.types[0]) else unhash.append(elt.types[0])
            elif isinstance(elt, Union):
                for _elt in elt.elts:
                    if not _unhash_check(_elt):
                        tmp_elts.append(_elt)
                    else:
                        unhash.append(_elt)
            elif not isinstance(elt, dict):
                tmp_elts.append(elt)
            else:
                unhash.append(elt)
        # class Any and Any instance exists togather. we need to remove one.
        try:
            self.elts = list(set(tmp_elts))
        except TypeError:
            pass
        if unhash:
            self.elts.extend(unhash)
        if self.elts: 
            self.prob = [p/sum(prob) for p in prob] if prob and len(prob) == len(self.elts) else [1/len(self.elts)] * len(self.elts)
        else: 
            self.prob = []

    def __repr__(self: 'Union') -> str:
        cls_name = "ProbType"
        lbracket = "{"
        rbracket = "}"
        elt_repr = []
        #if self.prob and not hasattr(self.prob, '__iter__'):
        #    import sys
        #    sys.stderr.write(f'ProbType:{self.prob, type(self.prob)}')
        if not isinstance(self.prob, list):
            self.prob = [self.prob]
        if self.prob:
            #if not isinstance(self.prob, list):
            #    self.prob = [self.prob]
            for el, prob in zip(self.elts, self.prob):
                if isinstance(el, Instance):
                    elt_repr.append(str(el) + ":" + str(prob))
                elif isinstance(el, dict):
                    elt_repr.append("Dict" + ":" + str(prob))
                else:
                    elt_repr.append(repr(el) + ":" + str(prob))
        else:
            for el in self.elts:
                if isinstance(el, Instance):
                    elt_repr.append(str(el))
                elif isinstance(el, dict):
                    elt_repr.append("Dict")
                else:
                    elt_repr.append(repr(el))
        return cls_name + lbracket + ",".join(elt_repr) + rbracket
    def __str__(self: 'Union') -> str:
        return self.__repr__()

    def __iter__(self: 'Union') -> AnyType:
        for elt in self.elts:
            yield elt
    # For probabilistic type, we return the type elt iterately.
    def get_attribute(self: 'Union', name: str, *probs: TupleType) -> AnyType:
        attrs = []
        idx = 0

        if hasattr(self.prob, '__iter__'):
            for elt, prob in zip(self.elts, self.prob):
                #try:
                #    elt = elt()
                #except TypeError as te:
                #    pass
                try:

                     if isinstance(elt, type):
                         elt = elt()
                except TypeError as te:
                    pass

                from .config import setTypeProb
                setTypeProb(self.prob[idx])
                idx += 1
                if hasattr(elt, 'get_attribute'):
                    attr = elt.get_attribute(name, prob)
                    attr = _get_type(attr)
                    if attr: 
                        attr.prob = prob
                    attrs.append(attr)
        
            #if len(self.elts) == 1:
            #    import sys
            #    sys.stderr.write(f"probtype:{attrs, elt}\n")

        #if len(self.elts) == 1:
        #    import sys
        #    sys.stderr.write(f"probtype:{attrs, hasattr(self.prob, 'iter'), self.prob, type(self.prob)}\n")
        if not attrs:
            return super().get_attribute(name, probs)
        else:
            return attrs
    
    def istypeof(self: 'Union', object_: AnyType) -> bool:
        from .util1 import issub
        return issub(self, object_)
        
    def check_call(self: 'Union', args: ListType, *probs: TupleType) -> 'Union':
        return self

# Set type of the self-defined type.
class Set(BaseType):
    def __init__(self: 'Set', type_map: OptionalType[DictType] = None, type_elements: ListType = [], prob: ListType = []) -> None:
        super().__init__(type_map)
        from .comp_types_attrs import set_attributes
        self.attributes.update(set_attributes)
        self.elts = type_elements
        self.index = 0
        if self.elts: 
            self.prob = prob if prob else [1/len(self.elts)] * len(self.elts) 
        else: 
            self.prob = []
    def __repr__(self: 'Set') -> str:
        if self.prob:
            return "Set" + '{' + ', '.join(repr(el) + ":" + str(prob) for el,prob in zip(self.elts, self.prob)) + '}'
        else:
            return 'Set'+ '{' + ', '.join(repr(el) for el \
                                      in self.elts) + '}'
    def __str__(self: 'Set') -> str:
        return self.__repr__()

    def __iter__(self: 'Set') -> 'Set':
        return self

    def __next__(self: 'Set') -> AnyType:
        if self.index < len(self.elts):
            self.index = self.index + 1
            return self.elts[self.index - 1]
        else:
            self.index = 0
            raise StopIteration
    def check_call(self: 'Set', args: ListType, *probs: TupleType) -> 'Set':
        return self

# List type of our checker self-defined type.
class List(BaseType):
    def __init__(self: 'List', type_map: OptionalType[DictType] = None, type_elements: ListType = [], prob: ListType = []) -> None:
        super().__init__(type_map)
        from .comp_types_attrs import list_attributes
        self.attributes.update(list_attributes)
        self.elts = type_elements
        self.index = 0
        if self.elts:
            self.prob = prob if prob else [1/len(self.elts)] * len(self.elts)
        else:
            self.prob = []
        if not isinstance(self.elts, list):
            self.elts = [self.elts]
    def __repr__(self: 'List') -> str:
        if self.prob and not isinstance(self.prob, list):
            #import sys
            #
            #sys.stderr.write(f'List:{self.prob, [self.prob], type(self.prob)}')
            self.prob = [self.prob]
        if self.prob: 
            return "List" + '[' + ', '.join(repr(el) + ":" + str(prob) for el,prob in zip(self.elts, self.prob)) + ']' 
        else:
            return 'List' + '[' + ', '.join(repr(el) for el \
                                        in self.elts) + ']'

    def __eq__(self: 'List', other: 'List') -> bool:
        return isinstance(other, List) and \
            self.elts == other.elts

    def __str__(self: 'List') -> str:
        return self.__repr__()

    def __iter__(self: 'List') -> 'List':
        return self

    def __next__(self: 'List') -> AnyType:
        if self.index < len(self.elts):
            self.index = self.index + 1
            return self.elts[self.index - 1]
        else:
            self.index = 0
            raise StopIteration

    def check_call(self: 'List', args: ListType, *probs: TupleType) -> 'List':
        return self

'''
TypeError: 'Union' object is not subscriptable

solution:
add method
def __getitem__(self, parameters):
      
'''
# self-defined dict type, we add probas.
class Dict(BaseType):
    def __init__(self: 'Dict', type_map: OptionalType[DictType] = None, k_types: ListType = [], v_types: ListType = [], prob: ListType = []) -> None:
        super().__init__(type_map)
        from .comp_types_attrs import dict_attributes
        self.attributes.update(dict_attributes)
        self.key_types = k_types
        self.value_types = v_types
        if self.value_types: 
            self.prob = prob if prob else [1/len(self.value_types)] * len(self.value_types) 
        else: 
            self.prob = []
    def get_attribute(self: 'Dict', name: str, *probs: TupleType) -> AnyType:

        attrs = []
        if not hasattr(self.prob, '__iter__'):
            self.prob = [self.prob]
        if name == "keys":
            key_lst = []
            prob_lst = []
            for kt, prob in zip(self.key_types, self.prob):
                key_lst.append(kt)
                prob_lst.append(prob)
                #attrs.append([kt, prob])
            keys = List(None, key_lst, prob_lst)
            #attrs.append([keys, 1.0])
            attrs = [keys, 1.0]

        elif name == "values":
            value_lst = []
            prob_lst = []
            for vt, prob in zip(self.value_types, self.prob):
                #attrs.append([vt, prob])
                value_lst.append(vt)
                prob_lst.append(prob)
            values = List(None, value_lst, prob_lst)
            #attrs.append(values, 1.0)
            attrs = [values, 1.0]
        elif name == "items":
            kv_lst = []
            for kt, vt in zip(self.key_types, self.value_types):
                kv_lst.append([kt, vt])
                #attrs.append([kt, vt])
            kv = List(None, kv_lst)
            #attrs.append(kv, 1.0)
            attrs = [kv, 1.0]

                
        else:
            pass
        if not attrs:
            return super().get_attribute(name, probs)
        else:
            return attrs

    def __repr__(self: 'Dict') -> str: 
        if not isinstance(self.key_types, list):
            self.key_types = [self.key_types]
            self.value_types = [self.value_types]
        length = len(self.key_types)
        return 'Dict' + '{' + ','.join(repr(self.key_types[i])\
                + ':' + repr(self.value_types[i]) \
                            for i in range(length)) + '}'
    
    def __str__(self: 'Dict') -> str:
        return self.__repr__()

    def __iter__(self: 'Dict') -> AnyType:
        for key in self.key_types:
            yield key

    def check_call(self: 'Dict', args: ListType, *probs: TupleType) -> 'Dict': 
        return self  

_normalize_alias: DictType[str, str] = {'list': 'List',
                    'tuple': 'Tuple',
                    'dict': 'Dict',
                    'set': 'Set',
                    'frozenset': 'FrozenSet',
                    'deque': 'Deque',
                    'defaultdict': 'DefaultDict',
                    'type': 'Type_',
                    'Set': 'AbstractSet'}


def isTypeOf(target: BaseType, object_: BaseType) -> bool:
    if hasattr(target, 'istypeof'):
        target.istypeof(object_)
    if target.__class__ == object_.__class__:
        return True
    try:
        return isinstance(target, object_)
    except TypeError:
        pass
    return False

# we merge the compound type elts.
class Intersection(BaseType):

    def __init__(self: 'Intersection', type_map: DictType, *types: TupleType) -> None:
        super().__init__(type_map)
        self.types = types

    def call_magic_method(self: 'Intersection', name: str, args: ListType) -> 'Intersection':
        return_types = [type_.call_magic_method(name, args)
                        for type_ in self.types]
        return Intersection(return_types)

    def check_call(self: 'Intersection', args: ListType, *probs: TupleType) -> 'Intersection':
        return_types = [type_.check_call(args, probs) for type_ in self.types]
        return Intersection(return_types)

    def get_attribute(self: 'Intersection', name: str, *probs: TupleType) -> AnyType:
        from .builtins.data_types import NoneType
        temp_types = []
        for _type in self.types:
            if _type is None:
                temp_types.append(NoneType())
                continue
            temp_types.append(_type)
        attribute_types = [type_.get_attribute(name, probs) for type_ in temp_types]
        return Intersection(attribute_types)

    def istypeof(self: 'Intersection', object_: BaseType) -> bool:
        return all(isTypeOf(type_, object_) for type_ in self.types)

    def __call__(self: 'Intersection', *args: TupleType, **kwargs: DictType) -> 'Intersection':
        return self

    def __repr__(self: 'Intersection') -> str:
        return '(' + ' | '.join(repr(t) for t in self.types) + ')'

# return the type in the namespace.
def _get_type(_type: ListType, PROB: bool = False) -> BaseType:
    #from .util1 import (_get_type_from_ns)
    
    while isinstance(_type, list):
        #_type = _get_type_from_ns(_type)
        #if _type and len(_type) == 2:
        if _type:
            _type = _type[0]
        else:
            from .builtins.data_types import Any
            return Any()
            #return List(None, [])

    return _type

# return probas in float format.
def _get_prob(probs: UnionType[TupleType, ListType]) -> BaseType:
    if not isinstance(probs, (tuple, list)):
        return probs
    if probs:
        prob = probs[0]
    else:
        from .config import getCurNode
        node = getCurNode()
        prob = node.prob
    while isinstance(prob, (tuple, list)):
        prob = prob[0] if prob else 0.5
    return prob


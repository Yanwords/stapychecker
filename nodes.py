"""
Our own implementation of an abstract syntax tree (AST).

The convert function recursively converts a Python AST (from the module `ast`)
to our own AST (of the class `Node`).
"""

import ast
import logging
import os
import sys
from typing import Dict, List, Set, Any as AnyType, Tuple, Union as UnionType

from .builtins import data_types

from .exceptions import (NotYetSupported, NoSuchAttribute, NotIterable, NoSuchName)
from . import types
from .types import Union, BaseType, _get_type
from .result import writeTypes
import __main__
import re
from .util1 import (getName, gettype, convertType, issub, mergeTypes, getModuleName, _get_type_from_ns)
from .util import (anno_type, binop_check, function_check)
from .config import (setCurNode, setTypeProb, getCurNode, getDebug)

AST = ast.AST

BUILTIN_TYPES: Dict = {
    'bool': data_types.Bool,
    'int': data_types.Int,
    'float': data_types.Float,
    'complex': data_types.Complex,
    'bytes': data_types.Bytes,
    'str': data_types.Str,
    # 'list': data_types.List,
    # 'tuple': data_types.Tuple,
    # 'dict': data_types.Dict,
    # 'set': data_types.Set,
    'Any': data_types.Any,
    'None': data_types.None_,
    'Optional': data_types.Union,
    'AbstractSet': data_types.Set,
    'object': data_types.Class,
}

#ISINSTANCE DATA TYPES
ISINSTANCE_TYPES:Dict = {
    'bool': data_types.Bool(),
    'int': data_types.Int(),
    'float': data_types.Float(),
    'complex': data_types.Complex(),
    'bytes': data_types.Bytes(),
    'bytearray': data_types.ByteArray(),
    'str': data_types.Str(),
    'Any': data_types.Any(),
    'None': data_types.None_(),
    'object': data_types.Class(),
    # initialize the compound types.
    # attributes exists in the instance.
    'list': data_types.List(),
    'tuple': data_types.Tuple(),
    'dict': data_types.Dict(),
    'set': data_types.Set(),
    'Optional': data_types.Union(),
    'AbstractSet': data_types.Set(),
}


debug: AnyType = logging.debug
tempArgs: List = []
sub_arg_names: List = []

# Node is the base class of our ast nodes with common interface and fields.
class Node:
    def __init__(self: 'Node', type_map: Dict, ast_node: AST) -> None:
        self.type_map = type_map
        self._ast_fields = ast_node._fields
        self.lineno = ast_node.lineno if hasattr(ast_node, 'lineno') \
            else -1
        self.start = ast_node.start if hasattr(ast_node, 'start') \
            else -1
        self.prob_type = ast_node.prob_type if hasattr(ast_node, 'prob_type') \
            else data_types.Any()
        self.prob = ast_node.prob if hasattr(ast_node, 'prob') \
            else 0.5
        self._fields = ast_node._fields

        # cache the checked result for subclass nodes.
        self._ckd_result = None
        
    def check(self: 'Node') -> None:
        """Must be overriden in subtype."""
        raise NotYetSupported('check call to', self)

    def iter_fields(self: 'Node') -> Tuple:
        for field in self._ast_fields:
            try:
                yield field, getattr(self, field)
            except AttributeError:
                pass
    # iterate the node fields.
    def iter_child_nodes(self: 'Node') -> 'Node':
        for _name, field in self.iter_fields():
            if isinstance(field, Node):
                yield field
            elif isinstance(field, list):
                for item in field:
                    if isinstance(item, Node):
                        yield item

# self-defined module node.
class Module(Node, types.BaseType):
    def __init__(self: 'Module', type_map: Dict, ast_node: AST):
        from . import import_visitor
        from .comp_types_attrs import module_attributes

        Node.__init__(self, type_map, ast_node)
        types.BaseType.__init__(self, type_map)
        ns = getModuleName()
        self.module_namespace = self.type_map.enter_namespace(ns)
        import_visitor.setTypeMap(self.type_map)        
        visitor = import_visitor.ImportVisitor()
        visitor.visit(ast_node)
        mod_type = import_visitor.getTypeMap().current_namespace
        mod_type.update(module_attributes)
        self.body = [convert(type_map, stmt) for stmt in ast_node.body]
    
    # check all the statements in the module body.
    def check(self: 'Module') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from . import config
        debug('checking module: %r', config.getFileName())
        stmts = []
        for stmt in self.body:
            stmt.check()
        temp = self.type_map.current_namespace
        temp.parent = None
        
        self._ckd_result = temp
        return temp
    # return specific identifier type in the module symbol table.
    def get_attribute(self: 'Module', name: str) -> AnyType:
        try:
            return self.module_namespace[name]
        except KeyError:
            types.BaseType.get_attribute(self, name)

# check function definition including variaous arguments.
class FunctionDef(Node):
    def __init__(self: 'FunctionDef', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        from .return_visitor import ReturnVisitor, getReturnFlag,restoreReturnFlag, getBranch
        from . import error_cache, config       
        from .error_condition import _return_value_checking
        from .return_visitor import isLastReturn
        
        self.args = ast_node.args
        self.defaults = None
        # function parameters:
        # default, positional, variable, keyword#

        if len(ast_node.args.defaults) > 0:
            self.defaults = [convert(type_map, default) \
                for default in ast_node.args.defaults]
        self.ptargs = ast_node.args.args
        self.kwoargs = ast_node.args.kwonlyargs
        self.kwarg = ast_node.args.kwarg.arg if ast_node.args.kwarg else None
        self.kw_defaults = [convert(type_map, default) \
            for default in ast_node.args.kw_defaults]
        self.kwonlyargs = [kwarg.arg 
            for kwarg in ast_node.args.kwonlyargs]
        self.vararg = ast_node.args.vararg.arg if ast_node.args.vararg else None
        self.dec_list = None
        # check the decorators such as classmethod, staticmethod.
        if hasattr(ast_node, 'decorator_list'):
            self.dec_list = [convert(type_map, dec) \
                for dec in ast_node.decorator_list]
            tmp = []
            for dec in self.dec_list:
                if isinstance(dec, Name):
                    tmp.append(dec.id)
                else:
                    tmp.append(dec)
            self.dec_list = tmp
        
        self.name = ast_node.name
        self.location = config.getFileName()
        self.params = [arg.arg \
            for arg in ast_node.args.args]
        return_anno_type = data_types.None_()
        args = [data_types.Any] * len(self.params)
        if self.kwonlyargs:
            for kwarg in self.kwonlyargs:
                self.params.append(kwarg)
        self.anno_args = {}
        # check the return value missing.
        visitor = ReturnVisitor()
        visitor.visit(ast_node)
        branches = getBranch()
        b_len = len(ast_node.body)
        self.stmts_return_flag = [False] * max(branches, b_len)
        self.return_flag = getReturnFlag()
        lastReturn = isLastReturn()
        self.lastReturn = lastReturn
        if not lastReturn \
            and self.return_flag \
            and _return_value_checking(config, error_cache, self.name, self.lineno):
            logging.error("[ReturnValueMissing] function:%r missing return type in file: [[%r:%d]]",self.name, config.getFileName(), self.lineno);
        restoreReturnFlag()
        for idx in range(len(ast_node.body)):
            stmt = ast_node.body[idx] 
            visitor = ReturnVisitor()
            visitor.visit(stmt)
            self.stmts_return_flag[idx] = getReturnFlag()
            restoreReturnFlag()
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.return_type = data_types.None_()
        self.returns = ast_node.returns
        self.return_anno_type = return_anno_type
        if ast_node.returns is not None \
            and return_anno_type is data_types.None_ \
            or isinstance(return_anno_type, data_types.None_):
            return_anno_type = convert(type_map, ast_node.returns)
            self.return_type = convertAnnotation(return_anno_type, type_map)
            self.return_anno_type = self.return_type
            
        self._ast_fields = ('name', 'params', 'body')
        function = types.Function(self, type_map)
        type_map.add_variable(self.name, function, 1.0)

    def check(self: 'FunctionDef') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .builtins.data_types import UnDefined
        from .config import getFileName, getLineNo
        
        check_flag = False
        if self.anno_args:
            for vt in self.anno_args.values():
                #vt = _get_type_from_ns(vt)
                vt = _get_type_from_ns(vt)
                if isinstance(vt, data_types.Any):
                    check_flag = True
                    break
        if not self.anno_args or check_flag:
            index = 0
            annoArgsMap = {}
            args = [data_types.Any] * len(self.params)
            for arg in self.ptargs:
                annoArgsMap[arg.arg] = args[index]
                if arg.annotation is not None \
                    and args[index] is data_types.Any:
                    arg_type = convert(self.type_map, arg.annotation)
                    args[index] = arg_type
                    index += 1
                    annoArgsMap[arg.arg] = convertAnnotation(arg_type, self.type_map)
            for kwarg in self.kwoargs:
                if kwarg.annotation is not None:
                    kwarg_type = convert(self.type_map, kwarg.annotation)
                    annoArgsMap[kwarg.arg] = convertAnnotation(kwarg_type, self.type_map)
            self.anno_args = annoArgsMap
        rlts = self.type_map.in_typemap(self.name)
        # here the function may return directly.
        '''
        if rlts[0] and not isinstance(rlts[1], UnDefined) and not self.name == "field_singleton_schema":
            return_type = self.type_map.find(self.name)
            return_type = _get_type_from_ns(return_type)
            return return_type
        '''
        setLineNo(self.lineno)
        debug('adding func def %s', self.name)
        tmp_anno_args = {}
        for key, value in self.anno_args.items():
            if key not in tmp_anno_args:
                tmp_anno_args[key] = value
        for arg in self.ptargs:
            if arg.annotation is not None \
                and isinstance(arg.annotation, ast.Subscript):
                arg_type = convert(self.type_map, arg.annotation)
                tmp_anno_args[arg.arg] = convertAnnotation(arg_type, self.type_map)
        self.anno_args = tmp_anno_args
        function = types.Function(self, self.type_map)
        self.type_map.add_variable(self.name, function, 1.0)
        
        if self.anno_args \
            and len(self.anno_args) == len(self.params)\
            and not 'self' in self.params:
            for arg, arg_type in self.anno_args.items():
                if isinstance(arg_type, types.Class):
                    arg_ins = arg_type.check_call([])
                    self.anno_args[arg] = arg_ins
            return_type = function.check_call(self.anno_args)
        function = self.type_map.find(self.name)
        #function = _get_type_from_ns(function)
        function = _get_type_from_ns(function)
        
        self._ckd_result = function
        return function
    
    def __repr__(self: 'FunctionDef') -> str:
        return 'def ' + self.name + '()'
# check async function definition same as function definition.
class AsyncFunctionDef(Node):
    def __init__(self: 'AsyncFunctionDef', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        from .return_visitor import ReturnVisitor, getReturnFlag,isLastReturn, restoreReturnFlag, getBranch 
        from . import error_cache, config
        from .error_condition import _return_value_checking
        
        self.args = ast_node.args
        self.defaults = None
        if len(ast_node.args.defaults) > 0:
            self.defaults = [convert(type_map, default) \
                for default in ast_node.args.defaults]

        self.ptargs = ast_node.args.args
        self.kwarg = ast_node.args.kwarg.arg \
            if ast_node.args.kwarg else None
        self.kw_defaults = [convert(type_map, default) \
            for default in ast_node.args.kw_defaults]
        self.kwonlyargs = [convert(type_map, kwarg) \
                for kwarg in ast_node.args.kwonlyargs]
        self.vararg = convert(type_map, ast_node.args.vararg)
        para_anno = []

        self.dec_list = None 
        if hasattr(ast_node, 'decorator_list'): 
            self.dec_list = [convert(type_map, dec) \
                for dec in ast_node.decorator_list]
            tmp = [] 
            for dec in self.dec_list: 
                if isinstance(dec, Name): 
                    tmp.append(dec.id) 
                else: 
                    tmp.append(dec) 
            self.dec_list = tmp
        #    If we use srcdata of the current file, that maybe ok. So we need
        #    to get ast_node.lineno, and then read the raw source file lineno - 1
        #    and lineno - 2.
        self.location = config.getFileName()
        self.name = ast_node.name
        self.params = [arg.arg \
            for arg in ast_node.args.args]

        return_anno_type = data_types.None_
        args = [data_types.Any] * len(self.params)
        if self.kwonlyargs:
            for kwarg in self.kwonlyargs:
                self.params.append(kwarg)
        self.anno_args = args
        index = 0 
        annoArgsMap = {} 
        for arg in ast_node.args.args: 
            if arg.annotation is not None \
                and args[index] is data_types.Any: 
                arg_type = convert(type_map, arg.annotation) 
                args[index] = arg_type 
                index += 1 
                annoArgsMap[arg.arg] = convertAnnotation(arg_type, type_map) 
        for kwarg in ast_node.args.kwonlyargs:
            if kwarg.annotation is not None:
                kwarg_type = convert(type_map, kwarg.annotation)
                annoArgsMap[kwarg.arg] = convertAnnotation(kwarg_type, type_map)
        self.anno_args = annoArgsMap 
        self.stmts_return_flag = [False] * len(ast_node.body) 
        visitor = ReturnVisitor() 
        visitor.visit(ast_node) 
        branches = getBranch() 
        b_len = len(ast_node.body) 
        self.stmts_return_flag = [False] * max(branches, b_len) 
        self.return_flag = getReturnFlag() 
        lastReturn = isLastReturn() 
        self.lastReturn = lastReturn
        if not lastReturn \
            and self.return_flag \
            and _return_value_checking(config, error_cache, self.name, self.lineno): 
            logging.error("[ReturnValueMissing] function:%r missing return type in file: [[%r:%d]]", self.name, config.getFileName(), self.lineno);
        restoreReturnFlag() 
        for idx in range(len(ast_node.body)): 
            stmt = ast_node.body[idx]  
            visitor = ReturnVisitor() 
            visitor.visit(stmt) 
            self.stmts_return_flag[idx] = getReturnFlag() 
            restoreReturnFlag()
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.return_type = data_types.Any()
        self.returns = ast_node.returns
        self.return_anno_type = return_anno_type
        if ast_node.returns is not None \
            and return_anno_type is data_types.None_:
            return_anno_type = convert(type_map, ast_node.returns)
            self.return_type = convertAnnotation(return_anno_type, type_map)
            self.return_anno_type = self.return_type
        self._ast_fields = ('name', 'params', 'body')
        # add async function definition before type checking.
        self.check()

    def check(self: 'AsyncFunctionDef') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .builtins.data_types import UnDefined
        rlts = self.type_map.in_typemap(self.name)
        if rlts[0] and not isinstance(rlts[1], UnDefined):
            return_type = self.type_map.find(self.name)
            #return_type = _get_type_from_ns(return_type)
            return_type = _get_type_from_ns(return_type)
            return return_type
        setLineNo(self.lineno)
        function = types.Function(self, self.type_map)
        self.type_map.add_variable(self.name, function, 1.0)
        if self.anno_args and \
            len(self.anno_args) == len(self.params):
            return_type = function.check_call(self.anno_args)
        self._ckd_result = function
        return function

    def __repr__(self: 'AsyncFunctionDef') -> str:
        return 'async def ' + self.name + '()'

# check the class definition including class fields reference checking.
class ClassDef(Node):
    def __init__(self: 'ClassDef', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        from . import config

        self.location = config.getFileName()
        self.name = ast_node.name
        class_namespace = self.type_map.enter_namespace(self.name)
        
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.bases = [convert(type_map, base) \
            for base in ast_node.bases]
        _self = types.Class(self, self.type_map, self.type_map.current_namespace)
        SkipFlag = False
        #for dec in ast_node.decorator_list:
        #    from .util1 import getDecorator
        #    dec_content = getDecorator(dec)
        #    if dec_content == "pytest.mark.skip":
        #        SkipFlag = True
        #        break

        self.type_map.add_variable('self', _self, 1.0)
        if not SkipFlag:
            from .class_visitor import ClassVisitor, setSelf, getSelf, ClassAttrCheckerVisitor, restoreState
            
            setSelf(_self)
            # collect Class Attributes.
            visitor = ClassVisitor()
            visitor.visit(ast_node)
            # check the class attributes references.
            restoreState()
            visitor = ClassAttrCheckerVisitor()
            visitor.visit(ast_node)
        
        self.BASES = False if self.bases else True
        self.ENTER = True
        self.check()
        self.ENTER = False

    def check(self: 'ClassDef') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None and self.BASES:
            return self._ckd_result
        
        from .builtins.data_types import UnDefined
        rlts = self.type_map.in_typemap(self.name)
        if rlts[0] and not isinstance(rlts[1], UnDefined):
            class_type = self.type_map.find(self.name)
            #class_type = _get_type_from_ns(class_type)
            class_type = _get_type_from_ns(class_type)
            if not self.BASES:
                from .util1 import _update_class_attributes_from_bases
                _update_class_attributes_from_bases(class_type, self.bases, self.type_map)
                self.BASES = True

            self._ckd_result = class_type
            return class_type
        _self = self.type_map.find('self')
        #_self = _get_type_from_ns(_self)
        _self = _get_type_from_ns(_self)
        # check class methods.
        for stmt in self.body:
            if isinstance(stmt, FunctionDef) and stmt.dec_list:
                for dec in stmt.dec_list:
                    if dec == 'classmethod':
                        stmt._classname = self.name
            stmt._class_ = _self
            stmt.check()
        setLineNo(self.lineno)
        # if _self is a Class object, _self add many attributes.
        # we don't need to instance it again.
        #if not isinstance(_self, types.Class):
        class_ = types.Class(self, self.type_map, self.type_map.current_namespace)
        if self.ENTER:
            self.type_map.exit_namespace()
        
        
        self.type_map.add_variable(self.name, class_, 1.0)

        self._ckd_result = class_
        return class_

    def __repr__(self: 'ClassDef') -> str:
        return 'class ' + self.name

"""
checking binop node including left, right operands and operator.
1 + 2 has no attribute value, left right op
"""

class BinOp(Node):
    def __init__(self: 'BinOp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        if hasattr(ast_node, 'value'):
            self.value = convert(type_map, ast_node.value)
            self.attr = ast_node.attr
            self.ctx = ast_node.ctx
        self.left = convert(type_map, ast_node.left)
        self.left_name = getName(ast_node.left)
        if type(self.left_name) is not str:
            self.left_name = str(self.left_name)
        self.right_name = getName(ast_node.right)
        if type(self.right_name) is not str:
            self.right_name = str(self.right_name)
        self.right = convert(type_map, ast_node.right)
        self.op = ast_node.op
        self.op_name = self.op.__class__.__name__

    def check(self: 'BinOp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from . import config
        
        left_type = self.left.check()
        right_type = self.right.check()
        left_type.lineno = self.left.lineno
        setLineNo(self.lineno)
        # Get the operands probabilities.
        left_prob = self.left.prob if hasattr(self.left, 'prob') else 0.5
        right_prob = self.right.prob if hasattr(self.right, 'prob') else 0.5
        if hasattr(left_type, 'prob'):
            left_prob = left_type.prob
        if hasattr(right_type, 'prob'):
            right_prob = right_type.prob
        temp = binop_check(left_type, right_type, self.op_name, left_prob, right_prob)
        if isinstance(temp, str): 
            self._ckd_result = data_types.Any()
            return self._ckd_result
            #return data_types.Any()
        self._ckd_result = temp
        return self._ckd_result

        #     TODO implement for Del, AugLoad, AugStore, Param
            # raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'BinOp') -> str:
        if hasattr(self, 'value'):
            return repr(self.value) + '.' + self.attr
        else:
            op_name = self.op_name
            if self.op_name == "Add":
                op_name = '+'
            elif self.op_name == 'Sub':
                op_name = '-'
            elif self.op_name == 'Mul':
                op_name = '*'
            elif self.op_name == 'Div':
                op_name = '/'
            return "{}{}{}".format(self.left_name, op_name, self.right_name)

# instance attributes removed dynamically and identifiers in symtable removed.

class Delete(Node):
    def __init__(self: 'Delete', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.targets = [convert(type_map, target) for target in ast_node.targets]

    def check(self: 'Delete') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        from .types import Instance
        del_type = data_types.Any()
        # Now we support object attributes dynamically delete and global identifiers removing.
        for target in self.targets:
            if isinstance(target, Attribute):
                value = target.value
                attr = target.attr
                v_type = value.check()
                if isinstance(v_type, Instance):
                    if attr in v_type.attributes:
                        del_type = v_type.attributes[attr]
                        v_type.attributes.pop(attr)
                    else:
                        logging.warning("instance:%r has no attribute:%f", v_type, attr)
            if isinstance(target, Name):
                name = target.id
                del_type = self.type_map.find(name)
                del_type = _get_type_from_ns(del_type)
                self.type_map.remove_variable(name)
        
        self._ckd_result = del_type
        #return del_type
        return self._ckd_result

    def __repr__(self: 'Delete') -> str:
        return "del"

# checking with statement, sometimes with clauses is a new scope.
class With(Node):
    def __init__(self: 'With', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        # context_expr and optional_vars is optional attribute in Python3.        
        if hasattr(ast_node, 'context_expr'):
            self.context_expr = ast_node.context_expr
        if hasattr(ast_node, 'optional_vars'):
            self.optional_vars = ast_node.optional_vars
        
        self.items = [convert(type_map, item) \
            for item in ast_node.items]

        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]

    def check(self: 'With') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .config import getAttrError, setAttrError
        
        setLineNo(self.lineno)
        return_type = data_types.Any()
        bkp_flag = getAttrError()
        for item in self.items:
            item.check()
        for stmt in self.body:
            if isinstance(stmt, Return):
                return_type = stmt.check()
                continue
            stmt.check()
        setAttrError(bkp_flag)
        self._ckd_result = return_type
        #return return_type
        return self._ckd_result

    def __repr__(self: 'With') -> str:
        return "with"

# checking async with statements, similar with With statements.
class AsyncWith(Node):
    def __init__(self: 'AsyncWith', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        # context_expr and optional_vars are optional attrs in Python3.
        if hasattr(ast_node, 'context_expr'):
            self.context_expr = ast_node.context_expr
        if hasattr(ast_node, 'optional_vars'):
            self.optional_vars = ast_node.optional_vars
        self.body = [convert(type_map, stmt) for stmt in ast_node.body]

    def check(self: 'AsyncWith') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        return_type = data_types.Any()
        for stmt in self.body:
            if isinstance(stmt, Return):
                return_type = stmt.check()
                continue
            stmt.check()
        self._ckd_result = return_type
        #return return_type
        return self._ckd_result

    def __repr__(self: 'AsyncWith') -> str:
        return "asyncwith"

# checking try statements, and our checker can handle some exceptions such as attribute error
class Try(Node):
    def __init__(self: 'Try', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.handlers = [convert(type_map, handler) \
            for handler in ast_node.handlers]
        self.orelse = None
        if ast_node.orelse:
            self.orelse = [convert(type_map, stmt) \
                for stmt in ast_node.orelse]
        self.finalbody = [convert(type_map, stmt) \
            for stmt in ast_node.finalbody]

    def check(self: 'Try') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .config import setAttrError, setTypeError, getAttrError, getTypeError
        
        try_type = data_types.Any()
        hand_name = None
        attr_flag = False
        type_flag = False
        # check the name of exception, then we use later such as attribute checking.
        for hand_stmt in self.handlers:
            hand_type = hand_stmt.type
            if isinstance(hand_type, ast.Tuple):
                # For (AttributeError, TypeError)
                for elt in hand_type.elts:
                    if not hasattr(elt, 'id'):
                        continue
                    if elt.id == "AttributeError":
                        attr_flag = True
                    elif elt.id == "TypeError":
                        type_flag = True
            elif isinstance(hand_type, Name):
                if hand_type.id == "AttributeError":
                    attr_flag = True
                elif hand_type.id == "TypeError":
                    type_flag = True
        bkp_attr = getAttrError()
        bkp_type = getTypeError()
        if attr_flag:
            setAttrError(True)
        if type_flag:
            setTypeError(True)
        for stmt in self.body:
            if isinstance(stmt, Return):
                try_type = stmt.check()
                continue
            stmt.check()
        setAttrError(bkp_attr)
        bkp_attr = getAttrError()
        for hand_stmt in self.handlers:
            hand_stmt._orelse = True
            hand_stmt.check()
        setAttrError(bkp_attr)
        if self.orelse and isinstance(self.orelse, list):
            for stmt in self.orelse:
                if isinstance(stmt, Return):
                    try_type = stmt.check()
                    continue
                stmt.check()
        for stmt in self.finalbody:
            if isinstance(stmt, Return):
                try_type = stmt.check()
                continue
            stmt.check()
        setTypeError(bkp_type)
        setLineNo(self.lineno)
        self._ckd_result = try_type
        #return try_type
        return self._ckd_result

    def __repr__(self: 'Try') -> str:
        return "try"

# check exception handler, including specific exception and neglected exceptions.
class ExceptHandler(Node):
    def __init__(self: 'ExceptHandler', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        # here type may be one Name node or a Tuple whose elts is a series of Name
        # For convenience, we don't convert the self.type.
        #self.type = ast_node.type
        self.type = convert(type_map, ast_node.type)
        # here name is an alias name of self.type. It's a string object.
        self.name = ast_node.name
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
    
    def check(self: 'ExceptHandler') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        if self.name:
            tmp_type = convert(self.type_map, self.type)
            self.type_map.add_variable(self.name, tmp_type)
        if isinstance(self.type, Tuple):
            for elt in self.type.elts:
                if hasattr(elt, 'id') and \
                    elt.id == 'AttributeError':
                    from .config import setAttrError
                    setAttrError(True)
        for stmt in self.body:
            if hasattr(self, '_orelse') and self._orelse:
                stmt._orelse = True
            except_type = stmt.check()
        # Remove exception variable, in case it's referenced in other scope 
        if self.name:
            self.type_map.remove_variable(self.name)
        self._ckd_result = except_type
        #return except_type
        return self._ckd_result
    
    def __repr__(self: 'ExceptHandler') -> str:
        return "exception handler"

# check try except statements
class TryExcept(Node):
    def __init__(self: 'TryExcept', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.type = data_types.Any
        if ast_node.type:
            self.type = ast_node.type
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]

    def check(self: 'TryExcept') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        try_type = data_types.Any()
        for stmt in self.body:
            if isinstance(stmt, Return):
                try_type = stmt.check()
                continue
            stmt.check()
        setLineNo(self.lineno)
        
        self._ckd_result = try_type
        #return try_type
        return self._ckd_result

    def __repr__(self: 'TryExcept') -> str:
        return "try / except"

# check try finally clauses. 
class TryFinally(Node):
    def __init__(self: 'TryFinally', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.finalbody = [convert(type_map, stmt) \
            for stmt in ast_node.finalbody]

    def check(self: 'TryFinally') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        try_type = data_types.Any()
        for stmt in self.body:
            if isinstance(stmt, Return):
                try_type = stmt.check()
                continue
            stmt.check()
        for stmt in self.finalbody:
            if isinstance(stmt, Return):
                try_type = stmt.check()
                continue
            stmt.check()
        setLineNo(self.lineno)
        
        self._ckd_result = try_type
        #return try_type
        return self._ckd_result

    def __repr__(self: 'TryFinally') -> str:
        return "try finally"
# check raise statement, it may be difficult to handle statically, so we return directly.
class Raise(Node):
    def __init__(self: 'Raise', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.exc = ast_node.exc if ast_node.exc else data_types.NoneType
        self.cause = ast_node.cause if ast_node.cause else data_types.NoneType

    def check(self: 'Raise') -> BaseType:
        setLineNo(self.lineno)
        return types.ExceptType(None)

    def __repr__(self: 'Raise') -> str:
        return "raise"

# ignore print node.
class Print(Node):
    def __init__(self: 'Print', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)

    def check(self: 'Print') -> BaseType:
        setLineNo(self.lineno)
        return data_types.Any()

    def __repr__(self: 'Print') -> str:
        return "print"

# exec is dynamic statement, we ignore it.
class Exec(Node):
    def __init__(self: 'Exec', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)

    def check(self: 'Exec') -> BaseType:
        setLineNo(self.lineno)
        return data_types.Any()

    def __repr__(self: 'Exec') -> str:
        return "exec"

# Unary operator such as not, invert and so on.
class UnaryOp(Node):
    def __init__(self: 'UnaryOp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        
        self.operand = convert(type_map, ast_node.operand)
        self.op = ast_node.op

    def check(self: 'UnaryOp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        #unary_op_methods = {
        #    '-': '__neg__',
        #    '+': '__pos__',
        #    '~': '__invert__',
        #}  # type: Final
        if isinstance(self.op, ast.Invert):
            op_methods = '__invert__'
        elif isinstance(self.op, ast.UAdd):
            op_methods = '__pos__'
        elif isinstance(self.op, ast.USub):
            op_methods = '__neg__'
        elif isinstance(self.op, ast.Not):

            op_type = data_types.BoolType
            
            self._ckd_result = self.op_type
            self.operand._not = True
            op_type = self.operand.check()
            #return self.op_type
            self._ckd_result = op_type
            return self._ckd_result

        op_type = self.operand.check()
        #op_type = _get_type_from_ns(op_type)
        op_type = _get_type_from_ns(op_type)
        if hasattr(op_type, 'get_attribute'):
            m = op_type.get_attribute(op_methods)
            
            op_type = m.check_call([op_type])
            #op_type = _get_type_from_ns(op_type)
            op_type = _get_type_from_ns(op_type)
        
        self._ckd_result = op_type
        #return op_type
        return self._ckd_result

    def __repr__(self: 'UnaryOp') -> str:
        return "unaryop"

# check compare node.
class Compare(Node):
    def __init__(self: 'Compare', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.left = convert(type_map, ast_node.left)
        self.comparators = [comp for comp in ast_node.comparators]
        self.comps = [convert(type_map, comp) \
            for comp in self.comparators]
        self.ops = ast_node.ops

    def check(self: 'Compare') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        for com in self.comps:
            com.check()
        setLineNo(self.lineno)
        
        self._ckd_result = data_types.Bool()
        #return data_types.Bool()
        return self._ckd_result

    def __repr__(self: 'Compare') -> str:
        return "compare"

# check list comprehension [x for x in range(10)]
class ListComp(Node):
    def __init__(self: 'ListComp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.generators = [convert(type_map, generator)\
            for generator in ast_node.generators]
        self.elt = convert(type_map, ast_node.elt)

    def check(self: 'ListComp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        ##

        #handle for generators. and elts
        for gen in self.generators:
            gen.check()
            if not isinstance(self.elt, list):
                elt_type = self.elt.check()
                #elt_type = _get_type_from_ns(elt_type)
                elt_type = _get_type_from_ns(elt_type)
        
        ## 
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = types.List(None, [elt_type])
        #return types.List(None, [elt_type])
        return self._ckd_result

    def __repr__(self: 'ListComp') -> str:
        return "listcomp"

# Similar with listcomp.
class SetComp(Node):
    def __init__(self: 'SetComp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.generators = [convert(type_map, generator)\
            for generator in ast_node.generators]
        self.elt = convert(type_map, ast_node.elt)

    def check(self: 'SetComp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)

        for gen in self.generators:
            gen.check()

        elt_type = self.elt.check()
        elt_type = _get_type_from_ns(elt_type)

        if hasattr(self, 'prob_type'):
            
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = types.Set(None, [elt_type])
        #return types.Set(None, [elt_type])
        return self._ckd_result

    def __repr__(self: 'SetComp') -> str:
        return "setcomp"

# check dict comperehension.
class DictComp(Node):
    def __init__(self: 'DictComp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.generators = [convert(type_map, generator)\
            for generator in ast_node.generators]
        self.key = convert(type_map, ast_node.key)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'DictComp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)

        for gen in self.generators:
            gen.check()

        k_type = self.key.check()
        #k_type = _get_type_from_ns(k_type)
        k_type = _get_type_from_ns(k_type)
        v_type = self.value.check()
        #v_type = _get_type_from_ns(v_type)
        v_type = _get_type_from_ns(v_type)


        if hasattr(self, 'prob_type'):
            
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = types.Dict(None, [k_type], [v_type])
        #return types.Dict(None, [k_type], [v_type])
        return self._ckd_result

    def __repr__(self: 'DictComp') -> str:
        return "dictcomp"

# check generator expression.
class GeneratorExp(Node):

    def __init__(self: 'GeneratorExp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.generators = [convert(type_map, generator)\
            for generator in ast_node.generators]
        self.elt = convert(type_map, ast_node.elt)

    def check(self: 'GeneratorExp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)

        ## add check for generator expressions
        for gen in self.generators:
            gen.check()
        if not isinstance(self.elt, list):
            self.elt.check()# if not isinstance(self.elt, list)
        else:

            self._ckd_result = self.elt
            #return self.elt
            return self._ckd_result


        if hasattr(self, 'prob_type'):

            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = data_types.Any()
        #return data_types.Any()
        return self._ckd_result

    def __repr__(self: 'GeneratorExp') -> str:
        return "generatorexp"

def _add_comprehension_variable(target: AST, iter_type: AnyType, type_map: Dict):
    
    # If the iter type connot be iterated, we set Any instead.
    type_map.add_variable(target, data_types.Any())
    
    if hasattr(iter_type, 'elts'):
        for i_type in iter_type.elts:
            type_map.add_variable(target, i_type)
    elif hasattr(iter_type, 'key_types'):
        for i_type in iter_type.key_types:
            type_map.add_variable(target, i_type)
    #else:
    #    type_map.add_variable(target, iter_type)

def _remove_comprehension_variable(target, type_map):
    
    if hasattr(target, 'id'):
        type_map.remove_variable(target.id)
    elif hasattr(target, 'elts'):
        for elt in target.elts:
            if hasattr(elt, 'id'):
                continue
            type_map.remove_variable(elt.id)
    else:
        logging.warning(f"Unsupported target:{type(target)} in comprehension.")
# check the comprehension node, we need check the iter and target.
class comprehension(Node):

    def __init__(self: 'comprehension', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.target)
        self.iter = convert(type_map, ast_node.iter)
        self.ifs = [convert(type_map,if_exp) \
            for if_exp in ast_node.ifs]
        self.is_async = ast_node.is_async

    def check(self: 'comprehension') -> None:
        iter_value = self.iter.check()
        #iter_value = _get_type_from_ns(iter_value)
        iter_value = _get_type_from_ns(iter_value)
        if hasattr(self.target, 'id'):
            _add_comprehension_variable(self.target.id, iter_value, self.type_map)
        elif hasattr(self.target, 'elts'):
            for elt in self.target.elts:
                if not isinstance(elt, Name): 
                    continue
                _add_comprehension_variable(elt.id, iter_value, self.type_map)

        for if_exp in self.ifs:
            if_exp.check()

# check the withitem node, we only need to check context expression in Python3.
class withitem(Node):
    def __init__(self: 'withitem', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.context_expr = convert(type_map, ast_node.context_expr)
        # In Python3 optional_vars is removed.
        if hasattr(ast_node, 'optional_vars'):
            self.optional_vars = convert(type_map, ast_node.optional_vars)

    def check(self: 'withitem') -> None:
        if isinstance(self.context_expr, Call):
            for arg in self.context_expr.args:
                if isinstance(arg, Name) \
                    and arg.id == "AttributeError":
                    from .config import setAttrError
                    setAttrError(True)
        self.context_expr.check() 

        if hasattr(self, 'optional_vars'):
            self.optional_vars.check()

# check the yield node, and we only check the value.
class Yield(Node):
    def __init__(self: 'Yield', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = None
        if ast_node.value:
            self.value = convert(type_map, ast_node.value)

    def check(self: 'Yield') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        if self.value:
            
            self._ckd_result = self.value.check()
            #self._ckd_result = _get_type_from_ns(self._ckd_result)
            self._ckd_result = _get_type_from_ns(self._ckd_result)
            #return self.value.check()
            return self._ckd_result
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = data_types.Any()
        return self._ckd_result
        #return data_types.Any()

    def __repr__(self: 'Yield') -> str:
        return "yield"

# check yieldfrom statement, we check value.
class YieldFrom(Node):
    def __init__(self: 'YieldFrom', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'YieldFrom') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        if self.value:
            self._ckd_result = self.value.check()
            #self._ckd_result = _get_type_from_ns(self._ckd_result)
            self._ckd_result = _get_type_from_ns(self._ckd_result)
            return self._ckd_result
            #return self.value.check()
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = data_types.Any()
        return self._ckd_result
        #return data_types.Any()

    def __repr__(self: 'YieldFrom') -> str:
        return "yieldfrom"

# check the lambda function definition and we extract the arguments, check the body directly.
class Lambda(Node):
    def __init__(self: 'Lambda', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.args = ast_node.args 
        self.defaults = None 
        # function parameters: 
        # default, positional, variable, keyword# 
        self.params = [arg.arg for arg in ast_node.args.args] 
        if len(ast_node.args.defaults) > 0: 
            self.defaults = [convert(type_map, default)\
                for default in ast_node.args.defaults] 
 
        self.kwarg = ast_node.args.kwarg.arg if ast_node.args.kwarg else None 
        self.kw_defaults = [convert(type_map, default)\
            for default in ast_node.args.kw_defaults] 
        self.kwonlyargs = [kwarg.arg for kwarg in ast_node.args.kwonlyargs] 
        self.vararg = ast_node.args.vararg.arg \
            if ast_node.args.vararg else None

        self.name = "lambda function"
        
        self.body = convert(type_map, ast_node.body)

    def check(self: 'Lambda') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        
        setLineNo(self.lineno)
        param_map = {}
        for arg in self.params:
            param_map[arg] = data_types.Any()

        self.body.check()
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result

        self._ckd_result = types.LambdaType
        return self._ckd_result
        #return types.LambdaType

    def __repr__(self: 'Lambda') -> str:
        return "lambda"

# check the index node, it's in the attribute node.
class Index(Node):
    def __init__(self: 'Index', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'Index') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        check_type = self.value.check()
        #check_type = _get_type_from_ns(check_type)
        check_type = _get_type_from_ns(check_type)
        if not isinstance(check_type, data_types.Any):
            self._ckd_result = check_type
            #return check_type
            return self._ckd_result

        if hasattr(self.value, 'prob_type'):
            self._ckd_result = self.value.prob_type
            #return self.value.prob_type
            return self._ckd_result

        value_type = self.type_map.find(self.value)
        #value_type = _get_type_from_ns(value_type)
        value_type = _get_type_from_ns(value_type)
        
        self._ckd_result = value_type
        #return value_type
        return self._ckd_result

    def __repr__(self: 'Index') -> str:
        return repr(self.value)

# we check the lower, upper, and step of the slice.
class Slice(Node):
    def __init__(self: 'Slice', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.lower = convert(type_map, ast_node.lower) \
            if ast_node.lower else None
        self.upper = convert(type_map, ast_node.upper) \
            if ast_node.upper else None
        self.step = convert(type_map, ast_node.step) \
            if ast_node.step else None
        ## type determinded by List/OBject/Any

    def check(self: 'Slice') -> BaseType:
        if self._ckd_result is not None:
            return self._ckd_result
        setLineNo(self.lineno)
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result
        self._ckd_result = types.List(None, [data_types.Any()])
        #return types.List(None, [data_types.Any()])
        return self._ckd_result

    def __repr__(self: 'Slice') -> str:
        return "slice"

# check the extslice. we only check dims.
class ExtSlice(Node):
    def __init__(self: 'ExtSlice', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.dims = [convert(type_map, dim) \
            for dim in ast_node.dims]

    def check(self: 'ExtSlice') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        dim_type = data_types.Any()
        for dim in self.dims:
            dim_type = dim.check()
        if hasattr(self, 'prob_type'):
            self._ckd_result = self.prob_type
            #return self.prob_type
            return self._ckd_result
        self._ckd_result = types.List(None, [data_types.Any()])
        return self._ckd_result
        #return types.List(None, [data_types.Any()])

    def __repr__(self: 'ExtSlice') -> str:
        return "extslice"
'''
starred expression
b = [1,2,3]
a,*c = b
'''
class Starred(Node):
    def __init__(self: 'Starred', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)
        self.ctx = ast_node.ctx

    def check(self: 'Starred') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        value = self.value.check()
        setLineNo(self.lineno)
        if hasattr(self.value, 'prob_type') \
            and not isinstance(self.value, data_types.Any):
            self._ckd_result = self.value.prob_type
            #return self.value.prob_type
            return self._ckd_result

        self._ckd_result = value
        return self._ckd_result
        #return value

    def __repr__(self: 'Starred') -> str:
        return "starred"
'''
bytes
a = b'assdf'
'''

class Bytes(Node):
    def __init__(self: 'Bytes', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.node = ast_node

    def check(self: 'Bytes') -> BaseType:
        setLineNo(self.lineno)
        return data_types.BytesType

    def __repr__(self: 'Bytes') -> str:
        return "bytes"

'''
ellipsis
a = ...
'''
class Ellipsis(Node):
    def __init__(self: 'Ellipsis', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.node = ast_node

    def check(self: 'Ellipsis') -> BaseType:
        setLineNo(self.lineno)
        return data_types.Any()

    def __repr__(self: 'Ellipsis') -> str:
        return "ellipsis"

# check the global statement, it often exists in function scope.
class Global(Node):
    def __init__(self: 'Global', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.names = ast_node.names

    def check(self: 'Global') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        value_type = []
        for name in self.names:
            glb_type = self.type_map.find(name)
            #glb_type = _get_type_from_ns(glb_type)
            glb_type = _get_type_from_ns(glb_type)
            value_type.append(glb_type)
        self._ckd_result = value_type
        return self._ckd_result
        #return value_type

    def __repr__(self: 'Global') -> str:
        return "global"

# check the nonlocal statement, it often exists in function or method scope.
class Nonlocal(Node):
    def __init__(self: 'Nonlocal', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.names = ast_node.names

    def check(self: 'Nonlocal') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        value_type = []
        for name in self.names:
            nl_type = self.type_map.find(name)
            #nl_type = _get_type_from_ns(nl_type)
            nl_type = _get_type_from_ns(nl_type)
            value_type.append(nl_type)
        self._ckd_result = value_type
        return self._ckd_result
        #return value_type

    def __repr__(self: 'Nonlocal') -> str:
        return "nonlocal"
# Binary operators, convert the ast node to string format binary operator representation.
op_methods: Set[str] = {
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
}

# Return Attribute value's type.
def _get_value_type(v_type: BaseType) -> BaseType:
    #if not isinstance(v_type, type):
    v_t = v_type
    if isinstance(v_type, type):
        try:
            v_t = v_type()
        except:
            pass
    return v_t

# check the attribute, such as attribute reference. It's tedious to check, and it relates to attribute error checking.
class Attribute(Node):
    def __init__(self: 'Attribute', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)
        self.attr = ast_node.attr
        self.ctx = ast_node.ctx

    def check(self: 'Attribute') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .config import getFileName, getLineNo, getBName
        if self.lineno == -1 and self.value.lineno > 0:
            self.lineno = self.value.lineno
        setCurNode(self.value)
        self.value._ckd_result = None
        value_type = self.value.check()
        value_type = _get_type_from_ns(value_type)
        setLineNo(self.lineno)
        
        # Here is a bug for TE checking, if we set the value type int, then we will get wrong TE results. :->
        if isinstance(self.ctx, ast.Load):
            if hasattr(value_type, 'get_attribute'):
                setCurNode(self.value)
                v_type = _get_value_type(value_type)
                from .types import Class
                if isinstance(v_type, Class):
                    _attr_type = v_type.get_attribute(self.attr, self.value.prob \
                    if hasattr(self.value, 'prob') else  0.0)
                    _attr_type = _get_type_from_ns(_attr_type)
                    if not isinstance(_attr_type, data_types.Any):
                        self._ckd_result = _attr_type
                        #return _attr_type
                        return self._ckd_result

                    v_type = v_type.check_call([])
                if not hasattr(v_type, 'get_attribute'):
                    self._ckd_result = data_types.Any()
                    return self._ckd_result
                    #return data_types.Any()
                # get attribute of specific type.
                attr_type = v_type.get_attribute(self.attr, self.value.prob \
                    if hasattr(self.value, 'prob') else  0.0)
                #attr_type = _get_type_from_ns(attr_type)
                attr_type = _get_type_from_ns(attr_type)
                
                if self.attr == "append" \
                    and hasattr(v_type, 'elts') \
                    and hasattr(self, '_append'):
                    args = self._append
                    
                    for arg in args:
                        #arg = _get_type_from_ns(arg)
                        arg = _get_type_from_ns(arg)
                        v_type.elts.append(arg)
                    self._ckd_result = v_type
                    return self._ckd_result
                if isinstance(attr_type, data_types.Any)\
                    and self.attr in op_methods:
                    from .builtins.functions import BuiltinFunction
                    attr_type = BuiltinFunction(self.attr, [v_type], data_types.Any)
                    #attr_type = _get_type_from_ns(attr_type)
                    attr_type = _get_type_from_ns(attr_type)

                self._ckd_result = attr_type
                return attr_type
            # get attribute from the dict such as symbol table.
            elif isinstance(value_type, dict):
                if self.attr in value_type:
                    self._ckd_result = value_type[self.attr]
                    self._ckd_result = _get_type_from_ns(self._ckd_result)
                    return self._ckd_result
                    #return value_type[self.attr]
                elif hasattr(value_type, self.attr):
                    self._ckd_result = getattr(value_type, self.attr)
                    #self._ckd_result = _get_type_from_ns(self._ckd_result)
                    self._ckd_result = _get_type_from_ns(self._ckd_result)
                    return self._ckd_result
                    #return getattr(value_type, self.attr)
                else:
                    # if there is no attribute in value, we return Any instead.
                    #return value_type
                    self._ckd_result = data_types.Any()
                    return data_types.Any()
            else:
                # default attribute checking.
                from .config import getFileName
                try:
                    if value_type and hasattr(value_type, self.attr):
                        self._ckd_result = getattr(value_type, self.attr)
                        #self._ckd_result = _get_type_from_ns(self._ckd_result)
                        self._ckd_result = _get_type_from_ns(self._ckd_result)
                        return self._ckd_result
                except Exception:
                    self._ckd_result = getattr(value_type, self.attr)
                    self._ckd_result = _get_type_from_ns(self._ckd_result)
                    return self._ckd_result
                else:
                    self._ckd_result = data_types.Any()
                    return self._ckd_result
                    #return value_type
        elif isinstance(self.ctx, ast.Store):
            debug("Store self.attr %r", self.attr)
            return value_type
        else:
            # TODO implement for Del, AugLoad, AugStore, Param
            raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Attribute') -> str:
        attr_name = 'AttrNode' if not isinstance(self.value, Name) else self.value.id
        return attr_name + '.' + self.attr

# check the name node. we always get the identifier type by the name.
class Name(Node):
    def __init__(self: 'Name', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.id = ast_node.id
        self.ctx = ast_node.ctx

    def check(self: 'Name') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        tmp_node = getCurNode()
        setCurNode(self)
        if hasattr(self, 'prob_type') \
            and not isinstance(self.prob_type, data_types.Any):# and isinstance(self.prob_type, Union):
            writeTypes(f"name_prob_type:{self.prob_type}, {type(self.prob_type)}, probs:{self.prob}")
        # load the identifier type from the symbol table.
        if isinstance(self.ctx, ast.Load):
            if self.id in BUILTIN_TYPES \
                and not hasattr(self, 'func_call') \
                and self.id not in self.type_map.current_namespace:
                
                self._ckd_result = BUILTIN_TYPES[self.id]
                return self._ckd_result
                #return BUILTIN_TYPES[self.id]
            setCurNode(tmp_node)
            id_type = self.type_map.find(self.id)
            if isinstance(id_type, list):
                if len(id_type) < 2:
                    if isinstance(id_type[0], list):
                        id_type = id_type[0]
                    else:
                        self._ckd_result = id_type
                        return self._ckd_result
                        #return id_type
                
                self.prob = id_type[1]
                id_type = id_type[0]

            self._ckd_result = id_type
            return self._ckd_result
            #return id_type
        elif isinstance(self.ctx, ast.Store):
            setCurNode(tmp_node)
            self._ckd_result = self
            return self._ckd_result
            #return self
        else:
            # TODO implement for Del, AugLoad, AugStore, Param
            raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Name') -> str:
        return self.id

# Check attribute exists object.
def _has_attr(_obj: BaseType, _attr: str) -> bool:
    if hasattr(_obj, 'attributes') and _attr in _obj.attributes:
        return True
    return False

# builtin method issubclass call checking, arguments are class types instead instances.
def _issub_handler(args: List) -> None:
    from .types import Union as ProbType
    if isinstance(args[0][0], ProbType):
        [_issub_handler([[_type, prob], args[1]]) \
            for _type, prob in zip(args[0][0].elts, args[0][0].prob)]
    elif isinstance(args[1][0], ProbType) \
        or hasattr(args[1][0], 'elts'):
        [_issub_handler([args[0], [_type, prob]]) \
            for _type, prob in zip(args[1][0].elts, args[1][0].prob)]
    else:
        ARG_FLAG = False
        global sub_arg_names
        from . import error_cache
        from .error_condition import _subtype_checking
        # check the 1st parameter is class or instance.
        if _subtype_checking(args[0][0], config, error_cache):
            ARG_FLAG = True
            logging.error(f"[SubTypeError]: issubclass arg 1:{sub_arg_names[0]} should be a class, not {args[0][0]} with prob: <<{1 - args[0][1]}>> in file [[{config.getFileName()}:{config.getLineNo()}]]")
        # check the second parameter is class or instance.
        if _subtype_checking(args[1][0], config, error_cache):
            ARG_FLAG = True
            logging.error(f"[SubTypeError]: issubclass arg 2:{sub_arg_names[1]} should be a class, not {args[1][0]} with prob: <<{1 - args[1][1]}>> in file [[{config.getFileName()}:{config.getLineNo()}]]")
        #if not ARG_FLAG:
        #    logging.warning(f"[SubTypeWarning]: issubclass should be surrounded by try-except, or it may raise TypeError for {sub_arg_names[0], sub_arg_names[1]}:{args[0][0], args[1][0]} with prob:{args[0][1], args[1][1]} in file {config.getFileName(),config.getLineNo()}")

# return arguemtns list of function.
def getArgsList(_args: List) -> List:
    args = []
    global sub_arg_names
    sub_arg_names = []
    for arg in _args:
        arg._ckd_result = None
        arg_type = arg.check()
        if isinstance(arg, Name):
            sub_arg_names.append(arg.id)
        else:
            sub_arg_names.append(repr(arg))
        prob = 0.5
        if isinstance(arg_type, list):
            if hasattr(arg, 'prob'):
                arg_type[1] = arg.prob if len(arg_type) == 2 else arg_type.append(arg.prob) 
            args.append(arg_type)
        else:
            if hasattr(arg, 'prob'):
                prob = arg.prob
            args.append([arg_type, prob])
    return args

# is operator checking. 
def _attribute_call(func: BaseType, args: List) -> bool:
    attr = func.attr
    if attr == "__is__":
        target = func.value
        _args = getArgsList(args)
        global sub_arg_names
        _attribute_assign(target, _args) \
            if isinstance(target, Attribute) else _attribute_assign(func, _args)
        return True
        
    return False

# builtin method hasattr call checking.
def _hasattr_call(func: BaseType, args: List) -> bool:
    assert len(args) == 2
    if isinstance(args[0], Name) \
        and isinstance(args[1], Str):
        _obj = args[0].check()
        _attr = args[1].s
        result = _has_attr(_obj, _attr)
        return result
    return False

# subclass checking, and handle the subclass error.
def __subclass_check(args: List) -> None:
    from .error_condition import _is_subclass
    from .config import getLineNo

    if not _is_subclass(args[0][0], args[1][0]):
        _issub_handler(args)

# builtin method issubclass call checking.
def _issubclass_call(func: BaseType, args: List) -> bool:
    assert len(args) == 2
    from .config import getTypeError, setTypeError
    
    
    if not getTypeError():
        # For subtype checking, we set the probability of each arg 1.0.
        for arg in args:
            arg._ckd_result = None
            arg.prob = 1.0
         
        # Handle args[1] checking when it's tuple type.
        if isinstance(args[1], Tuple):
            proba = 1 / len(args[1].elts)
            
            for arg in args[1].elts:
                arg.prob = proba
                _args = getArgsList([args[0], arg])
                __subclass_check(_args)
            # For consistency, we always return False.
            return False
        _args = getArgsList(args)
        
        __subclass_check(_args)

        return False
    
    setTypeError(False)
    return True

# isinstance(arg1, arg2). Type of arg2 is usually builtin types or tuple of builtin types. 
# If the type of arg2 in ISINSTANCE_TYPES, we return it directly.
def _get_isinstance_arg_type(arg):
    
    #arg_type = arg.check()
    prob = 1.0
    if isinstance(arg, Name) and arg.id in ISINSTANCE_TYPES:
        arg_type = ISINSTANCE_TYPES[arg.id]
        arg.prob = prob
        return [arg_type, prob]
    elif isinstance(arg, Tuple):
        elt_types = []
        probs = [1 / len(arg.elts)] * len(arg.elts) if len(arg.elts) > 0 else 1.0
        for elt in arg.elts:
            #elt_types.append(_get_isinstance_arg_type(elt))
            elt_type, prob = _get_isinstance_arg_type(elt)
            if prob == -1:
                elt_type = elt.check()
            elt_types.append(elt_type)
        if elt_types:
            return [Union(None, elt_types, probs), prob]
    else:
        return [arg, -1]
    #if isinstance(arg_type, list):
    #    if hasattr(arg, 'prob'):
    #        arg_type[1] = arg.prob
    #    args.append(arg_type)
    #else:
    #    if hasattr(arg, 'prob'):
    #        prob = arg.prob
    #    args.append([arg_type, prob])
    #return args

def _isinstance_call(func: BaseType, args: List, type_map: Dict, ISNOT: bool = False) -> bool:
    assert len(args) == 2
    #from .config import getTypeError, setTypeError
    from .types import Tuple as TupleType, _get_type
    for arg in args:
        arg.prob = 1.0
    #arg_type = arg[1]
    arg_type = _get_isinstance_arg_type(args[1])
    if len(arg_type) == 2 and arg_type[1] == -1:
        arg_type = getArgsList([args[1]])
    arg = args[0]
    tmp_arg_type = arg_type
    arg_type = _get_type_from_ns(arg_type)
    # Handle args[1] checking when it's tuple type.
    if isinstance(arg_type, TupleType):
        proba = 1 / len(arg_type.elts) if len(arg_type.elts) else 1.0
            
        from .types import Union as ProbType
        
        arg_type = ProbType(type_map, arg_type.elts) if arg_type.elts else arg_type
    if hasattr(arg, 'id') and not ISNOT:
        type_map.add_variable(arg.id, arg_type)

        return True
    return False

# For compound types such as List, we need to handle the append method specially.
def _append_call(target, args):
    if isinstance(target, Attribute):
        target._append = args
        target._ckd_result = None
        result = target.check()
        return result
    return False
    
# call node checking including builtin function and function node call checking. 
# It's tedious and we need to handle the recursion checking.
class Call(Node):
    def __init__(self: 'Call', type_map: Dict, ast_node: AST) -> None:
        if hasattr(ast_node, "starargs") \
            and hasattr(ast_node, "kwargs"):
            if (len(ast_node.keywords) > 0 \
                or ast_node.starargs is not None \
                or ast_node.kwargs is not None):
                raise NotYetSupported('keyword arguments and star arguments')

        super().__init__(type_map, ast_node)
        self.func = convert(type_map, ast_node.func)
        self.args = [convert(type_map, expr) for expr in ast_node.args]
        self.keywords = [convert(type_map, kw) for kw in ast_node.keywords]

    def check(self: 'Call') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .config import getFileName, getLineNo
        
        probs = []
        if isinstance(self.func, Name):
            self.func.func_call = True
        # Handle the is comparison operator.
        if isinstance(self.func, Attribute):
            call_result = _attribute_call(self.func, self.args)
            if call_result:
                self._ckd_result = True
                return True

        func = self.func.check()
        func = _get_type_from_ns(func)
        #from . import config
        # check the hasattr method.
        if hasattr(func, 'name') \
            and func.name == 'hasattr':
            self._ckd_result = _hasattr_call(func, self.args)
            return self._ckd_result
            #return _hasattr_call(func, self.args)
        
        if hasattr(func, 'name') \
            and func.name == 'issubclass':
            
            self._ckd_result = _issubclass_call(func, self.args)
            return self._ckd_result
            #return _issubclass_call(func, self.args)

        if hasattr(func, 'name') \
            and func.name == 'isinstance':
                self._ckd_result = _isinstance_call(func, self.args, self.type_map, hasattr(self, '_not') and self._not is True)
                return self._ckd_result
                #return _isinstance_call(func, self.args, self.type_map)
        
        if self.lineno == -1 and self.func.lineno > 0:
            self.lineno = self.func.lineno
        args = [[arg.check(), arg.prob \
            if hasattr(arg, 'prob') else 0.5] for arg in self.args]
        for _arg in args:
            probs.append(_arg[1])
        tmp_arg = []
        # function arguments checking.
        arg_len = len(func.param_types) - len(args) \
            if hasattr(func, 'param_types') else 0
        arg_len = len(func.params) - len(args) \
            if hasattr(func, 'params') else 0
        arg_len = arg_len - len(self.keywords) \
            if self.keywords else arg_len
        setLineNo(self.lineno)
        
        for arg in self.args:
            index = self.args.index(arg)
            if isinstance(arg, Starred):
                if hasattr(args[index], 'elts'):
                    for elt in args[index].elts:
                        prob = elt.prob if hasattr(elt, 'prob') else 0.5
                        tmp_arg.append([elt, prob])
                        probs.append(prob)
                    arg_len -= len(args[index].elts)
                else:
                    prob = args[index].prob if hasattr(args[index], 'prob') else 0.5
                    tmp_arg.append([args[index], prob])
                    probs.append(prob)
                    for i in range(0, arg_len):
                        tmp_arg.append([data_types.Any(), 0.5])
                        probs.append(0.5)
                continue

            tmp_arg.append(args[index])
        args = tmp_arg
        keywords = [kw.check() for kw in self.keywords]
        if keywords:
            for kw in keywords:
                prob = kw.prob if hasattr(kw, 'prob') else 0.5
                args.append([kw, prob])
                #args.append(kw)
                probs.append(prob)
        # Method call checking.
        from .types import Method
        if hasattr(func, 'name') \
            and not isinstance(func, Method):
            ### We need to check the function call carefullay. Or it may be a bug !!!!
            from .builtins.functions import BuiltinFunction
            from .types import Function
            
            if isinstance(func, BuiltinFunction):
                result = func
            else:
                result = self.type_map.in_global(func.name, func)
                if result is not None:        
                    result = self.type_map.find(func.name)
                    #result = _get_type_from_ns(result)
                    result = _get_type_from_ns(result)
            if result is not None \
                and hasattr(result, 'check_call') \
                and isinstance(result, BuiltinFunction):
                if result.name == "append":
                    self._ckd_result = _append_call(self.func, args)
                    if self._ckd_result is not False:
                        return self._ckd_result
                result = result.check_call(args, probs)\
                    if not self.type_map.in_global(func.name, func) else result.return_type
                #result = _get_type_from_ns(result)
                result = _get_type_from_ns(result)
                self._ckd_result = result
                return self._ckd_result
            elif result is not None \
                and hasattr(result, 'check_call') \
                and isinstance(result, Function):
                #Here we need to avoid the recursive_function call
                result = _recursive_funccall(result, args, probs)
                #result = _get_type_from_ns(result)
                result = _get_type_from_ns(result)
                self._ckd_result = result
                return self._ckd_result
            else:
                if hasattr(func, "check_call"):
                    result = _recursive_funccall(func, args, probs)
                    #result = _get_type_from_ns(result)
                    result = _get_type_from_ns(result)
                    self._ckd_result = result
                    return self._ckd_result
        elif isinstance(func, Method):
            result = _recursive_funccall(func, args, probs)
            #result = _get_type_from_ns(result)
            result = _get_type_from_ns(result)
        else:
            result = None
        if func is data_types.Any:
            self._ckd_result = data_types.Any()
            return self._ckd_result
            #return data_types.Any()
        if not result \
            and func is not None \
            and hasattr(func, 'check_call'):
            if not hasattr(func, 'name'):
                result = func.check_call(args, probs)
                #result = _get_type_from_ns(result)
                result = _get_type_from_ns(result)
                self._ckd_result = result
                return self._ckd_result
                #return result
            result = _recursive_funccall(func, args, probs)
            #result = _get_type_from_ns(result)
            result = _get_type_from_ns(result)
        else:
            from .builtins.functions import BuiltinFunction
            if isinstance(func, list):
                for _func in func:
                    if hasattr(_func, 'check_call') \
                        and isinstance(_func, BuiltinFunction):
                        result = _func.check_call(args, probs)
                        #result = _get_type_from_ns(result)
                        result = _get_type_from_ns(result)
        self._ckd_result = result
        return self._ckd_result
        #return result

    def __repr__(self: 'Call') -> str:
        return repr(self.func) + \
               '(' + ', '.join(repr(x) for x in self.args) + ')'

# check the expression, we only check the value node.
class Expr(Node):
    def __init__(self: 'Expr', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)
    def check(self: 'Expr') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setCurNode(self.value)
        result = self.value.check()
        #result = _get_type_from_ns(result)
        result = _get_type_from_ns(result)
        setLineNo(self.lineno)
        
        if isinstance(result, str):
            from . import config
            self._ckd_result = data_types.Any()
            return self._ckd_result
            #return data_types.Any()
        self._ckd_result = result
        return self._ckd_result
        #return result

    def __repr__(self: 'Expr') -> str:
        return repr(self.value)

# check the return statement, and return the value field.
class Return(Node):
    def __init__(self: 'Return', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'Return') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        setCurNode(self.value)
        return_type = self.value.check()
        #return_type = _get_type_from_ns(return_type)
        return_type = _get_type_from_ns(return_type)
        self._ckd_result = return_type
        return self._ckd_result
        #return self.value.check()

    def __repr__(self: 'Return') -> str:
        return 'return ' + repr(self.value)

# Annotation Assignment statement checking.
class AnnAssign(Node):
    def __init__(self: 'AnnAssign', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.target)
        self.annotation = convert(type_map, ast_node.annotation)
        self.value = convert(type_map, ast_node.value)
        self._ast_fields = ('target', 'annotation', 'value')

    def check(self: 'AnnAssign') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from .builtins.data_types import NoneType, UnDefined

        setLineNo(self.lineno)
        tmp_node = getCurNode()
        setCurNode(self)
        if isinstance(self.value, NoneType):
            self.value = UnDefined()
        if hasattr(self, '_class_'):
            self.target._class_ = getattr(self, '_class_')
        result = _annassign(self.target, self.annotation, self.value, self.type_map)
        #result = _get_type_from_ns(result)
        result = _get_type_from_ns(result)
        setCurNode(tmp_node)
        self._ckd_result = result
        return self._ckd_result
        #return result

    def __repr__(self: 'AnnAssign') -> str:
        return repr(self.target) + ':' + repr(self.annotation) + '=' + repr(self.value)

# Check the assignment statement. For the instance field reference, we need to update the class attributes.
class Assign(Node):
    def __init__(self: 'Assign', type_map: Dict, ast_node: AST) -> None:
        # TODO handle multiple targets

        super().__init__(type_map, ast_node)
        self.targets = [convert(type_map, target) \
            for target in ast_node.targets]
        self.value = convert(type_map, ast_node.value)
        self._ast_fields = ('target', 'value')

    def check(self: 'Assign') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        debug('checking assign %r = %r %d', self.targets, self.value, self.lineno)
        if hasattr(self, '_orelse'):
            for targ in self.targets:
                targ._orelse = True
        
        setLineNo(self.lineno)
        tmp_node = getCurNode()
        setCurNode(self)
        for target in self.targets:
            target.prob = 1.0
            if hasattr(self, '_class_'):
                target._class_ = getattr(self, '_class_')
            self.value._ckd_result = None
            result = _assign(target, self.value, self.type_map)
            #result = _get_type_from_ns(result)
            result = _get_type_from_ns(result)
        # check the instance reference assignment, and update the attributes.
        if hasattr(self, '_class') and getTargetName(self.targets[0]) is 'self':
            _cls_type = self.type_map.find(self._class)
            #_cls_type = _get_type_from_ns(_cls_type)
            _cls_type = _get_type_from_ns(_cls_type)
            self.type_map.add_variable('self', _cls_type, 1.0)
            setCurNode(tmp_node)
            self_type = self.type_map.find('self')
            #self_type = _get_type_from_ns(self_type)
            self_type = _get_type_from_ns(self_type)
            self._ckd_result = self_type
            return self._ckd_result
            #return self_type
        setCurNode(tmp_node)
        self._ckd_result = self.value
        return self._ckd_result
        #return self.value

    def __repr__(self: 'Assign') -> str:
        return repr(self.targets) + ' = ' + repr(self.value)

# check the AugAssigment statement, var += 1
class AugAssign(Node):
    def __init__(self: 'AugAssign', type_map: Dict, ast_node: AST) -> None:
        # TODO handle multiple targets

        super().__init__(type_map, ast_node)
        
        self.target = convert(type_map, ast_node.target)
        self.value = convert(type_map, ast_node.value)
        self.op = ast_node.op
        self.op_name = ast_node.op.__class__.__name__
        if self.op_name == 'Mult':
            self.op_name = 'Mul'
        self._ast_fields = ('target', 'op', 'value')

    def check(self: 'AugAssign') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        
        t_type = self.type_map.find(getTargetName(self.target))
        #t_type = _get_type_from_ns(t_type)
        t_type = _get_type_from_ns(t_type)
        setCurNode(self.value)
        v_type = self.value.check()
        #v_type = _get_type_from_ns(v_type)
        v_type = _get_type_from_ns(v_type)
        if not self.op_name.startswith("__") \
            or not self.op_name.endswith("__"):
            self.op_name = "__%s__" % self.op_name.lower()
        setLineNo(self.lineno)
        targ_prob = self.target.prob \
            if hasattr(self.target, 'prob') else 0.5
        value_prob = self.value.prob \
            if hasattr(self.value, 'prob') else 0.5
        # binary operator checking.
        temp = binop_check(t_type, v_type, self.op_name, targ_prob, value_prob)
        if isinstance(temp, str):
            from . import config
            temp = data_types.Any()
        try:
            temp.check()
        except TypeError:
            temp = temp()
        except AttributeError:
            pass
        setLineNo(self.lineno)
        _assign(self.target, temp, self.type_map)
        #temp = _get_type_from_ns(temp)
        temp = _get_type_from_ns(temp)
        self._ckd_result = temp
        return self._ckd_result
        #return temp

    def __repr__(self: 'AugAssign') -> str:
        return repr(self.target) + ' = ' + repr(self.value)

# check the pass statement, return builtin type directly.
class Pass(Node):
    
    def check(self: 'Pass') -> BaseType:
        setLineNo(self.lineno)
        return data_types.None_()

    def __repr__(self: 'Pass') -> str:
        return 'pass'

# check the not node, we return bool type directly.
class Not(Node):
    def __init__(self: 'Not', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'Not') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        self.value._not = True
        self.value.check()

        setLineNo(self.lineno)
        self._ckd_result = data_types.Bool()
        return self._ckd_result
        #return data_types.Bool()

    def __repr__(self: 'Not') -> str:
        return 'not ' + repr(self.value)

# we return bool type directly.
class BoolOp(Node):
    def __init__(self: 'BoolOp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.op = ast_node.op
        self.values = [value for value in ast_node.values]
        self.values_type = [convert(type_map, value) \
            for value in ast_node.values]

    def check(self: 'BoolOp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        # Here we should visit the self.values_type
        for value in self.values_type:
            if hasattr(value, 'check'):
                value.check()
        setLineNo(self.lineno)
        # TODO return intersection van types?
        self._ckd_result = data_types.Bool()
        return self._ckd_result
        #return data_types.Bool()

    def __repr__(self: 'BoolOp') -> str:
        op_name = ' {} '.format(self.op)
        return '(' + op_name.join(repr(val) for val in self.values) + ')'

# check the in node. we need to check the element and container.
class In(Node):
    def __init__(self: 'In', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.element = convert(type_map, ast_node.element)
        self.container = convert(type_map, ast_node.container)

    def check(self: 'In') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        element = self.element.check()
        #element = _get_type_from_ns(element)
        element = _get_type_from_ns(element)
        container = self.container.check()
        #container = _get_type_from_ns(container)
        container = _get_type_from_ns(container)
        setLineNo(self.lineno)
        try:
            container.call_magic_method('__contains__', element)
        except NoSuchAttribute:
            if not container.is_iterable():
                raise NotIterable(container)
        except AttributeError:
            logging.error(f"[InAttrError] container:{container} has no attr call_magic_method while checking in node.")
        except TypeError:
            logging.warning("In node container is a class not instance.")
        self._ckd_result = data_types.Bool()
        return self._ckd_result
        #return data_types.Bool()

    def __repr__(self: 'In') -> str:
        return '{!r} in {!r}'.format(self.element, self.container)

# check the for loop statement.
class For(Node):
    def __init__(self: 'For', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.target)
        self.iter = convert(type_map, ast_node.iter)
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.orelse = [convert(type_map, clause) \
            for clause in ast_node.orelse]

    def check(self: 'For') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        iterator = self.iter.check()
        from .builtins.functions import BuiltinFunction as BltFun
        if hasattr(iterator, 'get_enclosed_type') \
            and not isinstance(iterator, BltFun) \
            and not isinstance(iterator, data_types.Any):
            enclosed_type = iterator.get_enclosed_type()
            #enclosed_type = _get_type_from_ns(enclosed_type)
            enclosed_type = _get_type_from_ns(enclosed_type)
            _assign(self.target, enclosed_type, self.type_map)
        elif iterator is not None \
            and not isinstance(iterator, BltFun):
            try:
                if isinstance(self.target, Tuple) \
                    and hasattr(iterator, 'elts') \
                    and len(self.target.elts) == len(iterator.elts):
                    for target, iter in zip(self.target.elts, iterator):
                        _assign(target, iter, self.type_map)
                else:    
                    for iter in iterator:

                        if iter:
                            _assign(self.target, iter, self.type_map)
            except TypeError as te:
                _except_handler()
                # if the iterator is not iterated, we set Any instead.
                _assign(self.target, data_types.Any(), self.type_map)

        for stmt in self.body:
            stmt.check()
        if self.orelse and isinstance(self.orelse, list):
            for stmt in self.orelse:
                stmt.check()
        setLineNo(self.lineno)
        # TODO return intersection of values of both branches
        self._ckd_result = data_types.None_()
        return self._ckd_result
        #return data_types.None_()

    def __repr__(self: 'For') -> str:
        s = 'for {!r} in {!r}:\n    '.format(self.target, self.iter)
        s += '\n    '.join(repr(stmt) for stmt in self.body)
        if self.orelse:
            s += 'else:\n    '
            s += '\n    '.join(repr(stmt) for stmt in self.orelse)
        return s

# check async for statement, similar with for statement checking.
class AsyncFor(Node):
    def __init__(self: 'AsyncFor', type_map: Dict, ast_node: AST) -> None: 
        super().__init__(type_map, ast_node) 
        self.target = convert(type_map, ast_node.target) 
        self.iter = convert(type_map, ast_node.iter) 
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body] 
        self.orelse = [convert(type_map, clause) \
            for clause in ast_node.orelse] 
 
    def check(self: 'AsyncFor') -> BaseType: 
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        iterator = self.iter.check() 
        from .builtins.functions import BuiltinFunction as BltFun
        if hasattr(iterator, 'get_enclosed_type') \
            and not isinstance(iterator, BltFun) \
            and not isinstance(iterator, data_types.Any):
            enclosed_type = iterator.get_enclosed_type()
            #enclosed_type = _get_type_from_ns(enclosed_type)
            enclosed_type = _get_type_from_ns(enclosed_type)
            _assign(self.target, enclosed_type, self.type_map) 
        elif iterator is not None \
            and not isinstance(iterator, BltFun): 
            try: 
                for iter in iterator: 
                    if iter: 
                        _assign(self.target, iter, self.type_map) 
            except TypeError as te: 
                _except_handler()
                _assign(self.target, iterator, self.type_map) 
 
        for stmt in self.body: 
            stmt.check() 
        if self.orelse and isinstance(self.orelse, list): 
            for stmt in self.orelse: 
                stmt.check() 
        setLineNo(self.lineno) 
        # TODO return intersection of values of both branches 
        self._ckd_result = data_types.None_()
        return self._ckd_result
        #return data_types.None_() 
 
    def __repr__(self: 'AsyncFor') -> str: 
        s = 'for {!r} in {!r}:\n    '.format(self.target, self.iter) 
        s += '\n    '.join(repr(stmt) for stmt in self.body) 
        if self.orelse: 
            s += 'else:\n    ' 
            s += '\n    '.join(repr(stmt) for stmt in self.orelse) 
        return s 

# check the if statement, and we need to check the body for some special condition.
class If(Node):
    def __init__(self: 'If', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.test = convert(type_map, ast_node.test)
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.orelse = [convert(type_map, stmt) \
            for stmt in ast_node.orelse]

    def check(self: 'If') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        # TODO take isinstance into account (?)
        # TODO real branching?
        if not hasattr(self, '_class_'):
            self.type_map.enter_namespace('If_Branch')
        self.test._ckd_result = None
        test_result = self.test.check()
        #test_result = _get_type_from_ns(test_result)
        test_result = _get_type_from_ns(test_result)
        if isinstance(test_result, bool) \
            and not test_result:
           return_type = data_types.None_()
           self._ckd_result = return_type
           return self._ckd_result
           #return return_type
        return_type = []
        for stmt in self.body:
            # here if we reset the stmt.orelse = self.orelse, then we may recheck the orelse stmts
            if hasattr(self, '_orelse'):
                stmt._orelse = self._orelse
            else:
                stmt._orelse = True
            if isinstance(stmt, Return):
                rt = stmt.check()
                if isinstance(rt, list) \
                    and len(rt) == 2 \
                    and isinstance(rt[1], float):
                    rt = rt[0]
                return_type.append(rt)
                continue
            # if stat in the classdef, we set the _class_ attribute to collect the class fields.
            if hasattr(self, '_class_'):
                stmt._class_ = self._class_
            stmt.check()
        if not hasattr(self, '_class_'):
            self.type_map.exit_namespace()
        if isinstance(self.orelse, list):
            for stmt in self.orelse:
                # here if we set the If.orelse = True, then we lose some branches.
                stmt._orelse = True
                # here we should use the if elif, or we will duplicate check the stmts. :-)
                if isinstance(stmt, Return):
                    rt = stmt.check() 
                    if isinstance(rt, list) \
                        and len(rt) == 2 \
                        and isinstance(rt[1], float): 
                        rt = rt[0]
                    return_type.append(rt)
                    continue
                elif isinstance(stmt, If):
                    rts = stmt.check()
                    for rt in rts:
                        return_type.append(rt)
                else:
                    stmt.check()
        setLineNo(self.lineno)
        if not return_type:
            return_type.append(data_types.None_())
        # TODO return intersection of values of both branches
        self._ckd_result = return_type
        return self._ckd_result
        #return return_type

    def __repr__(self: 'If') -> str:
        s = 'if {!r}:\n    '.format(self.test)
        s += '\n    '.join(repr(stmt) for stmt in self.body)
        if self.orelse:
            s += 'else:\n    '
            s += '\n    '.join(repr(stmt) for stmt in self.orelse)
        return s

# check the ifexp node in some statement.
class IfExp(Node):
    def __init__(self: 'IfExp', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.test = convert(type_map, ast_node.test)
        self.body = convert(type_map, ast_node.body)
        self.orelse = convert(type_map, ast_node.orelse)

    def check(self: 'IfExp') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        debug('checking ifexp')

        # TODO take isinstance into account (?)
        self.test.check()
        value1 = self.body.check()
        #value1 = _get_type_from_ns(value1)
        value1 = _get_type_from_ns(value1)
        value2 = data_types.Any()
        if hasattr(self.orelse, 'check'):
            value2 = self.orelse.check()
        setLineNo(self.lineno)
        self._ckd_result = types.Intersection(value1, value2)
        return self._ckd_result
        #return types.Intersection(value1, value2)

    def __repr__(self: 'IfExp') -> str:
        template = '{!r} if {!r} else {!r}'
        return template.format(self.test, self.body, self.orelse)

# check constan node, and return the types directly.
class NameConstant(Node):
    def __init__(self: 'NameConstant', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = ast_node.value
        self.prob = 0.95

    def check(self: 'NameConstant') -> BaseType:
        debug('checking name constant %r', self.value)
        setLineNo(self.lineno)
        setTypeProb(self.prob)
        if self.value is None:
            return data_types.None_()
        elif self.value is True \
            or self.value is False:
            return data_types.Bool
        else:
            raise NotYetSupported('name constant', self.value)

    def __repr__(self: 'NameConstant') -> str:
        return repr(self.value)

# check the while loop statement.
class While(Node):
    def __init__(self: 'While', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.test = convert(type_map, ast_node.test)
        self.body = [convert(type_map, stmt) \
            for stmt in ast_node.body]
        self.orelse = [convert(type_map, stmt) \
            for stmt in ast_node.orelse]

    def check(self: 'While') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        debug('checking while')

        # TODO take isinstance into account (?)
        # TODO real branching?
        self.test.check()
        return_type = data_types.None_()
        for stmt in self.body:
            if isinstance(stmt, Return):
                return_type = stmt.check()
                continue
            stmt.check()
        if self.orelse \
            and isinstance(self.orelse, list):
            for stmt in self.orelse:
                if isinstance(stmt, Return):
                    return_type = stmt.check()
                    continue
                stmt.check()
        setLineNo(self.lineno)
        # TODO return intersection of values of both branches
        self._ckd_result = return_type
        return self._ckd_result
        #return return_type

    def __repr__(self: 'While') -> str:
        s = 'while {!r}:\n    '.format(self.test)
        s += '\n    '.join(repr(stmt) for stmt in self.body)
        if self.orelse:
            s += 'else:\n    '
            s += '\n    '.join(repr(stmt) for stmt in self.orelse)
        return s

# check the break node, and we return directly.
class Break(Node):
    def check(self: 'Break') -> BaseType:
        setLineNo(self.lineno)
        return data_types.None_()

    def __repr__(self: 'Break') -> str:
        return 'break'

# check the continue node, and we return directly.
class Continue(Node):
    def check(self: 'Continue') -> BaseType:
        setLineNo(self.lineno)
        return data_types.None_()

    def __repr__(self: 'Continue') -> str:
        return 'continue'

# check the num node, and we return builtin type directly.
class Num(Node):
    def __init__(self: 'Num', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.n = ast_node.n
        self.number_type = {
            bool: data_types.Bool,
            int: data_types.Int,
            float: data_types.Float,
            complex: data_types.Complex,
        }[type(ast_node.n)]
        self.prob = 1.0

    def check(self: 'Num') -> BaseType:
        setLineNo(self.lineno)
        setTypeProb(self.prob)
        # remove '()' type.int(), thus return number_type instead number_type()
        return self.number_type()

# check the import statement, we need to handle import statement in specific module.
class Import(Node):
    def __init__(self: 'Import', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.names = []
        self.asnames = {}
        # check the module names in the import statement.
        for name in ast_node.names:
            if isinstance(name, str):
                self.names.append(name)
            else:
                self.names.append(name.name)
                if not(name.asname is None):
                    self.asnames[name.name] = name.asname
    
    def check(self: 'Import') -> None:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        from . import imports_handler
        setLineNo(self.lineno)
        import sys
        from . import config
        for name in self.names:
            mod = imports_handler.checkimport(name, sys.path)
            self._ckd_result = mod
            if name in self.asnames:
                self.type_map.add_module(self.asnames[name], mod)
            else:
                self.type_map.add_module(name, mod)

# check the importfrom statement, we need to add the names into the current namespace.
class ImportFrom(Node):
    def __init__(self: 'ImportFrom', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        
        self.module = ast_node.module
        self.names = []
        self.asnames = {}
        self.level = ast_node.level
        
        for name in ast_node.names:
            if isinstance(name, str): 
                self.names.append(name) 
            else: 
                self.names.append(name.name) 
                if not(name.asname is None): 
                    self.asnames[name.name] = name.asname
        for name in self.names:
            self.type_map.add_undefined(name, data_types.Any())

    def check(self: 'ImportFrom') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        # get the absolute path of the module.Then we can import it in the imports handler moudle.
        def get_path(modname: str, tpath: str,  path: List) -> UnionType[str, bool]:
            for dir in path:
                if os.path.isfile(os.path.sep.join([dir, modname, '.py'])):
                    return dir
                elif os.path.isdir(os.path.sep.join([dir, modname])) \
                    and os.path.isfile(os.path.sep.join([dir,modname, '__init__.py'])):
                    return dir
            else:  # recall that a for's else is executed if the for is not break-ed
                for dir in path:
                    if os.path.isfile(os.path.sep.join([dir, modname, '.pyi'])):
                        return dir
                else:
                    if modname in sys.builtin_module_names:
                        return modname
                    return ""
                    #return False
                    from . import exceptions
                    raise exceptions.StaticImportError(self, 'Typechecker could not find type definitions for module {}'.format('.'.join(tpath)))
            return False
        
        from . import imports_handler
        # handle the relative import.  
        self.level += len(self.module.split('.')) - 1 if self.module else 0
        
        if self.level == 0:
            path = self.module.split(".")
        else:
            from . import config
            from .builtins.data_types import Any
            directory = os.path.abspath(config.getFileName())
            endpoint = -(self.level - 1) \
                if self.level > 1 else len(directory.split(os.path.sep))
            searchpath = os.path.sep.join(directory.split(os.path.sep)[:endpoint - 1])
            # the module is specific name.
            if self.module:
                path = self.module.split('.')
                path = [os.path.sep.join(path)]
                for pth in path:
                    filepath = os.path.sep.join([searchpath, pth])

                    mod_type = imports_handler.checkimport(filepath, sys.path)
                    
                    if not isinstance(mod_type, Any):
                        for name in self.names:
                            if name == '*':
                                for key, value in mod_type.items():
                                    proba = 1.0
                                    if isinstance(value, list) \
                                        and len(value) == 2:
                                        proba = value[1]
                                        value = value[0]
                                    
                                    from .config import setImportFrom, getImportFrom
                                    tmpImp = getImportFrom()

                                    self.type_map.add_variable(key, value, 1.0)
                                    setImportFrom(tmpImp)
                            else:
                                proba = 1.0 if name in mod_type else 0.0
                                value = mod_type[name] if name in mod_type else Any()
                                if isinstance(value, list ) \
                                    and len(value) == 2:
                                    proba = value[1]
                                    value = value[0]
                                self.type_map.add_variable(name, value, proba)
                        break
                    else:
                        for name in self.names:
                            filepath = os.path.sep.join([filepath, name])
                            mod_type = imports_handler.checkimport(filepath, sys.path)
                            #self._ckd_result = mod_type
                            if not isinstance(mod_type, Any):
                                if name in self.asnames:
                                    self.type_map.add_module(self.asnames[name], mod_type)
                                else:
                                    self.type_map.add_module(name, mod_type)
                self._ckd_result = data_types.Any()
                return self._ckd_result
            else:
                # check the relative import.
                path = [searchpath.split(os.path.sep)[-1]]
                for name in self.names:
                    filepath = os.path.sep.join([searchpath, name])
                    mod_type = imports_handler.checkimport(filepath, sys.path)
                    #self._ckd_result = mod_type
                    if not isinstance(mod_type, Any) \
                        and name in mod_type.keys():
                        value = mod_type[name]
                        proba = 1.0
                        if isinstance(value, list) \
                            and len(value) == 2:
                            proba = value[1]
                            value = value[0]
                        self.type_map.add_variable(name, value, proba)
                    if name in self.asnames:
                        self.type_map.add_module(self.asnames[name], mod_type)
                    else:
                        self.type_map.add_module(name, mod_type)
                self._ckd_result = data_types.Any()
                return self._ckd_result
         
        root_dir = get_path(path[0], path, sys.path)
        search_path = path[0] if root_dir is False or root_dir == "" else os.path.sep.join([root_dir, path[0]])
        #p_type = imports_handler.checkimport(path[0], sys.path)
        p_type = imports_handler.checkimport(search_path, sys.path)

        root_dir = os.path.sep.join([root_dir, path[0]])
        for pth in path[1:]:
            root_dir = os.path.sep.join([root_dir, pth])
            next_type = imports_handler.checkimport(path[0], sys.path)
            p_type = next_type
        
        mod = p_type
        setLineNo(self.lineno)
        if isinstance(mod, dict):
            #self._ckd_result = mod
            for name in self.names:
                if name in mod:
                    value = mod[name]
                    proba = 1.0
                    if isinstance(value, list) \
                        and len(value) == 2:
                        proba = value[1]
                        value = value[0]
                    self.type_map.add_variable(name, value, proba)
        else:
            #self._ckd_result = data_types.Any()
            for name in self.asnames:
                self.type_map.add_variable(name, data_types.Any(), 0.0)
        self._ckd_result = data_types.Any()
        
# check the assert node, we return directly. 
class Assert(Node):
    def __init__(self: 'Assert', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.msg = ast_node.msg
        self.test = ast_node.test

    def check(self: 'Assert') -> BaseType:
        setLineNo(self.lineno)
        return data_types.None_()

# check the tuple statment, and return builtin tuple type instead.
class Tuple(Node):
    def __init__(self: 'Tuple', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        # check the elements of Tuple type.
        self.elts = [convert(type_map, el) \
            for el in ast_node.elts]
        self.ctx = ast_node.ctx

    def check(self: 'Assert') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        # we change the Tuple __init__(type_map, elements)
        # if there is no prob of the element in tuple, so we set the average value as the probability.
        if self.elts:
            probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                for el in self.elts]
        else:
            probs = []
        if isinstance(self.ctx, ast.Load):
            el_types = [el.check() for el in self.elts]
            setLineNo(self.lineno)
            
            self._ckd_result = types.Tuple(self.type_map, el_types, probs)
            return self._ckd_result
            #return types.Tuple(self.type_map, el_types, probs)
        elif isinstance(self.ctx, ast.Store):
            self._ckd_result = types.Tuple(None, self.elts, probs)
            return self._ckd_result
            #return types.Tuple(None, self.elts, probs)
        else:
            # TODO implement for Del, AugLoad, AugStore, Param
            raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Assert') -> str:
        return '(' + ', '.join(repr(el) for el in self.elts) + ')'

# check the set statement, similar with list statement.
class Set(Node):
    def __init__(self: 'Set', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.elts = [convert(type_map, el) \
            for el in ast_node.elts]

    def check(self: 'Set') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        if self.elts: 
            probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                for el in self.elts] 
        else: 
            probs = []
        el_types = [el.check() for el in self.elts]
        setLineNo(self.lineno)
        self._ckd_result = types.Set(self.type_map, el_types, probs)
        return self._ckd_result
        #return types.Set(self.type_map, el_types, probs)
        # TODO implement for Del, AugLoad, AugStore, Param
        # raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Set') -> str:
        return '{' + ', '.join(repr(el) for el in self.elts) + '}'

# check the list statement, similar with tuple.
class List(Node):
    def __init__(self: 'List', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.elts = [convert(type_map, el) \
            for el in ast_node.elts]
        self.ctx = ast_node.ctx

    def check(self: 'List') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        if self.elts: 
            probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                for el in self.elts] 
        else: 
            probs = []
        if isinstance(self.ctx, (ast.Load, ast.Store)):
            el_types = [el.check() for el in self.elts]
            setLineNo(self.lineno)
            self._ckd_result = types.List(self.type_map, el_types, probs)
            return self._ckd_result
            #return types.List(self.type_map, el_types, probs)
        #elif isinstance(self.ctx, ast.Store):
        #    return self
        else:
            # TODO implement for Del, AugLoad, AugStore, Param
            raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'List') -> str:
        return '[' + ', '.join(repr(el) for el in self.elts) + ']'

# check the dict statement.
class Dict(Node):
    def __init__(self: 'Dict', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.keys = [convert(type_map, k) \
            for k in ast_node.keys]
        self.values = [convert(type_map, v) \
            for v in ast_node.values]

    def check(self: 'Dict') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        if self.values: 
            probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.values) \
                for el in self.values] 
        else: 
            probs = []
        k_types = [k.check() for k in self.keys]
        v_types = [v.check() for v in self.values]
        setLineNo(self.lineno)
        self._ckd_result = types.Dict(self.type_map, k_types, v_types, probs)
        return self._ckd_result
        #return types.Dict(self.type_map, k_types, v_types,probs)
        # TODO implement for Del, AugLoad, AugStore, Param
        # raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Dict') -> str:
        length = len(self.keys)
        return '{' + ', '.join(repr(self.keys[i])+':'+ repr(self.values[i]) for i in range(length)) + '}'

# check the self-defined statement variable declaration.
class VarDecl(Node):
    def __init__(self: 'VarDecl', type_map: Dict, ast_node: AST) -> None:
        if len(ast_node.targets) > 1:
            raise NotYetSupported("VarDecl assignment with multiple targets")

        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.targets[0])
        self.annotation = convert(type_map, ast_node.annotation)
        self.value = convert(type_map, ast_node.value)
        self._ast_fields = ('target', 'annotation', 'value')
    def check(self: 'VarDecl') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        setTypeProb(self.prob)
        _annassign(self.target, self.annotation, self.value, self.type_map)
        self._ckd_result = data_types.None_()
        return self._ckd_result
        #return data_types.None_()

    def __repr__(self: 'VarDecl') -> str:
        return repr(self.target) + ':' + repr(self.annotation) + '=' + repr(self.value)

# check the self-defined constant declaration.
class ConstDecl(Node):
    def __init__(self: 'ConstDecl', type_map: Dict, ast_node: AST) -> None:
        if len(ast_node.targets) > 1:
            raise NotYetSupported("ConstDecl assignment with multiple targets")

        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.targets[0])
        self.annotation = convert(type_map, ast_node.annotation)
        self.value = convert(type_map, ast_node.value)
        self._ast_fields = ('target', 'annotation', 'value')

    def check(self: 'ConstDecl') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        setTypeProb(self.value.prob)
        _annassign(self.target, self.annotation, self.value, self.type_map, True)
        self._ckd_result = data_types.None_()
        return self._ckd_result
        #return data_types.None_()

    def __repr__(self: 'ConstDecl') -> str:
        return repr(self.target) + ':' + repr(self.annotation) + '=' + repr(self.value)

# check the self-defined type definition statement.
class TypeDef(Node):
    def __init__(self: 'TypeDef', type_map: Dict, ast_node: AST) -> None:
        # TODO handle multiple targets

        super().__init__(type_map, ast_node)
        self.target = convert(type_map, ast_node.target)
        self.value = convert(type_map, ast_node.value)
        self._ast_fields = ('target', 'value')

    def check(self: 'TypeDef') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        setTypeProb(self.value.prob)
        _typeassign(self.target, self.value, self.type_map)
        self._ckd_result = data_types.None_()
        return data_types.None_()

    def __repr__(self: 'TypeDef') -> str:
        return repr(self.target) + ' = ' + repr(self.value)

# check the subscript statement, we need to check the value and slice.
class Subscript(Node):
    def __init__(self: 'Subscript', type_map: Dict, ast_node: AST) -> None:
        # TODO handle multiple targets
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)
        self.slice = convert(type_map, ast_node.slice)
        self.ctx = ast_node.ctx

    def check(self: 'Subscript') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        setLineNo(self.lineno)
        if isinstance(self.ctx, ast.Load):
            # check different kinds of slice.
            if not hasattr(self, 'elts') \
                and isinstance(self.slice, Index):
                elts = self.slice.value
                if not isinstance(elts, Tuple):
                    elts = (elts, )
                else:
                    elts = elts.elts
                self.elts = elts
            if isinstance(self.slice, Slice):
                elts = self.slice.check()
                #elts = _get_type_from_ns(elts)
                elts = _get_type_from_ns(elts)
                self.elts = elts.elts if hasattr(elts, 'elts') else elts
            value_name = self.value
            if isinstance(self.value, Name):
                value_name = self.value.id
            # check different compound types.
            if value_name == "Union" \
                or value_name == 'Optional':
                if self.elts: 
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                        for el in self.elts]
                else: 
                    probs = []
                el_types = []
                for el in self.elts:
                    if not isinstance(el, Str):
                        el_type = el.check()
                    else:
                        el_type = self.type_map.find(el.s)
                    #el_type = _get_type_from_ns(el_type)
                    el_type = _get_type_from_ns(el_type)
                    el_types.append(el_type)
                if value_name == "Optional":
                    el_types.append(data_types.NoneType)
                    probs = [0.5, 0.5]
                setLineNo(self.lineno)
                self._ckd_result = types.Union(self.type_map, el_types, probs)
                return self._ckd_result
                #return types.Union(self.type_map, el_types, probs)
            elif value_name == "Type":
                 
                if self.elts: 
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                        for el in self.elts]
                else: 
                    probs = []
                el_types = []
                for el in self.elts:
                    if not isinstance(el, Str):
                        el_type = el.check()
                    else:
                        el_type = self.type_map.find(el.s)
                    el_type = _get_type_from_ns(el_type)
                    el_types.append(el_type)
                setLineNo(self.lineno)
                if len(el_types) > 0 and len(probs) > 0:
                    self._ckd_result = [el_types[0], probs[0]]
                else:
                    self._ckd_result = [data_types.Any(), 0.5]
                return self._ckd_result
            elif value_name == "Tuple":
                if self.elts:  
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) for el in self.elts]  
                else:  
                    probs = [] 
                el_types = [el.check() for el in self.elts]
                try:
                    setLineNo(self.lineno)
                    self._ckd_result = types.Tuple(self.type_map, el_types, probs)
                    return self._ckd_result
                    #return types.Tuple(self.type_map, el_types, probs)
                except Exception as e:
                    _except_handler()
            elif value_name == "Set" \
                or value_name == 'AbstractSet':
                if self.elts:                                                                       
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                        for el in self.elts]
                else:   
                    probs = []
                el_types = [el.check() for el in self.elts]
                try:
                    setLineNo(self.lineno)
                    
                    self._ckd_result = types.Set(self.type_map, el_types, probs)
                    return self._ckd_result
                    #return types.Set(self.type_map, el_types, probs)
                except Exception as e:
                    _except_handler()
            elif value_name == "List":
                if self.elts:                                                                       
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(self.elts) \
                        for el in self.elts]
                else:   
                    probs = []
                el_types = [el.check() for el in self.elts]
                try:
                     #    setLineNo(self.lineno)
                     self._ckd_result = types.List(self.type_map, el_types, probs)
                     #return self._ckd_result
                     return types.List(self.type_map, el_types, probs)
                except Exception as e:
                    _except_handler()      
            elif value_name == 'Dict':     
                keys = []                  
                values = [] 
                idx = 0 
                for i in range(len(self.elts)): 
                    if i % 2 == 0: 
                        keys.append(self.elts[i]) 
                    else: 
                        values.append(self.elts[i]) 
                if values: 
                    probs = [el.prob if hasattr(el, 'prob') else 1 / len(values) \
                        for el in values]
                else:     
                    probs = []
                k_types = [k.check() for k in keys]
                v_types = [v.check() for v in values]
                setLineNo(self.lineno)
                self._ckd_result = types.Dict(self.type_map, k_types, v_types, probs)
                return self._ckd_result

                #return types.Dict(self.type_map, k_types, v_types, probs)
            # check the diffrent values, such as name and subscript.
            elif isinstance(self.value, Name):
                temp = self.type_map.find(self.value.id)
                temp = _get_type_from_ns(temp)
                if not isinstance(temp, data_types.Any)\
                    and isinstance(self.slice, Index):
                    index = self.slice.check()
                    index = _get_type_from_ns(index)
                    if (index is data_types.Int \
                        or isinstance(index, data_types.Int))\
                        and hasattr(temp, 'elts'):
                        self._ckd_result = temp.elts[0] if len(temp.elts) > 0 else temp.elts
                        return self._ckd_result
                from .types import Dict as DictType
                if isinstance(temp, DictType):
                   key_types = temp.key_types
                   value_types = temp.value_types
                   from .util1 import issub
                   #if not key_types \
                   #     and not value_types \
                   #     and hasattr(self, '_assign'):
                   #     value_type = self._assign
                   #     temp = DictType(None, [index], [value_type])
                   #     self.type_map.add_variable(self.value.id, temp)

                   for kt, vt in zip(key_types, value_types):
                       if not isinstance(kt, type):
                           kt = type(kt)
                       if index is kt \
                            or isinstance(index, kt) \
                            or issub(index, kt):
                            #if hasattr(self, '_assign'):
                            #    value_type = self._assign
                            #    idx = temp.key_types.index(kt)
                            #    temp.value_types[idx] = value_types
                            self._ckd_result = vt
                            return self._ckd_result

                        #return temp.elts[0] if len(temp.elts) > 0 else temp.elts
                #self._ckd_result = temp
                self._ckd_result = data_types.Any()
                return self._ckd_result
                #return temp
            elif isinstance(self.value, Subscript):
                temp = self.value.check()
                temp = _get_type_from_ns(temp)
                if not isinstance(temp, data_types.Any)\
                    and isinstance(self.slice, Index): 
                    index = self.slice.check()
                    index = _get_type_from_ns(index)
                    if isinstance(index, data_types.Int)\
                        and hasattr(temp, 'elts') \
                        and len(temp.elts) > 0: 
                        self._ckd_result = temp.elts[0]
                        return self._ckd_result
                        #return temp.elts[0] 
                #self._ckd_result = temp
                self._ckd_result = data_types.Any()
                return self._ckd_result
                #return temp 

            else:
                temp = self.type_map.find(self.value)
                temp = _get_type_from_ns(temp)
                debug("Subscript unknown type of value %r", self.value)
                #self._ckd_result = temp
                self._ckd_result = data_types.Any()
                return self._ckd_result
                #return temp
        elif isinstance(self.ctx, ast.Store):
            if isinstance(self.value, Name):
                temp = self.type_map.find(self.value.id)
                temp = _get_type_from_ns(temp)
                if not isinstance(temp, data_types.Any)\
                    and isinstance(self.slice, Index):
                    index = self.slice.check()
                    index = _get_type_from_ns(index)
                from .types import Dict as DictType
                if isinstance(temp, DictType):
                    key_types = temp.key_types
                    value_types = temp.value_types
                    from .util1 import issub
                    if not key_types \
                        and not value_types \
                        and hasattr(self, '_assign'):
                        value_type = self._assign
                        temp = DictType(None, [index], [value_type])
                        self.type_map.remove_variable(self.value.id)
                        self.type_map.add_variable(self.value.id, temp)
                    for kt, vt in zip(key_types, value_types):
                        _kt = kt
                        if not isinstance(kt, type):    
                            kt = type(kt)
                        if index is kt \
                            or isinstance(index, kt) \
                            or issub(index, kt):
                            if hasattr(self, '_assign'):
                                value_type = self._assign
                                idx = temp.key_types.index(_kt)
                                temp.value_types[idx] = value_types
                            #self._ckd_result = vt
                            #return self._ckd_result

                    self._ckd_result = temp
                    return self._ckd_result
            
            self._ckd_result = self
            return self._ckd_result
            #return self
        else:
            # TODO implement for Del, AugLoad, AugStore, Param
            raise NotYetSupported('name context', self.ctx)

    def __repr__(self: 'Subscript') -> str:
        if self.value == 'Dict':
            length = len(self.key_types)
            return self.value + '{' + ','.join(repr(self.key_types[i]) + ':' \
                        + repr(self.value_types[i]) for i in range(length)) + '}'
        elif hasattr(self, 'elts'):
            return repr(self.value) + '[' + ','.join(item.id if hasattr(item, 'id') else repr(item) for item in self.elts) + ']'
        else:
            return self.slice.__str__()

# check joined str, and return builtin type directly.
class JoinedStr(Node):
    def __init__(self: 'JoinedStr', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.values = [convert(type_map, value) \
            for value in ast_node.values]

    def check(self: 'JoinedStr') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        self.prob = 0.95
        [value.check() for value in self.values]
        self._ckd_result = data_types.Str()
        return data_types.Str()

    def __repr__(self: 'JoinedStr') -> str:
        setLineNo(self.lineno)
        return "joinedstr"

# check the str node, and return builtin type directly.
class Str(Node):
    def __init__(self: 'Str', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.s = ast_node.s

    def check(self: 'Str') -> BaseType:
        self.prob = 0.95
        setLineNo(self.lineno)
        return data_types.Str()
    def __repr__(self: 'Str') -> str:
        return "strnode"

# check the formatted value node, and we return builtin type directly.
class FormattedValue(Node):
    def __init__(self: 'FormattedValue', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'FormattedValue') -> BaseType:
        self.value.check()
        setLineNo(self.lineno)
        self.prob = 0.95
        return data_types.Str()
    def __repr__(self: 'FormattedValue') -> str:
        return "formmatted"

# check the arg node of the function node.
class arg(Node):
    def __init__(self: 'arg', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.arg = ast_node.arg

    def check(self: 'arg') -> BaseType:
        setLineNo(self.lineno)
        return self.arg
    def __repr__(self: 'arg') -> str:
        return repr(self.arg)

# check keyword node of the function node.
class keyword(Node):
    def __init__(self: 'keyword', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.arg = ast_node.arg
        self.value = convert(type_map, ast_node.value)

    def check(self: 'keyword') -> Tuple:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        arg = self.arg
        value = self.value.check()
        value = _get_type_from_ns(value)
        setLineNo(self.lineno)
        self._ckd_result = (arg, value)
        return (arg, value)

    def __repr__(self: 'keyword') -> str:
        return repr(self)

# check the await node, we return Any type directly.
class Await(Node):
    def __init__(self: 'Await', type_map: Dict, ast_node: AST) -> None:
        super().__init__(type_map, ast_node)
        self.value = convert(type_map, ast_node.value)

    def check(self: 'Await') -> BaseType:
        # For Performance, we cache the node's return result. 
        # If the checked result self._ckd_result is not None, then we return it directly.
        if self._ckd_result is not None:
            return self._ckd_result
        
        
        v_type = data_types.Any()
        setLineNo(self.lineno)
        v_type = self.value.check()
        v_type = _get_type_from_ns(v_type)
        self._ckd_result = v_type
        return v_type

    def __repr__(self: 'Await') -> str:
        return 'await'

# convert ast to our nodes, then we can add interface and fields.
def convert(type_map: Dict, node: AST) -> BaseType:
    class_name = node.__class__.__name__
    try:
        # Try to convert to a node
        class_ = globals()[class_name]
        return class_(type_map, node)
    except KeyError:
        if class_name in globals():
            class_ = globals()[class_name]
            return class_(type_map, node)
        try:
            # Try to convert to a builtin type
            class_ = getattr(data_types, class_name)
            return class_()
        except AttributeError:
            _except_handler()
            raise NotYetSupported('node', node)

# set the node's lineno, using when we report logging information
from . import config
def setLineNo(lineno: int) -> None:
    if lineno > 0:
        config.setLineNo(lineno)

# get the class abbreviated name of the node.
def getClass(target: Node) -> str:
    if isinstance(target, Name):
        return 'n'
    elif isinstance(target, Attribute):
        return 'a'
    else:
        return 'e'

# get name of the node.
def getTargetName(target: Node) -> str:
    if hasattr(target, 'id'):
        return target.id
    elif hasattr(target, 'value'):
        return target.value
    else:
        return repr(target) if isinstance(repr(target, str)) else target

# add variable into the current namespace.
def add_variable(target: Node, value: Node, type_map: Dict, *probs: Tuple) -> None:
    if hasattr(target, 'id'):
        type_map.add_variable(target.id, value.prob_type\
            if hasattr(value, 'prob_type') \
            and not isinstance(value.prob_type, data_types.Any) \
            else value, probs)
    elif hasattr(target, 'name'):
        type_map.add_variable(target.name, value.prob_type\
            if hasattr(value, 'prob_type') \
            and not isinstance(value.prob_type, data_types.Any) \
            else value, probs)
    else:
        type_map.add_variable(target, value.prob_type \
            if hasattr(value, 'prob_type') \
            and not isinstance(value.prob_type, data_types.Any) \
            else value, probs)

# attribute assign function, we need to consider the instance object.
def _attribute_assign(target: Node, value_type: BaseType) -> None:
    target_type = target.prob_type \
            if hasattr(target, 'prob_type') \
            and not isinstance(target.prob_type, data_types.Any) \
            else target.check()
    attr = target.attr
    from .types import Instance
    if isinstance(target_type, data_types.Any) \
        or not isinstance(target_type, Instance):
        target_type = target.value.check()
    try:
        if hasattr(target_type, 'set_attribute'):
            target_type.set_attribute(attr, value_type)
        elif target_type[attr] is not None:
            target_type[attr] = value_type
    except Exception:
        from . import config
        logging.warn("can't not assign %r[%r] = %r in file: %r at line: %d", target_type,\
                         attr, value_type, config.getFileName(), config.getLineNo())

from .util import data_type

# assignment function, we need to handle diffrent node of the left operand.
def _assign(target: Node, value: Node, type_map: Dict, *probs: Tuple) -> BaseType:
    
    from .builtins.functions import BuiltinFunction
    from .types import Function
    try:
        if isinstance(value, Node):
            if isinstance(value, Attribute):
                value._ckd_result = None
            value_type = value.check()
            value_type = _get_type_from_ns(value_type)
        else:
            value_type = value.return_type \
                if isinstance(value, BuiltinFunction) \
                else value.prob_type \
                  if hasattr(value, 'prob_type') \
                    and not isinstance(value.prob_type, data_types.Any) \
                    else value.check()
    except TypeError as te:
        value_type = value
    except AttributeError as ae:
        value_type = value
    except Exception as e:
        
        _except_handler()
        value_type = value
    value_type = convertType(value_type)
    if value_type is data_types.Int:
        value_type = anno_type['int']
    # handle different targets.
    if isinstance(target, Name):
        temp = False
        if target.id in type_map.current_namespace:
            if hasattr(target, '_orelse'):
                temp = True
        target_type = target.prob_type \
            if hasattr(target, 'prob_type') \
            and not isinstance(target.prob_type, data_types.Any) \
            else target.check()
        #if isinstance(target, Name) \
        #    and hasattr(target, 'prob_type') \
        #    and not isinstance(target.prob_type, data_types.Any):
        #    from .result import writeTypes
        #    writeTypes(f"assign name target:{target.prob_type}, {target.prob}")
        if value_type in data_type:
            value_type = value_type()
        if temp:
            _tartype = type_map.current_namespace[target.id]
            _tartype = _get_type_from_ns(_tartype)
        if temp and not issub(_tartype, value_type):
            from .config import getFileName, getLineNo
            from .result import writeUnionContent
            ts = [_tartype, value_type]
            value_type = types.Union(type_map, ts)
            #writeUnionContent(f"union:{getFileName()}, {getLineNo()}, {repr(value_type)}")
        if hasattr(target, 'prob') \
            and not isinstance(value_type, Node) \
            and not hasattr(value_type, 'prob') \
            and not probs:
            probs = (target.prob,)

        #if hasattr(target, '_class_'):
        #    _class_ = getattr(target, '_class_')
        #    _class_.set_attribute(target.id, value_type)
        #else:
        add_variable(target, value_type, type_map, probs)

    elif isinstance(target, Attribute):
        _attribute_assign(target, value_type)
    elif isinstance(target, Subscript):
        target._assign = value_type
        target_type = target.prob_type if hasattr(target, 'prob_type') \
            and not isinstance(target.prob_type, data_types.Any) else target.check()
    elif isinstance(target, Tuple):
        target_type = target.prob_type if hasattr(target, 'prob_type') else target.check()
        if isinstance(target_type, data_types.Any) \
            and not isinstance(target.check(), data_types.Any):
            target_type = target.check()
        if hasattr(value_type, 'elts') \
            and len(target_type.elts) == len(value_type.elts):
            for t,v  in zip(target_type.elts, value_type.elts):
                add_variable(t, v, type_map, probs)
        elif value_type is data_types.Any \
                or isinstance(value_type, data_types.Any):
            for t in target_type:
                add_variable(t, value_type, type_map, probs)
        else:
            for t in target_type:
                try:
                    for v in value_type:
                        add_variable(t, v, type_map, probs)
                except TypeError:
                    _except_handler()
                    add_variable(t, value_type, type_map, probs)
    elif isinstance(target, List):
        target_type = target.prob_type \
            if hasattr(target, 'prob_type') else target.check()
        if isinstance(target_type, data_types.Any) \
            and not isinstance(target.check(), data_types.Any):
            target_type = target.check()
        if hasattr(value_type, 'elts') \
            and len(target_type.elts) == len(value_type.elts):
            for t,v  in zip(target_type.elts, value_type.elts):
                add_variable(t, v, type_map, probs)
        elif value_type is data_types.Any \
            or isinstance(value_type, data_types.Any):
            for t in target_type:
                add_variable(t, value_type, type_map, probs)
        else:
            for t in target_type:
                try:
                    for v in value_type:
                        add_variable(t, v, type_map, probs)
                except TypeError:
                    _except_handler() 
                    add_variable(t, value_type, type_map, probs)
    else:
        raise NotYetSupported('assignment to', target)
    return value_type

# convert annotation in python source file into our types.
def convertAnnotation(annotation: Node, type_map: Dict) -> BaseType:
    if isinstance(annotation, Str):
        annotation_type = type_map.find(annotation.s)
        annotation_type = _get_type_from_ns(annotation_type)
    else:
        annotation_type = annotation.check()
        annotation_type = convertType(annotation_type)
    if hasattr(annotation, 'id') \
        and annotation.id in type_map.current_namespace:
        try:
            annotation_type = type_map.current_namespace[annotation.id]
            annotation_type = _get_type_from_ns(annotation_type)
        except KeyError:
            annotation_type = data_types.Any()
            
    elif hasattr(annotation, 'id') \
        and annotation.id in anno_type \
        and not(type(annotation_type) is Union):
        annotation_type = anno_type[annotation.id]
    annotation_type = _get_type_from_ns(annotation_type)
    return annotation_type

# prevent recursion function call.
def _recursive_funccall(func: BaseType, args: List, probs: List) -> BaseType:
    from . import recursion
    flag = recursion.getRecFunc(func.name)
    if flag == 2:
        flag = recursion.setRecFunc(func.name)
    if flag:
        recursion.setRecFunc(func.name, False)
        result = func.check_call(args, probs)
        recursion.setRecFunc(func.name)
    else:
        result = func.return_type \
            if hasattr(func, 'return_type') \
            else func.check_call(args, probs)
    return result

# get annotation type and probability.
def getAnnoInstance(anno: UnionType[List, Node]) -> Tuple:
    from .types import Class
    anno_type = _get_type_from_ns(anno)
    prob = 1.0
    if isinstance(anno, list) and len(anno) == 2:
        prob = anno[1]
    if isinstance(anno_type, Class):
        anno_type = anno_type.check_call([])
    else:
        try:
            anno_type = anno_type()
        except TypeError:
            pass
    return [anno_type, prob]

# annotation assignment checking.
def _annassign(target: Node, annotation: Node, value: Node, type_map: Dict, const: bool = False, *probs: Tuple) -> None:
    stub_flag = False
    from .config import getFileName, getLineNo
    if getFileName().endswith("pyi") \
        and isinstance(value, Ellipsis):
        stub_flag = True
    if value is not data_types.NoneType:
        value_type = value.prob_type \
            if hasattr(value, 'prob_type') \
            and not isinstance(value.prob_type, data_types.Any) \
            else value.check()
        value_type = convertType(value_type)
    else:
        value_type = value
    annotation_type = annotation.check()
    annotation_type = convertType(annotation_type)
    if isinstance(target, Name):
        target_type = target.prob_type if hasattr(target, 'prob_type') else target.check()
        if isinstance(target_type, data_types.Any) \
            and not isinstance(target.check(), data_types.Any):
            target_type = target.check()

        
        annotation_type = convertAnnotation(annotation, type_map)
        if value_type in data_type:
            value_type = value_type()
        if const:
            target_type.id = "Const " + target_type.id
        #:: here we need to build a tuple to store the probs.
        if not probs:
            probs = (1.0, )
        if stub_flag:
            # Here the annotation is may be a list[type, prob], we only need the type.    
            annotation_type = getAnnoInstance(annotation_type)
        # set class attributes that values may be None.
        #else:
        type_map.add_annvariable(target.id, annotation_type, value_type, *probs)
    elif isinstance(target, Attribute):
        from .error_condition import _attr_anno_mismatch_checking
        from . import config, error_cache

        target_type = target.prob_type \
            if hasattr(target, 'prob_type') \
            and not isinstance(target.prob_type, data_types.Any) \
            else target.check()
        annotation_type = convertAnnotation(annotation, type_map) 
        if value_type in data_type:
            value_type = value_type()
        if _attr_anno_mismatch_checking(config, error_cache, str(target), annotation_type, value_type):
            if not probs:
                prob = 1.0
            else:
                prob = probs[0] if len(probs) == 1 else probs[1]
            logging.error("[ValueAnnotationMismatch] annotation:%r NE value_type: %r in file:[[%r:%d]] <<%f>>, target:%d, str(target): %r", annotation, value_type, config.getFileName(), config.getLineNo(), 1 - prob, target.lineno, target)
        _attribute_assign(target, value_type)
    else:
        raise NotYetSupported('assignment to', target)
    return value_type \
             if not isinstance(value_type, data_types.NoneType) \
             and value_type is not data_types.NoneType \
             and value_type else annotation_type

# print the logging information according to the logger level.
def _except_handler()-> None:
    if getDebug():
        import traceback
        traceback.print_exc()

# type definition checking.
def _typeassign(target: Node, value: Node, type_map: Dict, *probs: Tuple) -> BaseType:
    value_type = value.prob_type if hasattr(value, 'prob_type') else value.check()
    if isinstance(target, Name):
        target_type = target.prob_type if hasattr(target, 'prob_type') else target.check()
        if value_type in anno_type:
            value_type = anno_type[value]
        type_map.add_variable(target_type.id, value_type, probs)
    elif isinstance(target, Attribute):
        target_type, attr = target.prob_type if hasattr(target, 'prob_type') else target.check()
        target_type.set_attribute(attr, value_type)
    else:
        raise NotYetSupported('assignment to', target)
    return value_type

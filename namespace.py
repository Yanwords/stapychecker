"""
This module handles namespaces. The TypeMap keeps track of the current
namespace during each step of the type checking process as it browses through
the code.
"""

from collections import UserDict
import logging
from typing import Dict, List, Tuple, Set, Union as UnionType, Any as AnyType

from .exceptions import NoSuchName
debug = logging.debug
warn = logging.warn
from .util1 import issub, _get_type_from_ns, _same_type
from . import config

# Symbol table for the module.
class Namespace(UserDict):
    """A namespace is a mapping of names to types"""

    def __init__(self: 'Namespace', name: str, parent: 'Namespace') -> None:
        super().__init__()
        self.name = name
        self.parent = parent

    def __repr__(self: 'Namespace') -> str:
        '''
        Don't print global namespace
        :return 'global namespace' instead.
        '''
        #return '{}({!r},{!r})'.format(self.name, self.data, self.parent)
        return 'global namespace' if self.name is 'global' or self.parent == None else\
                '{}({!r},{!r})'.format(self.name, self.data, self.parent)
    
    # return the string fromat of the namespace.
    def fqn(self: 'Namespace') -> str:
        if self.parent is None or self.parent.fqn() == 'global':
            return self.name
        else:
            return self.parent.fqn() + '.' + self.name

    # iterate the namespace.
    def iter_super_namespaces(self: 'Namespace') -> 'Namespace':
        namespace = self
        while namespace is not None:
            yield namespace
            namespace = namespace.parent
# When we check one object is an instance or type,
# we can use isinstance(obj, type). False if obj is an instance,
# True if obj is a type object.

def is_type_of(target: AnyType, value: AnyType) -> bool:
    target = _get_type_from_ns(target)
    if hasattr(target, 'istypeof'):
        try:
            # For type object, we just return directly.
            if isinstance(target, type):
                return target is value 
            return target.istypeof(value)
        except TypeError:
            if issub(target, value):
                return True
            if isinstance(target, type):
                return False
            tmp = target()
            tmp.istypeof(value)
    else:
        try:
            return isinstance(target, value)
        except TypeError:
            flag = isinstance(target, value.__class__)
            if flag:
                if hasattr(target, 'elts') and hasattr(value, 'elts'):
                    if len(target.elts) == len(value.elts) and target.elts == value.elts:
                        return True
                    return False
                return flag
            return isinstance(target, value.__class__)

# return the probability of the identifier in the namespace.
def _getprob(probs: Tuple) -> float:
    if isinstance(probs, tuple):
        if probs:
            return _getprob(probs[0])
        else:
            return 0
    else:
        return probs

# return the value is null. For compoud types, if the elsts are [], we regard it as null.
def _is_null_value(value):
    from .types import Dict as DictType, Tuple as TupleType, List as ListType, Set as SetType, Union as UnionType
    if isinstance(value, DictType) \
        and value.key_types == [] \
        and value.value_types == []:
        return True
    elif isinstance(value, (TupleType, ListType, SetType, UnionType)) \
        and value.elts is []:
        return True

    return False

def _recursive_find(names, mod):
    idx = 0
    while idx < len(names):
        _name = names[idx]
        try:
            if hasattr(mod, '__iter__') \
                and _name in mod:
                mod = mod[_name]
                idx += 1
            else:
                break
        except Exception:
            break

    if idx == len(names):
        return mod

    return False

# symtable for our type checker.
class TypeMap:
    def __init__(self: 'TypeMap', global_namespace: Namespace) -> None:
        self.stack = []
        self.current_namespace = global_namespace

    # find name's type in the symbol table.
    def find(self: 'TypeMap', name: str) -> AnyType:
        from .builtins.data_types import Any
        if not isinstance(name, str):
            name = repr(name)
        if "." in name:
            names = name.split(".")
            mod = self.current_namespace
            result = _recursive_find(names, mod)
            if result is not False:
                return result

        for super_namespace in self.current_namespace.iter_super_namespaces():
            if name in super_namespace:
                logging.info("%s found in %s namespace", name, super_namespace.name)
                return super_namespace[name]
        
        # Ignore the name error reporting.
        ## Check the module exists in the cache.   
        #if config.getFileName() in imports_flags:
        #    pkg_name = config.getFileName()
        #else:
        #    pkg_name = config.getFileName()
        #    pkg_name = pkg_name.replace(".pyi", "")
        #    pkg_name = pkg_name.replace(".py", "")
        #    pkg_name = pkg_name.replace("/__init__", "")
        #    pkg_name = pkg_name.split(os.path.sep)[-1]
        
        #if pkg_name not in imports_cache \
        #    and pkg_name in imports_flags \
        #    and not imports_flags[pkg_name]:
        #    warn("[NameERROR] Current ns has no name:%r in file: %r at line: %d", name, \
        #        config.getFileName(), config.getLineNo())
        
        # If the var_name cann't find in the symtable, return Any instead.
        return Any()

    def build_context_for(self: 'TypeMap', name: str) -> Namespace:
        return Namespace(name + '.<locals>', self.current_namespace)
    # enter a new namespace such as function scope and class scope.
    def enter_namespace(self: 'TypeMap', name: str) -> Namespace:
        self.current_namespace = Namespace(name, self.current_namespace)
        return self.current_namespace

    def exit_namespace(self: 'TypeMap') -> None:
        self.current_namespace = self.current_namespace.parent
    # enter the function scope with additional outer namespace.
    def enter_function_scope(self: 'TypeMap', context: Namespace, initial_mapping: Dict = None) -> None:
        self.stack.append(self.current_namespace)

        function_namespace = context.copy()
        if initial_mapping is not None:
            function_namespace.update(initial_mapping)
        self.current_namespace = function_namespace

    def exit_function_scope(self: 'TypeMap'):
        self.current_namespace = self.stack.pop()

    # add variable to current namespace including types and optional probability.
    def add_variable(self: 'TypeMap', name: str, object_: AnyType, *probs: List) -> None:
        from .builtins.data_types import UnDefined, Any
        _type = Any()
        # Judge name exists in the namespace instead of current namespace. Or there may be exists many identifiers.
        if name in self.current_namespace:
           _type = self.current_namespace[name]
           _type = _get_type_from_ns(_type)
        if not isinstance(_type, (UnDefined, Any)) \
            and _type is not None:
            _obj = _get_type_from_ns(object_)
            if isinstance(_obj, (UnDefined, Any)):
                return _type
            if not is_type_of(_type, object_):
                id_type = _get_type_repr(_type)
                obj_type = _get_type_repr(object_)
                logging.error("[OverRideTypeError] override identifier:%r:type:%r with type:%r in file: %r at line line: %d", name, id_type, obj_type, config.getFileName(), config.getLineNo())
            else:
                return _type
        if probs:
            object_ = [object_, _getprob(*probs)]
        self.current_namespace[name] = object_

    # UNDEFINED type is for pre-add identifiers while handling import statements.
    def add_undefined(self: 'TypeMap', name: str, object_: AnyType) -> None:
        self.current_namespace[name] = object_
    
    # remove variable in the namespace, maybe the variable in global namespace.
    def remove_variable(self: 'TypeMap', name: str) -> AnyType:
        for super_namespace in self.current_namespace.iter_super_namespaces():
            if name in super_namespace:
                ty = 'name:' + repr(super_namespace[name])
                super_namespace.pop(name)
                return ty
        logging.warning("current namespace:%r has no identifier:%r, can't remove:%r", self.current_namespace, name, name)

    # add variable and annotaion to the namespace.
    def add_annvariable(self: 'TypeMap', name: str, annotation: AnyType, object_: AnyType, *probs: List) -> None:
        from .builtins.data_types import Any, NoneType, UnDefined
        _type = Any()
        if name in self.current_namespace:
           _type = self.current_namespace[name]
           _type = _get_type_from_ns(_type)
        
        from . import error_cache, config
        from .error_condition import _anno_mismatch_checking
        if not isinstance(_type, (UnDefined, Any)):# and (self.current_namespace[name].istypesof(object_)):
            if not is_type_of(_type, object_):
                logging.error("[TypeError] override type:%r instead of %r in file: %r at line: %d", object_, self.current_namespace[name], config.getFileName(), config.getLineNo())
        elif annotation is not type(object_) \
            and not issub(annotation, object_) \
            and not _same_type(annotation, object_) \
            and _anno_mismatch_checking(config, error_cache, name):
            from .config import getCurNode 
            node = getCurNode() 
            prob = node.prob if hasattr(node, 'prob') else 0.5 
            if probs:
                if len(probs) == 1:
                    prob = probs[0]
                else:
                    prob = probs[1]
            logging.error("[ValueAnnotationMismatch] Annotation:%r NE value_type:%r in file: [[%r:%d]] <<%f>>",
                 annotation, object_, config.getFileName(), config.getLineNo(), 1 - prob)
        #elif ".pyi" in config.getFileName() and object_ is NoneType:
        #    pass
        # Here we need to handle it carefully. !!!! BUG exists.
        elif annotation is not type(object_) \
            and not issub(annotation, object_) \
            and not _same_type(annotation, object_) \
            and object_ is not NoneType \
            and type(annotation) is not type(object_) \
            and _anno_mismatch_checking(config, error_cache, name):
            from .config import getCurNode
            node = getCurNode()
            prob = node.prob if hasattr(node, 'prob') else 0.5
            if probs:
                prob = probs[0] if len(probs) == 1 else probs[1]
            logging.error("[ValueAnnotationMismatch] 2_annotation:%r NE value_type:%r in file: [[%r:%d]] <<%f>>",
                     annotation, object_, config.getFileName(), config.getLineNo(), 1 - prob)
        if isinstance(object_, (Any, NoneType, UnDefined)) \
            or object_ in (None, NoneType, Any, UnDefined) \
            or not isinstance(annotation, Any) \
            and _is_null_value(object_):
            self.current_namespace[name] = annotation
        else:
            self.current_namespace[name] = object_
    
    def add_import(self: 'TypeMap', name: str, import_map: Dict) -> None:
        import_namespace = Namespace(name, None)
        temp = 'module ' + name
        if temp in self.current_namespace:
            return
        else:
            self.current_namespace[temp] = import_map.data

    def add_module(self: 'TypeMap', mod_name: str, ns: Dict) -> Dict:
        data = {}
        if ns is None:
            return None
        from .builtins.data_types import Any
        if isinstance(ns, Any):
            return {}
        for key in ns.keys():
            data[key] = ns[key]
        self.current_namespace[mod_name] = data
    
    # check if the identifier exists in the namespace.
    def in_global(self: 'TypeMap', name: str, value: AnyType) -> bool:
        for ns in self.current_namespace.iter_super_namespaces():
            if ns.name == 'global' and name in ns \
                    and ns[name] == value:
                return True
        return False
    
    # check the identifier exists in the namespace and return the type of the namespace.
    def in_typemap(self: 'TypeMap', name: str) -> Tuple:
        for super_namespace in self.current_namespace.iter_super_namespaces():
            if name in super_namespace:
                return True, super_namespace[name] 
        return False, None

# return a simple representation of the complex types.
def _get_type_repr(_type: AnyType) -> str:
    if isinstance(_type, dict):
        return "dict_type"
    elif isinstance(_type, list):
        return "list_type"
    
    return _type

#def _same_type(obj1, obj2):
#    if not isinstance(obj1, type):
#        obj1 = type(obj1)
#    if not isinstance(obj2, type):
#        obj2 = type(obj2)
#    return obj1 is obj2

# return a namespace which super namespace is our gloabl namespace.
def build_type_map() -> TypeMap:
    global_namespace = Namespace('global', None)
    return TypeMap(global_namespace)


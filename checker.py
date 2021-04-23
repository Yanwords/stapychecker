import traceback
import logging
import sys
import os
from typing import Dict, List, Any as AnyType

from . import result
from . import insuline, namespace, builtins, nodes

from .coordinator.ExtractStaticTypes import staDict, probDict
from .coordinator.extractOneFileTypes import getOriginTypes
from .coordinator.fixnode import fixASTNode
from .coordinator.typemap import setTypeMap
from .imports_helper import imports_flags, imports_cache

import ast
AST = ast.AST

debug = logging.debug

# return module symbol table.
def getModuleType(ns: Dict) -> Dict:
    data = {}
    if ns is None:
        return None
    from .builtins.data_types import Any
    if isinstance(ns, Any):
        return data
    for key in ns.keys():
        data[key] = ns[key]
    return data

# add inferenced types and probabilities to ast nodes.
def fixNodeType(file_: str, asttree: AnyType) -> AST:
    if file_:
        absfile = os.path.abspath(file_)
        staTypes = getOriginTypes(os.path.sep.join(file_.split(os.path.sep)[2:]) + ".txt")
        asttree = fixASTNode(asttree, staTypes, absfile, isSingle=True)
        asttree = fixASTNode(asttree, staDict, absfile)
        asttree = fixASTNode(asttree, probDict, absfile, isProb=False)   
    
    return asttree

# type checking one module, and add the module type into the caches.
def check(module: AnyType, type_map: Dict, file_: str = '') -> Dict:
    from . import recursion
    recursion.clear()
    import ast
    
    if type_map is None:
        type_map = namespace.build_type_map()
        builtins.add_to_type_map(type_map)
    insuline.replace_syntactic_sugar(module)
    module = nodes.convert(type_map, module)
    mod = {}
    setTypeMap(type_map)
    module = fixNodeType(file_, module)
    from .modulevisitor import ModuleVisitor
    visitor = ModuleVisitor()
    visitor.visit(module)
    try:
        mod = module.check()
    except Exception as err:
        import traceback
        traceback.print_exc()
    from . import config
    import os
    root_dir = config.getRootDir()
    file = config.getFileName()
    imports_flags[file] = True
    file = os.path.abspath(file)
    if file.startswith(config.getRootDir()):
        filename = file.replace(root_dir, \
                                root_dir.split(os.path.sep)[-2] + os.path.sep)
    else:
        filename = file.split(os.path.sep)[-1]
    if '/__init__.' in file:
        from . import pkginfo
        filename = file.split(os.path.sep)[-2]

    filename = file.replace(".pyi", "")
    filename = filename.replace(".py", "")
    filename = filename.replace("/__init__", "")
    
    if filename not in imports_cache:
        imports_cache[filename] = getModuleType(mod)
        return imports_cache[filename]
    return getModuleType(mod)

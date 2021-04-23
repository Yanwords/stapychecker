# imports handler for the checker, and handle the import recursion.

import ast
import sys
import os
from typing import Union, Any as AnyType, Dict, List

from .checker import check
from .exceptions import NotYetSupported
from .builtins.data_types import Any

from .imports_helper import BUILTIN_IMPORTS, BUILTIN_FLAGS, imports_cache, imports_flags

# Get the file type and absolute path. Support py/pyi/package.
def getfiledefinitions(directory: str) -> Union[str, bool]:
    if os.path.isfile(directory + '.pyi'):
        return directory + '.pyi'
    elif os.path.isfile(directory + '.py'):
        return directory + '.py'
    elif os.path.isdir(directory) \
         and os.path.isfile(os.path.sep.join([directory, '__init__.py'])):
        return os.path.sep.join([directory, "__init__.py"])
    elif os.path.isdir(directory) \
         and os.path.isfile(os.path.sep.join([directory, '__init__.pyi'])):
        return os.path.sep.join([directory, '__init__.pyi'])
    else:
        # Not python file or pakcage. Skip.
        return False

# get module symbol table of the file.
def getMTypeFromFile(file: AnyType, type_map: Dict) -> Dict:
    asttree = ast.parse(file.read())
    m_type = check(asttree, type_map)
    return m_type

# check the import statements of the filename.
def checkimport(filename: str, syspath: List) -> AnyType:
    tmp = list(set(syspath))
    tmp.sort(key=syspath.index)
    syspath = tmp
    check_stub = True
    # Some builtin modules such as sys, typing, are imported from typeshed and cached.
    if filename in BUILTIN_IMPORTS:
        check_stub = BUILTIN_FLAGS[filename]
    if filename is None:
        return Any()
    if check_stub \
        and filename in imports_cache:
        return imports_cache[filename]
    else:
        flag = True
        if filename in BUILTIN_IMPORTS \
            and not BUILTIN_FLAGS[filename]:
            flag = False

        from .comp_types_attrs import module_attributes
        if flag \
            and filename in sys.builtin_module_names \
            or filename.startswith('_frozen') \
            or filename in BUILTIN_IMPORTS:

            from . import builtinpkgs
            tmp_syspath = sys.path
            sys.path = builtinpkgs.getBuiltinPkg() \
                    if filename in BUILTIN_IMPORTS \
                    and not BUILTIN_FLAGS[filename] \
                    else sys.path
            try:
                # For _frozenModuleName, we just need to get all the symbols defined in the module. If they were annoted in the typeshed, we import stub file.
                mod = __import__(filename)
                module_type = {var: Any() for var in dir(mod)}
            except ModuleNotFoundError:
                module_type = {}
                imports_flags[filename] = 'not found'
            except ImportError:
                flag = False
            finally:
                sys.path = tmp_syspath
            module_type.update(module_attributes)
            if flag:
                imports_cache[filename] = module_type
                return module_type

        from . import config
        from . import result
        for path in syspath:
            full_path = os.path.sep.join([path, filename]) \
                if len(filename.split(os.path.sep)) == 1\
                else filename
            file = getfiledefinitions(full_path)
            if file:
                # Remove the suffix in the filename.
                filename = filename.replace(".pyi", "")
                filename = filename.replace(".py", "")
                filename = filename.replace("/__init__", "")
                if filename in imports_cache:
                    return imports_cache[filename]
                else:
                    imports_cache[filename] = {}
                tmpFileName = config.getFileName()
                tmpLineNo = config.getLineNo()
                config.setFileName(file)
                imports_flags[file] = False
                from . import recursion
                tmp_rec = recursion.get()
                try:
                 with open(file, 'r') as f:
                     module_type = getMTypeFromFile(f, None)
                     module_type.update(module_attributes)
                     result.writeFileName(file)
                     result.writeFileName("Checked!")
                     config.setFileName(tmpFileName)
                     config.setLineNo(tmpLineNo)
                     imports_flags[file] = True
                     imports_cache[filename] = module_type
                     if filename in BUILTIN_IMPORTS:
                         BUILTIN_FLAGS[filename] = True
                     recursion.set(tmp_rec)
                     return module_type
                except Exception:
                 pass
                finally:
                 config.setFileName(tmpFileName)
                 config.setLineNo(tmpLineNo)
        return Any()

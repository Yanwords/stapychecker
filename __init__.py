#!/usr/bin python3
"""A static type checker for Python3. This is the entry of our checker."""

import argparse
import logging
import os
import sys
from typing import List

from . import checker
from .exceptions import CheckError, NotYetSupported
from . import config
from . import result
from . import logfile
from . import pkginfo
from . import result
from .coordinator.getAst import getASTS

# checker entry function that handles the options.
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('file')
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()
    log_level = logging.DEBUG \
            if args.verbose \
            else logging.WARNING

    try:
        from . import builtinpkgs
        builtinpkgs.setBuiltinPkg(sys.path[1:])
        sys.setrecursionlimit(10000)
        path = default_lib_path()
        sys.path[1:1] = path
        config.setDebug(args.debug)
        from . import sitepkgs
        sitepackages = sitepkgs.getsitepackages()
        for path in sitepackages:
            if not path in sys.path:
                sys.path.append(path)
        config.setRootDir(os.path.abspath(args.file) + os.path.sep)

        if os.path.isdir(args.file):
            dir_check(args.file)

        elif os.path.isfile(args.file):
            file_check(args.file)
        else:
            logging.error("Error! What we check is not project nor file. Please input again!")

        from .imports_handler import imports_cache, BUILTIN_FLAGS
        typeshed_pkd = {}
    except CheckError as error:
        import traceback
        traceback.print_exc()
    except NotYetSupported as error:
        import traceback
        traceback.print_exc()
    except Exception as e:
        import traceback 
        traceback.print_exc()
    finally:
        result.closeFile()

# check a python project.
def dir_check(path: str) -> None:
    logFName = path.split(os.path.sep)
    pkginfo.setPkg(logFName[-2] \
            if logFName[-1] else logFName[-3])
    result.setPkg(logFName[-2] 
            if logFName[-1] else logFName[-3])
    pkginfo.setSubPkg(os.path.sep.join(logFName[-2:] \
            if logFName[-1] else logFName[-3:-1]))
    logFName.reverse()
    for lfname in logFName:
        if lfname:
            logfile.setFileName(lfname, False)
            break
    sys.path.append(os.path.abspath(path))
    sys.path.insert(1, '')
    asts = getASTS(path)
    from .coordinator.ExtractStaticTypes import getAllTypes
    getAllTypes()
    from .imports_helper import imports_flags
    for dir, folder, files in  os.walk(path):
        for fname in files:
            if fname.endswith(".py") or fname.endswith(".pyi"):
                # We use absolute path to avoid log same error messages.
                file = os.path.join(os.path.abspath(dir), fname)
            else:
                continue
            config.setFileName(file)
            imports_flags[file] = False
            sys.path.pop(1)
            sys.path.insert(1, os.path.sep.join(os.path.abspath(file).split(os.path.sep)[:-1]))
            checker.check(asts[file], None, file)
            result.writeFileName(file)
            result.writeFileName('Checked!')

# check a single file.
def file_check(path: str) -> None:
    fname = path.split(os.path.sep)[-1]
    config.setFileName(path)
    m_name = fname
    if not fname.endswith(".py") \
        and not fname.endswith(".pyi"):
        raise exceptions.NotPythonFile(fname)
    if fname.endswith(".pyi"):
        logfile.setFileName(fname.replace(".pyi", ""))
        m_name = fname.replace(".pyi", "")
    elif fname.endswith(".py"):
        logfile.setFileName(fname.replace(".py", ""))
        m_name = fname.replace(".py", "")
    asts = getASTS(path)
    result.setPkg(m_name)
    from .imports_helper import imports_flags
    imports_flags[path] = False
    sys.path.insert(1, os.path.sep.join(os.path.abspath(path).split(os.path.sep)[:-1]))
    checker.check(asts[path], None, path)
    result.writeFileName(fname)
    result.writeFileName("Checked!")

# add python's library path into sys.path. so we can search for some standard modules.
def default_lib_path() -> List:
    """Return default standard library search paths."""
    path = []  # type: List[str]
    TSPKG = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-2]) 
    typeshed_dir = os.path.sep.join([TSPKG, "typeshed_3"])
    #typeshed_dir = './typeshed_3'
    from . import version
    if version.PY_VERSION == 3:
        # We allow a module for e.g. version 3.5 to be in 3.4/. The assumption
        # is that a module added with 3.4 will still be present in Python 3.5.
        versions = ["%d.%d" % (version.PY_VERSION, minor)\
                for minor in reversed(range(4, version.PY3_VERSION + 1))]
    else:
        # For Python 2, we only have stubs for 2.7
        versions = ["2.7"]
    # E.g. for Python 3.6, try 3.6/, 3.5/, 3.4/, 3/, 2and3/.
    for v in versions + [str(version.PY_VERSION), '2and3']:
        for lib_type in ['stdlib', 'third_party']:
            stubdir = os.path.join(typeshed_dir, lib_type, v)
            if os.path.isdir(stubdir):
                path.append(stubdir)
    # Add fallback path that can be used if we have a broken installation.
    if not path:
        logging.warning("can't find typeshed module")
        sys.exit(1)
    return path

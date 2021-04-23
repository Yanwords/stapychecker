#!/usr/bin/python371

"""A static type checker for Python3"""

import argparse
import ast
import logging
import os
import sys
from typing import List, Tuple, Dict, Optional, Any as AnyType

from .dump_python import parse_dump, parse_string

AST = ast.AST
asts:Dict[str, AST] = {}
# get the project asts and fix the node location such lineno.
def getASTS(dir_path: str) -> Optional[Dict[str, AST]]:
    global asts
    try:
        sys.setrecursionlimit(10000)

        if os.path.isdir(dir_path):
            for dirs, folder, files in  os.walk(dir_path):
                for fname in files:
                    if fname.endswith(".py") \
                        or fname.endswith(".pyi"):
                        # We use the absolute path instead of relative path. Thus we can avoid log same error messages.
                        file = os.path.join(os.path.abspath(dirs), fname)
                    else:
                        continue
                    with open(file, 'r', encoding='utf-8') as pyfile:
                        asttree = parse_string(pyfile.read())
                        asts[file] = asttree

        elif os.path.isfile(dir_path):
            fname = dir_path.split(os.path.sep)[-1]
            if not fname.endswith(".py") \
                and not fname.endswith(".pyi"):
                raise exceptions.NotPythonFile(fname)
            with open(dir_path, 'r', encoding='utf-8') as file:
                asttree = parse_string(file.read())
                asts[dir_path] = asttree
        else:
            print("Error! What we check is not project nor file. Please input again!")
        return asts

    except Exception as e:
        import traceback
        traceback.print_exc()
        from .type_result import closeFile
        closeFile()

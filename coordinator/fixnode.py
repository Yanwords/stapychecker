#!/usr/bin/python371

"""A static type checker for Python3"""

import sys
from typing import Any as AnyType, Dict

from .genVisitor import CodeVisitor, setTypes
import ast

AST = ast.AST

# collect inferred types and add them to the asttree.
def fixASTNode(asttree: AnyType, typeDict: Dict, absfile: str, isProb: bool = True, isSingle: bool=False) -> AST:
    types = []
    if isinstance(typeDict, dict):
        for path in typeDict.keys():
            if path in absfile:
                types = typeDict[path]
                break
    else:
        types = typeDict  
    setTypes(types.copy(), isProb, isSingle)
    visitor = CodeVisitor()
    visitor.visit(asttree)
    return asttree

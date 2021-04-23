# from __future__ import print_function
"""This file is used to find the site packages of a Python executable, which may be Python 2.

This file MUST remain compatible with Python 2. Since we cannot make any assumptions about the
Python being executed, this module should not use *any* dependencies outside of the standard
library found in Python 2. This file is run each mypy run, so it should be kept as fast as
possible.
"""
BUILT_IN_PKG = []
# set builtin pkg path.
def setBuiltinPkg(path: str) -> None:
    global BUILT_IN_PKG
    BUILT_IN_PKG = path
# get builtin pkg path.
def getBuiltinPkg() -> str:
    return BUILT_IN_PKG


# module that save version information of the python interpreter.
import sys

PY_VERSION: int = sys.version_info.major
PY3_VERSION: int = sys.version_info.minor
CHECHER_VERSION: str = '0.1.0'

def strict_annotations() -> bool:
    return False

def optimized() -> bool:
    return True

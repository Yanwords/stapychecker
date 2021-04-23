# Config information of the checker.
import sys

PY_VERSION: int = sys.version_info.major
PY3_VERSION: int = sys.version_info.minor
RETIC_VERSION: str = '0.1.0'

def strict_annotations() -> bool:
    return False

def optimized() -> bool:
    return True

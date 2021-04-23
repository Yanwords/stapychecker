# from __future__ import print_function
"""This file is used to find the site packages of a Python executable, which may be Python 2.

This file MUST remain compatible with Python 2. Since we cannot make any assumptions about the
Python being executed, this module should not use *any* dependencies outside of the standard
library found in Python 2. This file is run each mypy run, so it should be kept as fast as
possible.
"""

from typing import List
from distutils.sysconfig import get_python_lib
import site

# retun the sitepackages of the current python intepreter.
def getsitepackages() -> List[str]:
    # type: () -> List[str]
    if hasattr(site, 'getusersitepackages') and hasattr(site, 'getsitepackages'):
        user_dir = site.getusersitepackages()
        return site.getsitepackages() + [user_dir]
    else:
        return [get_python_lib()]


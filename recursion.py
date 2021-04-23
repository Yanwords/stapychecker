# This module is for handling recursion call checking, 
# such as functions call , methods call.
from typing import Dict, List, Any as AnyType, Union

from .types import BaseType

recursive_function: Dict = {}

# return current function.
def getRecFunc() -> BaseType:
    return recursive_function

# set function that may be in recursion.
def setRecFunc(func_name: str, flag: bool = True) -> bool:
    '''
    if func_name in recursive_function.keys():
        return recursive_function[func_name]
    else:
        recursive_function[func_name] = True
    '''
    if not func_name in recursive_function.keys():
        recursive_function[func_name] = flag
    # temp = recursive_function[func_name]
    recursive_function[func_name] = flag
    return flag

# return function according to the function name.
def getRecFunc(func_name: str) -> Union[int, BaseType]:
    if not func_name in recursive_function.keys():
        return 2
    else:
        return recursive_function[func_name]

# initial the recursive function map.
def clear() -> None:
    global recursive_function
    recursive_function = {}

# getter and setter of the recursive function map.
def get() -> BaseType:
    return recursive_function

def set(rec_results: Dict) -> None:
    global recursive_function
    recursive_function = rec_results

# prevent recursion function call. 
def _recursive_funccall(func: BaseType, args: List, probs: List) -> BaseType: 
    flag = getRecFunc(func.name) 
    if flag == 2: 
        flag = setRecFunc(func.name) 
    if flag: 
        setRecFunc(func.name, False) 
        result = func.check_call(args, probs) 
        setRecFunc(func.name) 
    else: 
        result = func.return_type \
                if hasattr(func, 'return_type') \
                else func.check_call(args, probs)
    return result

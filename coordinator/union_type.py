# Union type for converting probabilistic types that our checker can handle them.
from typing import Dict, List, Any as AnyType

class UnionType: 
    # if we use *type_elements, we may get a tuple not a list. 
    # For example, Union([int, str]), elts = ([int, str],). So we need to use type_element instead *type_element. 
                                                                                                    
    def __init__(self: 'UnionType', type_map: Dict, type_elements: List, probs: List = []) -> None: 
        self.elts = type_elements 
        self.probs = probs 
    
    def __repr__(self: 'UnionType') -> str: 
        if self.probs: 
            return "Union" + '[' + ', '.join(repr(el) + ":" + str(prob) if not isinstance(el, dict) else "Dict" for el,prob in zip(self.elts, self.probs)) + ']' 
        else: 
            return "Union" + "[" + ", ".join(repr(el) if not isinstance(el, dict) else 'Dict' for el in self.elts) + "]" 
    def __str__(self: 'UnionType') -> str: 
        return self.__repr__() 
 
    def __iter__(self: 'UnionType') -> AnyType: 
        for elt in self.elts: 
            yield elt 

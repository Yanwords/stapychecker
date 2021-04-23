# There are many error checking function in this module.
# They are all for checking the condition.
# We will ignore some files and filter some unneccessary checking.
from .types import Module, BaseType

# Ignore libraries checking for some kinds of errors.
def _filename_checking(filename: str) -> bool:
    if "site-packages" not in filename \
        and "lib/python" not in filename \
        and ".pyi" not in filename:               
        return True 
    return False 

# AttributeError checking. Ignore libraries.
# config and error_cache are modules in PyProb.
def _attr_error_checking(config: Module, error_cache: Module, name: str) -> bool:
    # For performance, we don't check libraries and stub files.
    filename = config.getFileName()
    
    # Skip the is and isnot operators checking.
    if name == "__is__" or name == "__isnot__":
        return False
    
    if not config.getAttrError() \
        and _filename_checking(filename) \
        and error_cache.addError("[AttributeError]", filename, config.getLineNo(), name):
        return True
    return False

# Class Attribute Refernce error checking.
def _class_attr_error_checking(config: Module, error_cache: Module, name: str, single_field: bool) -> bool:
    filename = config.getFileName()

    if _filename_checking(filename) \
        and (not name.startswith("__") or not name.endswith("__")) \
        and (not name == "__new__" or not name == "__init__") \
        and single_field \
        and error_cache.addError("[CAttributeError]", filename, config.getLineNo(), name):
        return True
    return False


# Return Value checking
def _return_value_checking(config: Module, error_cache: Module, name: str, lineno: int) -> bool:
    #For performance, we ignore the third-party libraries, builtin libraries and stub files checking.
    # There is no body in stub files.
    filename = config.getFileName()
    
    if _filename_checking(filename) \
        and error_cache.addError("[ReturnValueMissing]", filename, lineno, name):
        return True
    return False

# Check object is a class type. 
def _is_class(_cls: BaseType) -> bool:

    #from .types import BaseType, Class 
    from .types import Class
    from .builtins.data_types import Any, UnDefined 
    from .builtins.functions import BuiltinFunction as Fun 
    # for dynamic type and Function(TypeError and so) 
    if isinstance(_cls, (Any, UnDefined, Fun)): 
        # or _cls is Any:                                
        # or _cls is (list, tuple, dict, set): 
        return True 
    try: 
        return issubclass(_cls, BaseType) 
    except TypeError:
        if isinstance(_cls, Class):                      
            return True 
    return False 

# Return the class type of object.
def get_class(_cls: BaseType) -> bool:
    #from .types import BaseType
    
    try:
        issubclass(_cls, BaseType)
        return _cls
    except TypeError:
        return type(_cls)

# subclass checking for two classes objects. 
def _is_subclass(cls1: BaseType, cls2: BaseType) -> bool: 
    #from .types import BaseType, Instance 
    from .types import Instance
    from .util1 import issub 
    
    if isinstance(cls1, Instance) \
        or isinstance(cls2, Instance):
        return False
    if _is_class(cls1) \
        and _is_class(cls2): 
        _type1 = get_class(cls1) 
        _type2 = get_class(cls2) 
        return issub(_type1, _type2) 
    return False   

# Condition for subtype error checking.
def _subtype_checking(_cls: BaseType, config: Module, error_cache: Module) -> bool: 
    # subtype error duplicate in log file. For performance, we ignore the third-party libraries, builtin libraries and stub files checking.
    filename = config.getFileName()

    if not _is_class(_cls) \
        and _filename_checking(filename) \
        and error_cache.addError("[SubTypeError]", config.getFileName(), config.getLineNo(), str(_cls)): 
        return True 
    return False 

# Condition for TypeError checking.
def _type_error_checking(config: Module, error_cache: Module, name: str) -> bool: 
    filename = config.getFileName()

    if _filename_checking(filename) \
        and error_cache.addError("[TypeError]", config.getFileName(), config.getLineNo(), name):
        return True
    return False

def _anno_mismatch_checking(config: Module, error_cache: Module, name: str) -> bool:
    filename = config.getFileName()
    if _filename_checking(filename) \
        and error_cache.addError("[ValueAnnoMismatch]", filename, config.getLineNo(), name):
        return True
    return False

def _attr_anno_mismatch_checking(config: Module, error_cache: Module, name: str, annotation: BaseType, value_type: BaseType) -> bool:
    from .util1 import issub, _same_type
    
    if _anno_mismatch_checking(config, error_cache, name)\
        and annotation is not type(value_type)\
        and not issub(annotation, value_type) \
        and not _same_type(annotation, value_type):
        return True
    return False

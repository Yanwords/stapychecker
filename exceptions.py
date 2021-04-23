# self-defined exception classes.
import sys
from typing import Any as AnyType, Dict, List
import ast

AST = ast.AST

class NotYetSupported(Exception):
    def __init__(self: 'NotYetSupported', kind: AnyType, thing: AnyType = None) -> None:
        self.msg = 'Support for {}'.format(kind)
        if thing is not None:
            self.msg += ' "{}"'.format(type(thing).__name__)
        self.msg += ' is not yet implemented'

# Base class of the checking error class.
class CheckError(Exception):
    pass


class NoSuchName(CheckError):
    def __init__(self: 'NoSuchName', name: str, namespace: Dict) -> None:
        template = '{} not found in namespace {}'
        self.msg = template.format(name, namespace.fqn())


class NoSuchAttribute(CheckError):
    def __init__(self: 'NoSuchAttribute', type_: AnyType, attribute: str) -> None:
        template = '{} has no attribute {}'
        self.msg = template.format(type_, attribute)


class WrongBuiltinArgument(CheckError):
    def __init__(self: 'WrongBuiltinArgument', name: str, param: List, arg: List) -> None:
        template = 'Builtin function {} expected {} but got {}.'
        self.msg = template.format(name, param, arg)


class WrongArgumentsLength(CheckError):
    def __init__(self: 'WrongArgumentsLength', name: str, params_length: int, args_length: int) -> None:
        template = '{} expected {} parameters, but received {}'
        self.msg = template.format(name, params_length, args_length)


class NotCallable(CheckError):
    def __init__(self: 'NotCallable', value: AnyType) -> None:
        template = '{} is not callable'
        self.msg = template.format(value)


class InvalidAssignmentTarget(CheckError):
    def __init__(self: 'InvalidAssignmentTarget', target: AnyType) -> None:
        template = "can't assign to {}"
        self.msg = template.format(target)


class NotIterable(CheckError):
    def __init__(self: 'NotIterable', non_iterable: AnyType) -> None:
        template = 'object {} is not iterable'
        self.msg = template.format(non_iterable)


class CantSetBuiltinAttribute(CheckError):
    def __init__(self: 'CantSetBuiltinAttribute', builtin_type: AnyType) -> None:
        template = "can't set attributes of built-in/extension type {}"
        self.msg = template.format(builtin_type)

class NotPythonFile(CheckError):
    def __init__(self: 'NotPythonFile', fname: str) -> None:
        template = "only check python file ends with .py or pyi, not {}"
        self.msg = template.format(fname)

# Exceptions and exception handling
class MalformedTypeError(Exception):
    def __init__(self: 'MalFormedTypeError', node: AST, msg:str) -> None:
        self.node = node
        self.msg = msg

class StaticTypeError(Exception):
    def __init__(self: 'StaticTypeError', node: AST, msg:str) -> None:
        self.node = node
        self.msg = msg

class StaticImportError(StaticTypeError): pass

class UnimplementedException(Exception): pass

class InternalReticulatedError(Exception): pass

# print the error information in string format.
def handle_static_type_error(error:StaticTypeError, srcdata: Dict, exit: bool = True, stream: AnyType = sys.stderr) -> None:
    print('\nStatic type error:', file=stream)
    if error.node:
        print('  File "{}", line {}'.format(srcdata.filename, error.node.lineno), file=stream)
        print('   ', srcdata.src.split('\n')[error.node.lineno-1], file=stream)
        print('   ', ' ' * error.node.col_offset + '^', file=stream)
    else:
        print('  File "{}", line 1'.format(srcdata.filename), file=stream)
    print(error.msg, file=stream)
    print(file=stream)
    if exit:
        quit()

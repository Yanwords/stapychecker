"""
This module operates on the AST before any checks are made.
It's sole goal is to remove purely syntactic sugar and to replace it with a
semantically equivalent AST.
"""

import ast
from typing import Dict, List, Tuple, Any as AnyType
from .exceptions import NotYetSupported
from .types import Module

AST = ast.AST
Visitor = ast.NodeVisitor

# TODO
# x.__len__() <==> len(x)
# x.__delitem__(y) <==> del x[y]
# x.__delslice__(i, j) <==> del x[i:j]
# x.__contains__(y) <==> y in x
# x.__iadd__(y) <==> x+=y
# x.__imul__(y) <==> x*=y
# Etc


BINOP_TRANSLATION: Dict[AST, str] = {
        ast.Add: 'add',
        ast.Sub: 'sub',
        ast.Mult: 'mul',
        ast.Div: 'truediv',
        ast.Mod: 'mod',
        ast.Pow: 'pow',
        ast.LShift: 'lshift',
        ast.RShift: 'rshift',
        ast.BitOr: 'or',
        ast.BitXor: 'xor',
        ast.BitAnd: 'and',
        ast.FloorDiv: 'floordiv',
        ast.MatMult: 'matmul'
}

UNARYOP_TRANSLATION: Dict[AST, str] = {
        ast.Invert: 'invert',
        ast.UAdd: 'pos',
        ast.USub: 'neg'
}

COMPARE_TRANSLATION: Dict[AST, str] = {
        ast.Eq: 'eq',
        ast.NotEq: 'ne',
        ast.Lt: 'lt',
        ast.LtE: 'le',
        ast.Gt: 'gt',
        ast.GtE: 'ge',
        ast.IsNot: 'isnot',
        ast.Is: 'is',
}


class Not(ast.AST):
    _fields: Tuple = ('value',)


class In(ast.AST):
    _fields: Tuple = ('element', 'container')


class SugarReplacer(ast.NodeTransformer):
    def visit_BinOp(self: Visitor, node: ast.BinOp) -> AnyType:
        left = self.visit(node.left)
        right = self.visit(node.right)

        try:
            op_name = '__%s__' % BINOP_TRANSLATION[type(node.op)]
        except KeyError:
            raise NotYetSupported('binary operation', node.op)
        return _make_method_call(left, op_name, [right])

    def visit_UnaryOp(self: Visitor, node: ast.UnaryOp) -> AnyType:
        operand = self.visit(node.operand)

        if isinstance(node.op, ast.Not):
            return Not(operand)
        else:
            try:
                op_name = '__%s__' % UNARYOP_TRANSLATION[type(node.op)]
            except KeyError:
                raise NotYetSupported('unary operation', node.op)
            return _make_method_call(operand, op_name, [])

    def visit_Compare(self: Visitor, node: ast.Compare) -> AnyType:
        left = self.visit(node.left)
        comparison_nodes = []
        for op, comparator in zip(node.ops, node.comparators):
            comparator = self.visit(comparator)
            comparison = _make_comparison(left, op, comparator)
            comparison_nodes.append(comparison)
            left = comparator

        return ast.BoolOp(op=ast.And(), values=comparison_nodes)

def _make_method_call(caller: AST, method: AnyType, args: List) -> AST:
    method = ast.Attribute(value=caller, attr=method, ctx=ast.Load())
    return ast.Call(func=method, args=args, keywords=[], starargs=None,
                    kwargs=None)

def _make_comparison(left: AST, op: AST, right: AST) -> AST:
    if isinstance(op, ast.In):
        return In(left, right)
    elif isinstance(op, ast.NotIn):
        return Not(In(left, right))
    else:
        try:
            op_name = '__%s__' % COMPARE_TRANSLATION[type(op)]
            #if isinstance(op, ast.Is):
            #    print(f"op:{op_name}")
        except KeyError:
            raise NotYetSupported('comparison operator', op)
        return _make_method_call(left, op_name, [right])


def replace_syntactic_sugar(module: Module) -> None:
    replacer = SugarReplacer()
    replacer.visit(module)

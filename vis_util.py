# visitor that for ast traversal.
from typing import List as ListType, Tuple as TupleType, Any as AnyType
import ast
AST = ast.AST
from .exceptions import NotYetSupported
debug = False

class Visitor(object):
    def __init__(self: 'Visitor') -> None:
        self.node = None
        self._cache = {}

    def default(self: 'Visitor', n: AST, *args: TupleType) -> None:
        raise NotYetSupported('no visit method for type %s in %s for %s' \
                        % (n.__class__, self.__class__, repr(n)))

    def valid(self: 'Visitor', node: AST, stage: AST) -> AnyType:
        return filter(lambda x: x == stage, node.valid_stages)

    def visit(self: 'Visitor', node: AST, *args: TupelType) -> AnyType:
        if debug:
            logging.warning("%r dispatching for %r  %r in %r", self.__class__, node.__class__, node, self.__class__.__name__)
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass, None)
        if meth is None:
            className = klass.__name__
            meth = getattr(self.visitor, 'visit' + className, self.default)
            self._cache[klass] = meth

        ret = meth(node, *args)
        if debug:
            logging.warning("finished with:%r, produced:%r", node.__class__, str(ret))
        return ret

    def preorder(self: 'Visitor', tree: AST, *args: TupleType) -> AnyType:
        """Do preorder walk of tree using visitor"""
        self.visitor = self

        return self.visit(tree, *args)


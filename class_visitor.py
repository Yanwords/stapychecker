import ast
import logging
from typing import Dict, List, Any as AnyType


from .nodes import Name as nodeName
from .nodes import Attribute as nodeAttr

AST = ast.AST
Visitor = ast.NodeVisitor

SELF = None
INITIALIZE = False
TRY_EXCEPT = False
ASSIGN = False
WITH_ERROR = False

# set the class itself for attributes checking.
def setSelf(_self: AnyType) -> None:
    global SELF
    SELF = _self

# get the class instance.
def getSelf() -> AnyType:
    return SELF

# set the flag of the __init__ method.
def setInitialize(flag: bool) -> None:
    global INITIALIZE
    INITIALIZE = flag

# get the flag of __init__ method.
def getInitialize() -> bool:
    return INITIALIZE

# set the flag of try except clauses.
def setTryExcept(flag: bool) -> None:
    global TRY_EXCEPT
    TRY_EXCEPT = flag

# get the flag of try except clauses.
def getTryExcept() -> bool:
    return TRY_EXCEPT

# set the flag of assign statement.
def setAssign(flag: bool) -> None:
    global ASSIGN
    ASSIGN = flag

# get the flag of assign statement.
def getAssign() -> bool:
    return ASSIGN

# set the flag of with block.
def setWithError(flag: bool) -> None:
    global WITH_ERROR
    WITH_ERROR = flag

# get the flag of with block.
def getWithError() -> bool:
    return WITH_ERROR

# restore all the variable states.
def restoreState() -> None:
    global INITIALIZE, TRY_EXCEPT, WITH_ERROR
    INITIALIZE = False
    TRY_EXCEPT = False
    WITH_ERROR = False

# class attributes checking.
def attrChecking(attr: str) -> None:
    global SELF
    if getInitialize() or getAssign():
        from .builtins.data_types import UnDefined
        SELF.set_attribute(attr, UnDefined())
    elif not getTryExcept() and not getWithError():
        SELF.get_attribute(attr, 1.0)

# interface of visit method call.
def callVisitMethod(obj: AnyType, node: AnyType) -> None:
    visit_method = getattr(obj, f"visit_{node.__class__.__name__}")
    visit_method(node)


# visit the class node and collect all the neccessary attributes in class methods and fields.
class ClassVisitor(ast.NodeVisitor):
    
    def visit_Add(self: Visitor, node: ast.Add) -> None:
        self.generic_visit(node)
    
    def visit_And(self: Visitor, node: ast.And) -> None:
        self.generic_visit(node)
    
    def visit_AnnAssign(self: Visitor, node: ast.AnnAssign) -> None:
        if getInitialize() and isinstance(node.target, ast.Name):
            attrChecking(node.target.id)
        elif isinstance(node.target, ast.Attribute):
            setAssign(True)
            callVisitMethod(self, node.target)
            setAssign(False)
        else:
            self.generic_visit(node.target)
        self.generic_visit(node.annotation)
        if node.value:
            self.generic_visit(node.value)
    
    def visit_arg(self: Visitor, node: ast.arg) -> None:
        self.generic_visit(node)

    def visit_Assert(self: Visitor, node: ast.Assert) -> None:
        self.generic_visit(node)
    
    def visit_Assign(self: Visitor, node: ast.Assign) -> None:
        for target in node.targets:
            if getInitialize() and isinstance(target, ast.Name):
                attrChecking(target.id)
                continue
            if isinstance(target, ast.Attribute):
                setAssign(True)
                callVisitMethod(self, target)
                setAssign(False)
                continue
            self.generic_visit(target)
        self.generic_visit(node.value)
    
    def visit_AsyncFor(self: Visitor, node: ast.AsyncFor) -> None:
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self: Visitor, node: ast.AsyncFunctionDef) -> None:
        self.generic_visit(node)
        for stat in node.body:
            self.generic_visit(stat)
    
    def visit_AsyncWith(self: Visitor, node: ast.AsyncWith) -> None:
        self.generic_visit(node)
    
    def visit_Attribute(self: Visitor, node: ast.Attribute) -> None:
        value = node.value
        attr = node.attr
        if getAssign() and isinstance(value, nodeName) and value.id == 'self':
            attrChecking(attr)
        elif isinstance(value, nodeAttr):
            self.generic_visit(value)
        elif getAssign() and isinstance(value, ast.Name) and value.id == 'self':
            from .config import setLineNo
            setLineNo(value.lineno)
            attrChecking(attr)
        elif isinstance(value, ast.Attribute):
            self.generic_visit(value)
        else:
            self.generic_visit(node)
    
    def visit_AugAssign(self: Visitor, node: ast.AugAssign) -> None:
        self.generic_visit(node)
    
    def visit_AugLoad(self: Visitor, node: ast.AugLoad) -> None:
        self.generic_visit(node)
    
    def visit_AugStore(self: Visitor, node: ast.AugStore) -> None:
        self.generic_visit(node)
    
    def visit_Await(self: Visitor, node: ast.Await) -> None:
        self.generic_visit(node)
    
    def visit_BinOp(self: Visitor, node: ast.BinOp) -> None:
        self.generic_visit(node)
    
    def visit_BitAnd(self: Visitor, node: ast.BitAnd) -> None:
        self.generic_visit(node)
    
    def visit_BitOr(self: Visitor, node: ast.BitOr) -> None:
        self.generic_visit(node)
    
    def visit_BitXor(self: Visitor, node: ast.BitXor) -> None:
        self.generic_visit(node)
    
    def visit_BoolOp(self: Visitor, node: ast.BoolOp) -> None:
        self.generic_visit(node)
    
    def visit_Break(self: Visitor, node: ast.Break) -> None:
        self.generic_visit(node)
    
    def visit_Bytes(self: Visitor, node: ast.Bytes) -> None:
        self.generic_visit(node)
    
    def visit_Call(self: Visitor, node: ast.Call) -> None:
        self.generic_visit(node)
    
    def visit_ClassDef(self: Visitor, node: ast.ClassDef) -> None:
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                setInitialize(True)
                callVisitMethod(self, stmt)
                setInitialize(False)
                continue
            elif isinstance(stmt, (ast.AnnAssign, ast.Assign)):
                 setInitialize(True)
                 callVisitMethod(self, stmt)
                 setInitialize(False)
                 continue

        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__" or \
                    isinstance(stmt, ast.ClassDef):
                continue
            elif isinstance(stmt, ast.FunctionDef) and not stmt.decorator_list:
                callVisitMethod(self, stmt)
            else:
                self.generic_visit(stmt)
    
    def visit_Compare(self: Visitor, node: ast.Compare) -> None:
        self.generic_visit(node)
    
    def visit_ConstDecl(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_Constant(self: Visitor, node: ast.Constant) -> None:
        self.generic_visit(node)
    
    def visit_Continue(self: Visitor, node: ast.Continue)-> None:
        self.generic_visit(node)
    
    def visit_Del(self: Visitor, node: ast.Del) -> None:
        self.generic_visit(node)
    
    def visit_Delete(self: Visitor, node: ast.Delete) -> None:
        self.generic_visit(node)
    
    def visit_Dict(self: Visitor, node: ast.Dict) -> None:
        self.generic_visit(node)
    
    def visit_DictComp(self: Visitor, node: ast.DictComp) -> None:
        self.generic_visit(node)
    
    def visit_Div(self: Visitor, node: ast.Div) -> None:
        self.generic_visit(node)
    
    def visit_Ellipsis(self: Visitor, node: ast.Ellipsis) -> None:
        self.generic_visit(node)
    
    def visit_Eq(self: Visitor, node: ast.Eq) -> None:
        self.generic_visit(node)
    
    def visit_ExceptHandler(self: Visitor, node: ast.ExceptHandler) -> None:
        self.generic_visit(node)
    
    def visit_Expr(self: Visitor, node: ast.Expr) -> None:
        self.generic_visit(node)
    
    def visit_Expression(self: Visitor, node: ast.Expression) -> None:
        self.generic_visit(node)
    
    def visit_ExtSlice(self: Visitor, node: ast.ExtSlice) -> None:
        self.generic_visit(node)
    
    def visit_FloorDiv(self: Visitor, node: ast.FloorDiv) -> None:
        self.generic_visit(node)
    
    def visit_For(self: Visitor, node: ast.For) -> None:
        self.generic_visit(node)
    
    def visit_FormattedValue(self: Visitor, node: ast.FormattedValue) -> None:
        self.generic_visit(node)
    
    def visit_FunctionDef(self: Visitor, node: ast.FunctionDef) -> None:
        SkipFlag = False
        for dec in node.decorator_list:
            from .util1 import getDecorator
            dec_content = getDecorator(dec)
            # We skip the unneccessary checking with pytest.mark.skip.
            if dec_content == "pytest.mark.skip":
                SkipFlag = True
        if SkipFlag:
            return
        for stmt in node.body:
            # Here we need to call visit_Assign explicitly. Or it will visit stmt.fields.
            callVisitMethod(self, stmt)
    
    def visit_GeneratorExp(self: Visitor, node: ast.GeneratorExp) -> None:
        self.generic_visit(node)
    
    def visit_Global(self: Visitor, node: ast.Global) -> None:
        self.generic_visit(node)
    
    def visit_Gt(self: Visitor, node: ast.Gt) -> None:
        self.generic_visit(node)
    
    def visit_GtE(self: Visitor, node: ast.GtE) -> None:
        self.generic_visit(node)
    
    def visit_If(self: Visitor, node: ast.If) -> None:
        self.generic_visit(node)
       
    def visit_IfExp(self: Visitor, node: ast.IfExp) -> None:
        self.generic_visit(node)
    
    def visit_Import(self: Visitor, node: ast.Import) -> None:
        self.generic_visit(node)
    
    def visit_ImportFrom(self: Visitor, node: ast.ImportFrom) -> None:
        self.generic_visit(node)
    
    def visit_In(self: Visitor, node: ast.In) -> None:
        self.generic_visit(node)
    
    def visit_Index(self: Visitor, node: ast.Index) -> None:
        self.generic_visit(node)
    
    def visit_Interactive(self: Visitor, node: ast.Interactive) -> None:
        self.generic_visit(node)
    
    def visit_Invert(self: Visitor, node: ast.Invert) -> None:
        self.generic_visit(node)
    
    def visit_Is(self: Visitor, node: ast.Is) -> None:
        self.generic_visit(node)
    
    def visit_IsNot(self: Visitor, node: ast.IsNot) -> None:
        self.generic_visit(node)
    
    def visit_JoinedStr(self: Visitor, node: ast.JoinedStr) -> None:
        self.generic_visit(node)
    
    def visit_LShift(self: Visitor, node: ast.LShift) -> None:
        self.generic_visit(node)
    
    def visit_Lambda(self: Visitor, node: ast.Lambda) -> None:
        self.generic_visit(node)
    
    def visit_List(self: Visitor, node: ast.List) -> None:
        self.generic_visit(node)
    
    def visit_ListComp(self: Visitor, node: ast.ListComp) -> None:
        self.generic_visit(node)
    
    def visit_Load(self: Visitor, node: ast.Load) -> None:
        self.generic_visit(node)
    
    def visit_Lt(self: Visitor, node: ast.Lt) -> None:
        self.generic_visit(node)
    
    def visit_LtE(self: Visitor, node: ast.LtE) -> None:
        self.generic_visit(node)
    
    def visit_MatMult(self: Visitor, node: ast.MatMult) -> None:
        self.generic_visit(node)
    
    def visit_Mod(self: Visitor, node: ast.Mod) -> None:
        self.generic_visit(node)
    
    def visit_Module(self: Visitor, node: ast.Module) -> None:
        self.generic_visit(node)
    
    def visit_Mult(self: Visitor, node: ast.Mult) -> None:
        self.generic_visit(node)
    
    def visit_Name(self: Visitor, node: ast.Name) -> None:
        self.generic_visit(node)
    
    def visit_NameConstant(self: Visitor, node: ast.NameConstant) -> None:
        self.generic_visit(node)
    
    def visit_Nonlocal(self: Visitor, node: ast.Nonlocal) -> None:
        self.generic_visit(node)
    
    def visit_Not(self: Visitor, node: ast.Not) -> None:
        self.generic_visit(node)
    
    def visit_NotEq(self: Visitor, node: ast.NotEq) -> None:
        self.generic_visit(node)
    
    def visit_NotIn(self: Visitor, node: ast.NotIn) -> None:
        self.generic_visit(node)
    
    def visit_Num(self: Visitor, node: ast.Num) -> None:
        self.generic_visit(node)
    
    def visit_Or(self: Visitor, node: ast.Or) -> None:
        self.generic_visit(node)
    
    def visit_Param(self: Visitor, node: ast.Param) -> None:
        self.generic_visit(node)
    
    def visit_Pass(self: Visitor, node: ast.Pass) -> None:
        self.generic_visit(node)
    
    def visit_Pow(self: Visitor, node: ast.Pow) -> None:
        self.generic_visit(node)
    
    def visit_RShift(self: Visitor, node: ast.RShift) -> None:
        self.generic_visit(node)
    
    def visit_Raise(self: Visitor, node: ast.Raise) -> None:
        self.generic_visit(node)
    
    def visit_Return(self: Visitor, node: ast.Return) -> None:
        self.generic_visit(node)
    
    def visit_Set(self: Visitor, node: ast.Set) -> None:
        self.generic_visit(node)
    
    def visit_SetComp(self: Visitor, node: ast.SetComp) -> None:
        self.generic_visit(node)
    
    def visit_Slice(self: Visitor, node: ast.Slice) -> None:
        self.generic_visit(node)
    
    def visit_Starred(self: Visitor, node: ast.Starred) -> None:
        self.generic_visit(node)
    
    def visit_Store(self: Visitor, node: ast.Store) -> None:
        self.generic_visit(node)
    
    def visit_Str(self: Visitor, node: ast.Str) -> None:
        self.generic_visit(node)
    
    def visit_Sub(self: Visitor, node: ast.Sub) -> None:
        self.generic_visit(node)
    
    def visit_Subscript(self: Visitor, node: ast.Subscript) -> None:
        self.generic_visit(node)
    
    def visit_Suite(self: Visitor, node: ast.Suite) -> None:
        self.generic_visit(node)
    
    def visit_Try(self: Visitor, node: ast.Try) -> None:
        attr_flag = False
        for handler in node.handlers:
            hand_type = handler.type
            if isinstance(hand_type, ast.Tuple):
                for elt in hand_type.elts:
                    if not hasattr(elt, 'id'):
                        continue
                    if elt.id == "AttributeError":
                        attr_flag = True
            elif isinstance(hand_type, ast.Name):
                if hand_type.id == "AttributeError":
                    attr_flag = True
            elif hand_type is None:
                attr_flag = True
        bkp_flag = getTryExcept() 
        if attr_flag:
            setTryExcept(attr_flag)
        self.generic_visit(node)
        setTryExcept(bkp_flag)

    
    def visit_Tuple(self: Visitor, node: ast.Tuple) -> None:
        self.generic_visit(node)
    
    def visit_TypeDef(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_UAdd(self: Visitor, node: ast.UAdd) -> None:
        self.generic_visit(node)
    
    def visit_USub(self: Visitor, node: ast.USub) -> None:
        self.generic_visit(node)
    
    def visit_UnaryOp(self: Visitor, node: ast.UnaryOp) -> None:
        self.generic_visit(node)
    
    def visit_VarDecl(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_While(self: Visitor, node: ast.While) -> None:
        self.generic_visit(node)
    
    def visit_With(self: Visitor, node: ast.With) -> None:
        bkp_flag = getWithError()
        self.generic_visit(node)
        setWithError(bkp_flag)
    
    def visit_withitem(self: Visitor, node: ast.withitem) -> None:
        context_expr = node.context_expr
        if isinstance(context_expr, ast.Call):
            args = context_expr.args
            for arg in args:
                if isinstance(arg, ast.Name) and arg.id == "AttributeError":
                    setWithError(True)
        self.generic_visit(node)

    def visit_Yield(self: Visitor, node: ast.Yield) -> None:
        self.generic_visit(node)
    
    def visit_YieldFrom(self: Visitor, node: ast.YieldFrom) -> None:
        self.generic_visit(node)

# visit the class object and checking the fields reference in the class methods body.
class ClassAttrCheckerVisitor(ast.NodeVisitor):
    
    def visit_Add(self: Visitor, node: ast.Add) -> None:
        self.generic_visit(node)
    
    def visit_And(self: Visitor, node: ast.And) -> None:
        self.generic_visit(node)
    
    def visit_AnnAssign(self: Visitor, node: ast.AnnAssign) -> None:
        self.generic_visit(node)   

    def visit_arg(self: Visitor, node: ast.arg) -> None:
        self.generic_visit(node)

    def visit_Assert(self: Visitor, node: ast.Assert) -> None:
        self.generic_visit(node)
    
    def visit_Assign(self: Visitor, node: ast.Assign) -> None:
        self.generic_visit(node.value)

    def visit_AsyncFor(self: Visitor, node: ast.AsyncFor) -> None:
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self: Visitor, node: ast.AsyncFunctionDef) -> None:
        self.generic_visit(node)
        for stat in node.body:
            self.generic_visit(stat)
    
    def visit_AsyncWith(self: Visitor, node: ast.AsyncWith) -> None:
        self.generic_visit(node)
    
    def visit_Attribute(self: Visitor, node: ast.Attribute) -> None:
        value = node.value
        attr = node.attr
        if isinstance(value, nodeName) and value.id == 'self':
            attrChecking(attr)
        elif isinstance(value, nodeAttr):
            self.generic_visit(value)
        elif isinstance(value, ast.Name) and value.id == 'self':
            from .config import setLineNo
            setLineNo(value.lineno)
            attrChecking(attr)
        elif isinstance(value, ast.Attribute):
            self.generic_visit(value)
        else:
            self.generic_visit(node)
    
    def visit_AugAssign(self: Visitor, node: ast.AugAssign) -> None:
        self.generic_visit(node)
    
    def visit_AugLoad(self: Visitor, node: ast.AugLoad) -> None:
        self.generic_visit(node)
    
    def visit_AugStore(self: Visitor, node: ast.AugStore) -> None:
        self.generic_visit(node)
    
    def visit_Await(self: Visitor, node: ast.Await) -> None:
        self.generic_visit(node)
    
    def visit_BinOp(self: Visitor, node: ast.BinOp) -> None:
        self.generic_visit(node)
    
    def visit_BitAnd(self: Visitor, node: ast.BitAnd) -> None:
        self.generic_visit(node)
    
    def visit_BitOr(self: Visitor, node: ast.BitOr) -> None:
        self.generic_visit(node)
    
    def visit_BitXor(self: Visitor, node: ast.BitXor) -> None:
        self.generic_visit(node)
    
    def visit_BoolOp(self: Visitor, node: ast.BoolOp) -> None:
        self.generic_visit(node)
    
    def visit_Break(self: Visitor, node: ast.Break) -> None:
        self.generic_visit(node)
    
    def visit_Bytes(self: Visitor, node: ast.Bytes) -> None:
        self.generic_visit(node)
    
    def visit_Call(self: Visitor, node: ast.Call) -> None:
        self.generic_visit(node)
    
    def visit_ClassDef(self: Visitor, node: ast.ClassDef) -> None:
        
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                setInitialize(True)
                callVisitMethod(self, stmt)
                setInitialize(False)
                continue
            elif isinstance(stmt, (ast.AnnAssign, ast.Assign)):
                 setInitialize(True)
                 callVisitMethod(self, stmt)
                 setInitialize(False)
                 continue
        
        
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__" or \
                    isinstance(stmt, ast.ClassDef):
                continue
            elif isinstance(stmt, ast.FunctionDef) and not stmt.decorator_list:
                callVisitMethod(self, stmt)
            else:
                self.generic_visit(stmt)
        
    def visit_Compare(self: Visitor, node: ast.Compare) -> None:
        self.generic_visit(node)
    
    def visit_ConstDecl(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_Constant(self: Visitor, node: ast.Constant) -> None:
        self.generic_visit(node)
    
    def visit_Continue(self: Visitor, node: ast.Continue) -> None:
        self.generic_visit(node)
    
    def visit_Del(self: Visitor, node: ast.Del) -> None:
        self.generic_visit(node)
    
    def visit_Delete(self: Visitor, node: ast.Delete) -> None:
        self.generic_visit(node)
    
    def visit_Dict(self: Visitor, node: ast.Dict) -> None:
        self.generic_visit(node)
    
    def visit_DictComp(self: Visitor, node: ast.DictComp) -> None:
        self.generic_visit(node)
    
    def visit_Div(self: Visitor, node: ast.Div) -> None:
        self.generic_visit(node)
    
    def visit_Ellipsis(self: Visitor, node: ast.Ellipsis) -> None:
        self.generic_visit(node)
    
    def visit_Eq(self: Visitor, node: ast.Eq) -> None:
        self.generic_visit(node)
    
    def visit_ExceptHandler(self: Visitor, node: ast.ExceptHandler) -> None:
        self.generic_visit(node)
    
    def visit_Expr(self: Visitor, node: ast.Expr) -> None:
        self.generic_visit(node)
    
    def visit_Expression(self: Visitor, node: ast.Expression) -> None:
        self.generic_visit(node)
    
    def visit_ExtSlice(self: Visitor, node: ast.ExtSlice) -> None:
        self.generic_visit(node)
    
    def visit_FloorDiv(self: Visitor, node: ast.FloorDiv) -> None:
        self.generic_visit(node)
    
    def visit_For(self: Visitor, node: ast.For) -> None:
        self.generic_visit(node)
    
    def visit_FormattedValue(self: Visitor, node: ast.FormattedValue) -> None:
        self.generic_visit(node)
    
    def visit_FunctionDef(self: Visitor, node: ast.FunctionDef) -> None:
        for stmt in node.body:
            # Here we need to call visit_Assign explicitly. Or it will visit stmt.fields.
            callVisitMethod(self, stmt)
    
    def visit_GeneratorExp(self: Visitor, node: ast.GeneratorExp) -> None:
        self.generic_visit(node)
    
    def visit_Global(self: Visitor, node: ast.Global) -> None:
        self.generic_visit(node)
    
    def visit_Gt(self: Visitor, node: ast.Gt) -> None:
        self.generic_visit(node)
    
    def visit_GtE(self: Visitor, node: ast.GtE) -> None:
        self.generic_visit(node)
    
    def visit_If(self: Visitor, node: ast.If) -> None:
        self.generic_visit(node)
       
    def visit_IfExp(self: Visitor, node: ast.IfExp) -> None:
        self.generic_visit(node)
    
    def visit_Import(self: Visitor, node: ast.Import) -> None:
        self.generic_visit(node)
    
    def visit_ImportFrom(self: Visitor, node: ast.ImportFrom) -> None:
        self.generic_visit(node)
    
    def visit_In(self: Visitor, node: ast.In) -> None:
        self.generic_visit(node)
    
    def visit_Index(self: Visitor, node: ast.Index) -> None:
        self.generic_visit(node)
    
    def visit_Interactive(self: Visitor, node: ast.Interactive) -> None:
        self.generic_visit(node)
    
    def visit_Invert(self: Visitor, node: ast.Invert) -> None:
        self.generic_visit(node)
    
    def visit_Is(self: Visitor, node: ast.Is) -> None:
        self.generic_visit(node)
    
    def visit_IsNot(self: Visitor, node: ast.IsNot) -> None:
        self.generic_visit(node)
    
    def visit_JoinedStr(self: Visitor, node: ast.JoinedStr) -> None:
        self.generic_visit(node)
    
    def visit_LShift(self: Visitor, node: ast.LShift) -> None:
        self.generic_visit(node)
    
    def visit_Lambda(self: Visitor, node: ast.Lambda) -> None:
        self.generic_visit(node)
    
    def visit_List(self: Visitor, node: ast.List) -> None:
        self.generic_visit(node)
    
    def visit_ListComp(self: Visitor, node: ast.ListComp) -> None:
        self.generic_visit(node)
    
    def visit_Load(self: Visitor, node: ast.Load) -> None:
        self.generic_visit(node)
    
    def visit_Lt(self: Visitor, node: ast.Lt) -> None:
        self.generic_visit(node)
    
    def visit_LtE(self: Visitor, node: ast.LtE) -> None:
        self.generic_visit(node)
    
    def visit_MatMult(self: Visitor, node: ast.MatMult) -> None:
        self.generic_visit(node)
    
    def visit_Mod(self: Visitor, node: ast.Mod) -> None:
        self.generic_visit(node)
    
    def visit_Module(self: Visitor, node: ast.Module) -> None:
        self.generic_visit(node)
    
    def visit_Mult(self: Visitor, node: ast.Mult) -> None:
        self.generic_visit(node)
    
    def visit_Name(self: Visitor, node: ast.Name) -> None:
        self.generic_visit(node)
    
    def visit_NameConstant(self: Visitor, node: ast.NameConstant) -> None:
        self.generic_visit(node)
    
    def visit_Nonlocal(self: Visitor, node: ast.Nonlocal) -> None:
        self.generic_visit(node)
    
    def visit_Not(self: Visitor, node: ast.Not) -> None:
        self.generic_visit(node)
    
    def visit_NotEq(self: Visitor, node: ast.NotEq) -> None:
        self.generic_visit(node)
    
    def visit_NotIn(self: Visitor, node: ast.NotIn) -> None:
        self.generic_visit(node)
    
    def visit_Num(self: Visitor, node: ast.Num) -> None:
        self.generic_visit(node)
    
    def visit_Or(self: Visitor, node: ast.Or) -> None:
        self.generic_visit(node)
    
    def visit_Param(self: Visitor, node: ast.Param) -> None:
        self.generic_visit(node)
    
    def visit_Pass(self: Visitor, node: ast.Pass) -> None:
        self.generic_visit(node)
    
    def visit_Pow(self: Visitor, node: ast.Pow) -> None:
        self.generic_visit(node)
    
    def visit_RShift(self: Visitor, node: ast.RShift) -> None:
        self.generic_visit(node)
    
    def visit_Raise(self: Visitor, node: ast.Raise) -> None:
        self.generic_visit(node)
    
    def visit_Return(self: Visitor, node: ast.Return) -> None:
        self.generic_visit(node)
    
    def visit_Set(self: Visitor, node: ast.Set) -> None:
        self.generic_visit(node)
    
    def visit_SetComp(self: Visitor, node: ast.SetComp) -> None:
        self.generic_visit(node)
    
    def visit_Slice(self: Visitor, node: ast.Slice) -> None:
        self.generic_visit(node)
    
    def visit_Starred(self: Visitor, node: ast.Starred) -> None:
        self.generic_visit(node)
    
    def visit_Store(self: Visitor, node: ast.Store) -> None:
        self.generic_visit(node)
    
    def visit_Str(self: Visitor, node: ast.Str) -> None:
        self.generic_visit(node)
    
    def visit_Sub(self: Visitor, node: ast.Sub) -> None:
        self.generic_visit(node)
    
    def visit_Subscript(self: Visitor, node: ast.Subscript) -> None:
        self.generic_visit(node)
    
    def visit_Suite(self: Visitor, node: ast.Suite) -> None:
        self.generic_visit(node)
    
    def visit_Try(self: Visitor, node: ast.Try) -> None:
        attr_flag = False
        for handler in node.handlers:
            hand_type = handler.type
            if isinstance(hand_type, ast.Tuple):
                for elt in hand_type.elts:
                    if not hasattr(elt, 'id'):
                        continue
                    if elt.id == "AttributeError":
                        attr_flag = True
            elif isinstance(hand_type, ast.Name):
                if hand_type.id == "AttributeError":
                    attr_flag = True
            elif hand_type is None:
                attr_flag = True
        bkp_flag = getTryExcept() 
        if attr_flag:
            setTryExcept(attr_flag)
        self.generic_visit(node)
        setTryExcept(bkp_flag)
    
    def visit_Tuple(self: Visitor, node: ast.Tuple) -> None:
        self.generic_visit(node)
    
    def visit_TypeDef(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_UAdd(self: Visitor, node: ast.UAdd) -> None:
        self.generic_visit(node)
    
    def visit_USub(self: Visitor, node: ast.USub) -> None:
        self.generic_visit(node)
    
    def visit_UnaryOp(self: Visitor, node: ast.UnaryOp) -> None:
        self.generic_visit(node)
    
    def visit_VarDecl(self: Visitor, node: AST) -> None:
        self.generic_visit(node)
    
    def visit_While(self: Visitor, node: ast.While) -> None:
        self.generic_visit(node)
    
    def visit_With(self: Visitor, node: ast.With) -> None:
        bkp_flag = getWithError()
        self.generic_visit(node)
        setWithError(bkp_flag)
    
    def visit_withitem(self: Visitor, node: ast.withitem) -> None:
        context_expr = node.context_expr
        if isinstance(context_expr, ast.Call):
            args = context_expr.args
            for arg in args:
                if isinstance(arg, ast.Name) and arg.id == "AttributeError":
                    setWithError(True)
        self.generic_visit(node)

    def visit_Yield(self: Visitor, node: ast.Yield) -> None:
        self.generic_visit(node)
    
    def visit_YieldFrom(self: Visitor, node: ast.YieldFrom) -> None:
        self.generic_visit(node)
    

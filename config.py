# Global variables for our checker. We set these variables before type checking.
import ast
AST = ast.AST

FILE_NAME: str = ""
LINE_NO: int = 0
ROOT_DIR: str = '.'
CUR_NODE: AST = None
TYPE_PROB: float = -1
ATTR_ERROR: bool = False
TYPE_ERROR: bool = False
DEBUG: bool = False
B_NAME: str = ""
IMPORT_FROM: bool = False

def setBName(name: str) -> None:
    global B_NAME
    B_NAME = name

def getBName() -> str:
    return B_NAME

def getFileName() -> str:
    return FILE_NAME

def setFileName(fname: str) -> None:
    global FILE_NAME
    FILE_NAME = fname

def getLineNo() -> int:
    return LINE_NO

def setLineNo(lno: int) -> None:
    global LINE_NO
    LINE_NO = lno

def getRootDir() -> str:
    return ROOT_DIR

def setRootDir(dir: str) -> None:
    global ROOT_DIR
    ROOT_DIR = dir

def setCurNode(node: AST) -> None:
    global CUR_NODE
    CUR_NODE = node

def getCurNode() -> AST:
    return CUR_NODE

def setTypeProb(prob: float) -> None:
    global TYPE_PROB
    TYPE_PROB = prob

def getTypeProb() -> float:
    return TYPE_PROB

def setAttrError(error_flag: bool) -> None:
    global ATTR_ERROR
    ATTR_ERROR = error_flag

def getAttrError() -> bool:
    return ATTR_ERROR

def setTypeError(error_flag: bool) -> None:
    global TYPE_ERROR
    TYPE_ERROR = error_flag

def getTypeError() -> bool:
    return TYPE_ERROR

def setDebug(isDebug: bool) -> bool:
    global DEBUG
    DEBUG = isDebug
    
def getDebug() -> bool:
    return DEBUG

def setImportFrom(imp: bool) -> bool:
    global IMPORT_FROM
    IMPORT_FROM = imp

def getImportFrom() -> bool:
    return IMPORT_FROM

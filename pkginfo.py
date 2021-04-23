# source directory information setter and getter module.
PKG: str = ""
SUBPKG: str = ""

def setPkg(pkg: str) -> None:
    global PKG
    PKG = pkg

def getPkg() -> str:
    return PKG

def setSubPkg(spkg: str) -> None:
    global SUBPKG
    SUBPKG = spkg

def getSubPkg() -> str:
    return SUBPKG 

# module for the checker tests. We write the types of the special types, only for debugging.
import os

PKG: str = ""
filepath: str = ""
typepath: str = ""
unionpath: str = ""
file: str = ""
typefile: str = ""
unionfile:str = ""

# setter and getter of the current package name of the source directory. 
def setPkg(pkg: str) -> None:
    pkg = pkg.replace("check", "")
    global PKG, filepath, typepath, unionpath, file, typefile, unionfile
    filepath = os.path.sep.join(["./ProbResults", pkg + "_results.txt"])
    typepath = os.path.sep.join(["./ProbResults", pkg + "_prob_types.txt"])
    unionpath = os.path.sep.join(["./ProbResults", pkg + "_union.txt"])
    #writeTypes(f"{os.getcwd()},abs:{os.path.abspath(typepath)}Hello,world!")
    PKG = pkg
    file = open(filepath, "w+") 
    typefile = open(typepath, "w+") 
    unionfile = open(unionpath, "w+") 

    writeTypes(f"{os.getcwd()},abs:{os.path.abspath(typepath)}Hello,world!")

def getPkg() -> str:
    return PKG

# function that write the filename.
def writeFileName(fname: str) -> None:
    file.write(fname)
    file.write('\n')

# close all the files we open before.
def closeFile() -> None:
    if not isinstance(typefile, str):
        typefile.close()
    if not isinstance(file, str):
        file.close()
    if not isinstance(unionfile, str):
        unionfile.close()

# write types to specific files.
def writeTypes(content: str) -> None:
    typefile.write(content)
    typefile.write('\n')

# write probabilistic types into the file for debugging.
def writeUnionContent(content: str) -> None:
    unionfile.write(content)
    unionfile.write("\n")

if __name__ == "__main__":
    filepath = os.path.sep.join(["./ProbResults", getPkg() + "_results.txt"])
    typepath = os.path.sep.join(["./ProbResults", getPkg() + "_prob_types.txt"])
    unionpath = os.path.sep.join(["./ProbResults", getPkg() + "_union.txt"])
    file = open("./results.txt", "w+")
    typefile = open("./types.txt", "w+")
    unionfile = open("./union.txt", "w+")
    file = open(filepath, "w+")
    typefile = open(typepath, "w+")
    unionfile = open(unionpath, "w+")


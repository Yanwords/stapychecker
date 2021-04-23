#!/usr/bin/python371

# Convert one static file types that inferred by Proba to our builtin data types.

import re
import sys
import os
from typing import Dict, List, Tuple, Any as AnyType

#SDataDir = "/home/yyy/checkerfile/Type/master/Current/NamingProject/SData/"
PKG = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-3])
SDataDir = os.path.sep.join([PKG, "SData", ""])

# return the location of the identifier.
def getLocation(location: str) -> Tuple[int]:
    lineno, offset = location.split(':')
    start, end = offset.split('-')
    return int(lineno), int(start), int(end)

# convert string types to our builtin data types that the checker can notify.
def getStaticTypes(filepath: str, HIGH_Prob: Tuple[int]) -> AnyType:
    staTypes = []
     
    with open(filepath, 'r', encoding='utf-8') as file:
        allLines = file.readlines()
        for line in allLines:
            name, location, stype = re.findall('<<(.*?)>>', line)[:3]
            lineno, start, end = getLocation(location)
            if stype == "?":
                stype = 'Any'
            staTypes.append((filepath, lineno, start, end, name, stype, HIGH_Prob))
    
    return staTypes

# return the string type format of the source file.
def getOriginTypes(file: str) -> str:
    if file == ".txt":
        return [('', 34, 401, 0, 'fdd', 'Foo', 1.0)]
    if not os.path.isfile(SDataDir + file):
        return [] 
    staTypes = getStaticTypes(SDataDir + file, 1.0)
    staTypes = sorted(staTypes, key=lambda x:(x[1], x[2]))
    return staTypes    

#if __name__ == '__main__':
#    results = getAllTypes()
#    for item in results:
#        print(item)

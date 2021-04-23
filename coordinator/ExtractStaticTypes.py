#!/usr/bin/python371

import re
import sys
import os
import numpy as np
from typing import List, Dict, Tuple, Any as AnyType

from .union_type import UnionType as Union

PKG: str = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-3]) 

#SDataDir = os.path.sep.join([PKG, "SData", ""])  
# For testing, we import the union_type directly.
StaTypePath: str = os.path.sep.join([PKG, "MData", ""])  
#StaTypePath: str = "/home/yyy/checkerfile/Type/master/Current/NamingProject/MData/"
sta_pattern: AnyType = re.compile(r"([\w]+)\s([<|\w]+|[\(].*|[\[].*|[?\w]+\s[->\s[\w]+]?|[<][\w]+[>]\s[|]\s[?|\w]+\s[->]*\s[?|\w]+)\s([\w]+|[\|+[\w]+]?)\s(.*)\s(.*)\s")

ProbTypePath: str = os.path.sep.join([PKG, "tests", "log", ""])  
#ProbTypePath:str = "/home/yyy/checkerfile/Type/master/Current/NamingProject/tests/log/"
prob_pattern: AnyType = re.compile(r"(\[.*\])\s(\[[R|B][\d]+\])[(]([\w]+)[)][<](.*)[>]\s(\[[^\]]*\])[\[](.*)[\]]\s[\[]([^\]]*)[\]](\[.*\])")

staTypes: List = []
probTypes: List = []
staDict: Dict = {}
probDict: Dict = {}

# softmax function that normalize the probabilistic vector.
def softmax(probs: List) -> List:
    max_prob = np.max(probs)
    exp_probs = np.exp(probs - max_prob)
    sum_exp_probs = np.sum(exp_probs)
    new_probs = exp_probs / sum_exp_probs
    return new_probs.tolist()

# Get the identifier location.
def getLocation(location: str) -> Tuple:
    if location.startswith("<") \
        and location.endswith(">"):
        loc_list = list(location)
        loc_list.pop(len(location) - 1)
        loc_list.pop(0)
        location = ''.join(loc_list)
    path, line_offset = location.split("#")
    lineno, offset = line_offset.split(':')
    start, end = offset.split('-')
    return path, int(lineno), int(start), int(end)

# convert probabilistic types to Our builti Union Types.
def convertProbTypes(ptypes: str) -> Union:
    R_FLAG = False
    if ", " in ptypes:
        ptypes = ptypes.replace(", ", "* ")
        R_FLAG = True
    items = ptypes.split(',')
    telts = []
    probs = [] 
    count = 0 
    for item in items:
        if not item:
            continue
        if R_FLAG and "* " in item:
            item = item.replace("* ", ", ")
        t, p = item.split(':')
        t = t.strip('<>')
        t = t.strip()
        if count >= 3:
            break
        count += 1
        telts.append(t)
        probs.append(float(p))
    probs = softmax(probs) if probs else probs
    return Union(None, telts, probs)

# Get prob static types.
def getStaticTypes(filepath: str, HIGH_Prob: Tuple) -> None:
    global staTypes    
    with open(filepath, 'r', encoding='utf-8') as file:
        allLines = file.readlines()
        for line in allLines:
            data = sta_pattern.match(line)
            if not data:
                continue
            name, stype, dtype, kind, location = data.groups()
            path, lineno, start, end = getLocation(location)
            staTypes.append((path, lineno, start, end, name, stype, dtype, HIGH_Prob))

# get project probabilistic types.
def getProbTypes(filepath: str) -> None:
    global probTypes
    with open(filepath, 'r', encoding='utf-8') as file:
        allLines = file.readlines()
        idx = 1
        for line in allLines:
            idx += 1
            data = prob_pattern.match(line)
            cid, gid, name, location, types_num, prob_types, d_types, r_types = data.groups()
            path, lineno, start, end = getLocation(location)
            prob_types = convertProbTypes(prob_types)
            probTypes.append((path, lineno, start, end, name, prob_types, d_types, eval(types_num)))

# get project file checking result path.
def getProbPath(directory: str) -> str:
    for root, dirs, files in os.walk(directory):
        for _file in files:
            if _file.startswith("analysis-results"):
                path = os.path.sep.join([directory, _file])
                return path
    return directory

# get project static and inferred types.
def getAllTypes() -> None:
    global staTypes, probTypes, staDict, probDict, StaTypePath, ProbTypePath
    from .. import pkginfo
    if pkginfo.getPkg() \
        and pkginfo.getSubPkg():
        StaTypePath += os.path.sep.join([pkginfo.getSubPkg(), 'same.txt'])
        probPath = getProbPath(ProbTypePath + pkginfo.getPkg().replace("check", "")) 
    getStaticTypes(StaTypePath, 1.0)
    getProbTypes(probPath)
    staTypes = sorted(staTypes, key=lambda x:(x[0], x[1], x[2]))
    probTypes = sorted(probTypes, key=lambda x:(x[0], x[1], x[2]))
    for item in staTypes:
        if item[0] not in staDict:
            staDict[item[0]] = []
        staDict[item[0]].append(item[1:])
    for item in probTypes:
        if item[0] not in probDict:
            probDict[item[0]] = []
        probDict[item[0]].append(item[1:])

# return the collected types and probability.
def getDynTypes(dtypes: str) -> Tuple:
    dtypes = dtypes.split(",")
    dlst = list()
    dprob = list()
    for item in dtypes:
        dt, dp = item.split(":")
        dlst.append(dt)
        dprob.append(float(dp))
    return dlst, dprob

if __name__ == '__main__':
    
    pkg_list = ['cerberus']
    for pkg in pkg_list:    
        path = getProbPath(ProbTypePath + pkg)
        probTypes = list()
        getProbTypes(path)
        tcount = 0
        fcount = 0
        account = len(probTypes)
        for pt in probTypes:
            pts = pt[5].elts
            dt, dp = getDynTypes(pt[6])
            isTrue = [x for x in pts if x in dt]
            if isTrue:
                tcount += 1
            else:
                fcount += 1
        print("pkg_name:", pkg)
        print("True Positives", tcount / account)
        print("False Positives", fcount / account)


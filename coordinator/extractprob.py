
# extract the project types and convert them to our builtin data types.
import re
import sys
import os
from typing import Dict, List, Tuple, Any as AnyType

from union_type import Union

PKG: str = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-3]) 
#SDataDir = os.path.sep.join([PKG, "SData", ""])  
# project static inferred types location. 
StaTypePath:str = os.path.sep.join([PKG, "MData", ""])   
#StaTypePath: str = "/home/yyy/checkerfile/Type/master/Current/NamingProject/MData/"
#sta_pattern = re.compile(r"([\w]+)\s([\w]+|[\(].*|[\[].*|[->\s[\w]+]?|[<][\w]+[>]\s[|]\s[?|\w]+\s[->]*\s[?|\w]+)\s([\w]+|[\|+[\w]+]?)\s(.*)\s(.*)\s")
sta_pattern: AnyType = re.compile(r"([\w]+)\s([<|\w]+|[\(].*|[\[].*|[?\w]+\s[->\s[\w]+]?|[<][\w]+[>]\s[|]\s[?|\w]+\s[->]*\s[?|\w]+)\s([\w]+|[\|+[\w]+]?)\s(.*)\s(.*)\s")

#sta_pattern = re.compile(r"([\w]+)\s([\w]+|[\(].*|[\[].*|[->\s[\w]+]?)\s([\w]+|[\|+[\w]+]?)\s(.*)\s(.*)\s")
# project probabilistic inferred types location.
ProbTypePath: str = os.path.sep.join([PKG, "tests", "log", ""])
#ProbTypePath: str = "/home/yyy/checkerfile/Type/master/Current/NamingProject/tests/log/"

prob_pattern: AnyType = re.compile(r"(\[.*\])\s(\[[R|B][\d]+\])[(]([\w]+)[)][<](.*)[>]\s(\[[^\]]*\])[\[](.*)[\]]\s[\[]([^\]]*)[\]](\[.*\])")

staTypes: List = []
probTypes: List = []
staDict:Dict = {}
probDict:Dict = {}

stat:Dict = {} 

for k in range(11): 
    key = 'interval' + str(k) 
    stat[key] = 0 
# probability interval.
def mapInterval(prob: float) -> None: 
    global stat 
    p = prob * 100
    key = "interval" + str(int(p))[0] \
          if p < 100 else "interval10"
    stat[key] += 1 

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

# convert string probabilistic types to our Union Type.
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
    p_sum = sum(probs)
    probs = [p/p_sum for p in probs] \
            if probs else probs
    return Union(None, telts, probs)

# Get project static types.
def getStaticTypes(filepath: str, HIGH_Prob: float) -> None:
    #staTypes = []
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

# Get probabilstic inferred types.
def getProbTypes(filepath: str) -> None:
    #probTypes = []
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

# Get static and inferred types.
def getAllTypes() -> None:
    global staTypes, probTypes, staDict, probDict, StaTypePath, ProbTypePath
    from .. import pkginfo
    if pkginfo.getPkg() \
        and pkginfo.getSubPkg():
        StaTypePath += os.path.sep.join([pkginfo.getSubPkg(), 'same.txt'])
        ProbTypePath += os.path.sep.join([pkginfo.getPkg().replace("check", ""), 'analysis-results-4-95-70.txt'])
    getStaticTypes(StaTypePath, 0.95)
    getProbTypes(ProbTypePath)
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

# Get project dynamic types.
def getDynTypes(dtypes :str) -> Tuple:
    dtypes = dtypes.split(",")
    dlst = list()
    dprob = list()
    for item in dtypes:
        dt, dp = item.split(":")
        dlst.append(dt)
        dprob.append(float(dp))
    return dlst, dprob

if __name__ == '__main__':
    #getAllTypes()
    pkg_list = ['ansible', 'bokeh', 'cerberus', 'factory', 'invoke', 'hunter', \
            'pydantic', 'pygal', 'sc2', 'schematics', 'seaborn', 'shortcuts']
    for pkg in pkg_list:    
        path =ProbTypePath + os.path.sep.join([pkg, 'analysis-results-4-95-70.txt']) 
        probTypes = list()
        getProbTypes(path)
        tcount = 0
        fcount = 0
        account = len(probTypes)
        stat = dict()
        for k in range(11):
            #stat[key] = 0
            key = 'interval' + str(k)
            stat[key] = 0  
        print("account:", account)   
        for pt in probTypes:
            pts = pt[5].elts
            pp = pt[5].probs
            for p in pp:
                mapInterval(p)
            dt, dp = getDynTypes(pt[6])
            isTrue = [x for x in pts if x in dt]
            if isTrue:
                tcount += 1
            else:
                fcount += 1
        print("pkg_name:", pkg)
        t_num = 0
        for i, c in stat.items():
            t_num += c
            print(f"{i}: {c}")
        print("type num:", t_num)
        print("True Positives", tcount / account)
        print("False Positives", fcount / account)


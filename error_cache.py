ERROR_LISTS = []

def addError(EName: str, fname: str, lineNo: int, name: str) -> bool:
    if not isinstance(name, str):
        name = str(name)
    item = "_".join([EName, fname, str(lineNo), name])
    if item not in ERROR_LISTS:
        ERROR_LISTS.append(item)
        return True
    else:
        return False

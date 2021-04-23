ERROR_LISTS = []

def addError(EName: str, fname: str, lineNo: int, name: str) -> bool:
    if not isinstance(name, str):
        import sys
        import traceback

        sys.stderr.write(f"Name is not string fromat, while error cache:{name}, {traceback.print_stack()}")
        name = str(name)
    item = "_".join([EName, fname, str(lineNo), name])
    if item not in ERROR_LISTS:
        ERROR_LISTS.append(item)
        return True
    else:
        return False

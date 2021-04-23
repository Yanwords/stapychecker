from typing import Any as AnyType
# write our types and probability into file.
file:AnyType  = open("type_results.txt", "w+")

def writeTypesProb(types: str, prob: str) -> None:
    if not isinstance(types, list):
        if not isinstance(types, str):
            file.write(str(types))
        else:
            file.write(types)
    else:
        file.write(str(types))
    file.write('   ')
    file.write(str(prob))
    file.write('\n')

def closeFile() -> None:
    file.close()

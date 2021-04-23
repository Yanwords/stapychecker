import os
PKG = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-2])
SDataDir = os.path.sep.join([PKG, "typeshed_3"])
print(SDataDir)


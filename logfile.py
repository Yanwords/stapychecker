import logging
# set the logging level and logging information format.

from .config import getFileName, getLineNo

filename: str = "logger.log"
def setFileName(fname: str, DEBUG: bool = True) -> None:
    global filename
    filename = fname + "_" + filename
    if DEBUG:
        logging.basicConfig(format='%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s',
                        level=logging.WARNING, \
                        filename=filename, filemode='w')
    else:
        logging.basicConfig(format='%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s',
                        level=logging.WARNING, \
                        filename=filename, filemode='w')

# imports helper module that save the builtin module and module checking results.
from typing import List, Tuple, Dict

BUILTIN_IMPORTS: Tuple[List[str]] = ( # third_party
['croniter', 'certifi', 'markupsafe', 'pynamodb', 'termcolor', 'werkzeug'] + 
['atomicwrites', 'boto', 'singledispatch', 'ujson', 'mypy_extensions', 'attr', 'pymysql'] + 
['yaml', 'typing_extensions', 'characteristic', 'mock', 'requests', 'emoji', 'first', 'pytz'] + 
['google', 'protobuf', 'click', 'backports_abc', 'jinja2', 'backports', 'dateutil', 'simplejson'] +
['toml', 'Crypto', 'enum', 'pkg_resouces', 'typed_ast', 'jwt', 'six', 'itsdangerous', 'docutils'] +
# stdlib
['secrets', 'contextvars', 'dataclasses', 'zipfile', 'plistlib', 'bisect', 'doctest', 'sunau'] + 
['symtable', 'sndhdr', 'sched', 'tty', 'termios', 'quopri', 'pstats', 'py_compile', 'cmd', 'grp'] +
['dis', '_random', 'marshal', 'xml', 'pickletools', 'traceback', 'pwd', 'profile', 'mimetypes'] + 
['zlib', 'difflib', 'uu', 'pyclbr', 'token', 'poplib', 'syslog', '_heapq', 'linecache', 'numbers'] +
['datetime', 'array', 'pkgutil', 'lib2to3', 'bz2', 'pprint', 'code', 'telnetlib', 'argparse'] + 
['nis', 'ctypes', '__future__', 'ssl', 'disutils', '_codecs', 'pty', 'operator', 'rlcompleter'] + 
['xdrlib', 'site', 'crypt', 'filecmp', 'csv', 'zipimport', 'math', 'genericpath', 'sre_compile'] +
['binascii', 'stringprep', 'imghdr', 'shutil', 'fileinput', 'trace', 'calendar', 'netrc'] + 
['_bisect'] +
['pyexpat', 'socket', 'cmath', 'fractions', 'readline', 'errno', '_csv', 'sqlite3', 'mmap'] + 
['decimal', 'weakref', 'hmac', 'chunk', 'pdb', 'copy', 'threading', 'smtpd', 'locale', 'binhex'] + 
['cProfile', 'timeit', 'keyword', 'sysconfig', 'base64', 'tabnanny', 'codeop', 'asynchat'] + 
['ftplib'] + 
['select', 'unicodedata', 'opcode', 'webbrowser', 'cgi', 'wave', 'codecs', 'asyncore', 'optparse'] + ['warnings', '_weakrefset', 'tarfile', 'logging', '_weakref', 'wsgiref', 'imaplib', 'struct'] + 
['contextlib', 'time', 'pickle', 'colorsys', 'uuid', 'formatter', 'zipapp', 'urllib', 'fcntl'] + 
['re', 'types', 'configparser', 'enum', 'nturl2path', 'hashlib', '__importlib_modulespec'] + 
['smtplib', 'unittest', 'queue', '_thread', 'ast', 'inspect', 'textwrap', 'reprlib', 'gc'] +
['socketserver', '_stat', 'symbol', '_warnings', 'importlib', '_dummy_thread', '_operator'] + 
['fnmatch', '_subprocess', 'json', 'getopt', '_markupbase', 'getpass', 'shelve', 'runpy'] +
['posixpath'] +
['builtins', 'itertools', 'random', 'ipaddress', 'tracemalloc', 'tempfile', 'os', 'sys'] + 
['multiprocessing', 'lzma', 'email', 'resource', 'asyncio', 'tkinter', '_tracemalloc', 'heapq'] +
['sre_parse', 'shlex', 'platform', 'sre_constants', 'stat', '_threading_local', 'html'] +
['subprocess'] +
['string', '_curses', 'io', 'glob', '_compression', 'atexit', 'http', 'selectors', 'collections'] + 
['functools', 'nntplib', '_ast', 'gettext', 'msvcrt', 'concurrent', 'tokenize', 'curses'] + 
['compileall', 'imp', 'typing', 'statistics', '_json', 'pipes', 'macpath', 'ntpath'] + 
['_posixsubprocess'] + ['encodings', 'spwd', '_winapi', 'abc', '_imp', 'pathlib', 'posix'] +
['signal', 'gzip']
)

# When we import modules that is built-in, we set the flag True. And we can return it directly next time.
BUILTIN_FLAGS: Dict = {key:False for key in BUILTIN_IMPORTS}

# cache all the modules checked and store them.
imports_cache: Dict = {}

# if the module is checked or imported, set the flag true. And we can return it directly.
imports_flags: Dict = {}

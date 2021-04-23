
#import numpy

# test file for the coordinator package.

num = int(input())
var = None
if num > 10:
    var = 10
else:
    var = 'str'

back_var = var

var1 = back_var + 20

#foo()
'''
def bar(n):
    if n > 0:
        b = n + bar(n-1)
    else:
        return n
    return b

a = bar(10)
'''

class Foo():
    def __init__(self, name):
        self.name = name
        self.inst = Foo(name + "inst_")

foo = Foo('1_')
fdd = 1

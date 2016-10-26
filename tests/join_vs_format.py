import copy
import time
import os
import random

def random_text(n):
    return ''.join(chr(random.randint(32, 126)) for i in range(n))

x = [random_text(10) for i in range(500)]
y = [random_text(10) for i in range(500)]

def test_join(n, f):
    a = [None] * 1000
    for i in range(n):
        _test_join(a, f)

def _test_join(a, f):
    a = copy.copy(a)
    for i, (xx, yy) in enumerate(zip(x, y)):
        a[i*2] = '@' + xx
        a[(i*2)+1] = yy
    f.write("\n".join(a))
    f.write("\n")

def test_plus(n, f):
    for i in range(n):
        _test_plus(f)

def _test_plus(f):
    for xx, yy in zip(x, y):
        f.write('@' + xx + '\n' + yy + '\n')

def test_format(n, f):
    for i in range(n):
        _test_format(f)

def _test_format(f):
    for xx, yy in zip(x, y):
        f.write('{xx}\n{yy}\n'.format(xx=xx, yy=yy))

try:
    start = time.time()
    with open('temp', 'wt') as f:
        test_plus(1000, f)
    end = time.time()
    print(end-start)
finally:
    os.remove('temp')

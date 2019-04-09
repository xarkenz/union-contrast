from math import *
from re import split, sub
#split()
vars = []

def rmNonNumerics(string):
	result = ""
	for i in string:
		if i.isdigit(): result += i
	return result

def join(ilist: list, spacing: str=""):
    # Helper function to join a list together, separated by a string
    result = ilist[0]
    for i in range(len(ilist)): result += spacing + ilist[i]
    return result

def strip_start(string, amount: int):
    # Helper function to cut off the beginning of a string
    result = ""
    for i in range(len(str(string)) - amount): result = result + str(string)[i + amount]
    return result

def strip_end(string: str, amount: int):
    # Helper function to cut off the end of a string
    result = ""
    for i in range(len(str(string)) - amount):
            result = result + str(string)[i]
    return result

def root(number, root=2):
    return float(number ** (1 / root))

class Equation:
    def __init__(self, eq: str):
        self.eq = eq
    def left(self): return self.eq.split("=")[0]
    def right(self): return self.eq.split("=")[1]
    def solve(sym: str): pass

class Variable:
    def __init__(self, symbol: str, value: float=0.0):
        global vars
        self.sym = symbol
        self.val = value
        vars.append(self)
    def __del__(self): vars.remove(self)
    def equals(self, value: float): self.val = value
    def __int__(self): return int(self.val)
    def __str__(self): return str(self.val)
    def __float__(self): return float(self.val)
    def __add__(self, x): return self.val + x
    def __sub__(self, x): return self.val - x
    def __rsub__(self, x): return x - self.val
    def __mul__(self, x): return self.val * x
    def __truediv__(self, x): return self.val / x
    def __rtruediv__(self, x): return x / self.val
    def __floordiv__(self, x): return self.val // x
    def __rfloordiv__(self, x): return x // self.val
    def __pow__(self, x): return self.val ** x
    def __rpow__(self, x): return x ** self.val
    def __divmod__(self, x): return divmod(self.val, x)
    def __rdivmod__(self, x): return divmod(x, self.val)
    def __lshift__(self, x): return self.val << x
    def __rlshift__(self, x): return x << self.val
    def __rshift__(self, x): return self.val >> x
    def __rrshift__(self, x): return x >> self.val
    def __iadd__(self, x): self.val += x; return self.val
    def __isub__(self, x): self.val -= x; return self.val
    def __imul__(self, x): self.val *= x; return self.val
    def __itruediv__(self, x): self.val /= x; return self.val
    def __ifloordiv__(self, x): self.val //= x; return self.val

def printvars():
    res = ""
    for var in vars:
        res += var.sym + " = " + str(var) + "\n"
    print(res)

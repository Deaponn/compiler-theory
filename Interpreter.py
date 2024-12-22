import AST
import SymbolTable
from Memory import *
from Exceptions import  *
from visit import *
import sys

sys.setrecursionlimit(10000)

class Interpreter(object):
    @on('node')
    def visit(self, node):
        print("visit here")

    @when(AST.StartNode)
    def visit(self, node):
        print("start node")

    @when(AST.ArithmeticExpression)
    def visit(self, node):
        print("visit here2")
        r1 = node.left.accept(self)
        r2 = node.right.accept(self)
        # try sth smarter than:
        # if(node.op=='+') return r1+r2
        # elsif(node.op=='-') ...
        # but do not use python eval

    @when(AST.AssignStatement)
    def visit(self, node):
        pass

    # simplistic while loop interpretation
    @when(AST.WhileStatement)
    def visit(self, node):
        r = None
        while node.cond.accept(self):
            r = node.body.accept(self)
        return r

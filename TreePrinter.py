import AST

def addToClass(cls):
    def decorator(func):
        setattr(cls,func.__name__,func)
        return func
    return decorator

def printIndented(string, indent):
    if string is None: return
    print(" " * indent, string)

class TreePrinter:
    @addToClass(AST.Node)
    def printTree(self, indent=0):
        raise Exception("printTree not defined in class " + self.__class__.__name__)

    @addToClass(AST.ValueNode)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.StartNode)
    def printTree(self, indent=0):
        printIndented(self.block, indent)

    @addToClass(AST.Statement)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.AssignStatement)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ReturnValue)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.PrintValue)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.LoopControlNode)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.IndexList)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ValueList)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ArithmeticExpression)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ComparisonExpression)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.BoundExpression)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.IfStatement)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.WhileStatement)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ForStatement)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.ApplyTransposition)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.RangeNode)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.Variable)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.IndexedVariable)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.Outerlist)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.MatrixInitiator)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.Error)
    def printTree(self, indent=0):
        pass    
        # fill in the body


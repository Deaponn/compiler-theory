import AST

def addToClass(cls):
    def decorator(func):
        setattr(cls,func.__name__,func)
        return func
    return decorator

def printIndented(string, indent):
    if string is None: return
    print("| " * indent, string, sep="")

class TreePrinter:
    @addToClass(AST.Node)
    def printTree(self, indent=0):
        raise Exception("printTree not defined in class " + self.__class__.__name__)

    @addToClass(AST.ValueNode)
    def printTree(self, indent=0):
        printIndented(self.value, indent)

    @addToClass(AST.StartNode)
    def printTree(self, indent=0):
        self.block.printTree(indent)
        if self.nextStart is not None:
            self.nextStart.printTree(indent)

    @addToClass(AST.Statement)
    def printTree(self, indent=0, special_name=""):
        if special_name != "": printIndented(special_name, indent)
        self.statement.printTree(indent)
        if self.nextStatements is not None:
            self.nextStatements.printTree(indent)

    @addToClass(AST.BlockStatement)
    def printTree(self, indent=0, special_name=""):
        printIndented(special_name + " {" if special_name != "" else "{", indent)
        self.nextStatements.printTree(indent + 1)
        printIndented("}", indent)

    @addToClass(AST.AssignStatement)
    def printTree(self, indent=0):
        printIndented(f"{self.action}", indent)
        self.variableId.printTree(indent + 1)
        self.newValue.printTree(indent + 1)

    @addToClass(AST.ReturnValue)
    def printTree(self, indent=0):
        printIndented("RETURN", indent)
        self.value.printTree(indent + 1)

    @addToClass(AST.PrintValue)
    def printTree(self, indent=0):
        printIndented("PRINT", indent)
        self.value.printTree(indent + 1)

    @addToClass(AST.LoopControlNode)
    def printTree(self, indent=0):
        printIndented(self.action.upper(), indent)

    @addToClass(AST.ValueList)
    def printTree(self, indent=0):
        self.value.printTree(indent)
        if self.nextItem is not None:
            self.nextItem.printTree(indent)

    @addToClass(AST.Vector)
    def printTree(self, indent=0):
        printIndented("VECTOR", indent)
        self.value.printTree(indent + 1)
        if self.nextItem is not None:
            self.nextItem.printTree(indent)

    @addToClass(AST.ArithmeticExpression)
    def printTree(self, indent=0):
        printIndented(f"{self.action}", indent)
        self.leftExpr.printTree(indent + 1)
        self.rightExpr.printTree(indent + 1)

    @addToClass(AST.ComparisonExpression)
    def printTree(self, indent=0):
        printIndented(self.action, indent)
        self.leftExpr.printTree(indent + 1)
        self.rightExpr.printTree(indent + 1)

    @addToClass(AST.NegateExpression)
    def printTree(self, indent=0):
        printIndented("NEG", indent)
        self.expr.printTree(indent + 1)

    @addToClass(AST.IfStatement)
    def printTree(self, indent=0):
        printIndented("IF", indent)
        self.condition.printTree(indent + 1)
        self.action.printTree(indent + 1, "DO")
        if self.elseAction is not None:
            self.elseAction.printTree(indent + 1, "ELSE DO")

    @addToClass(AST.WhileStatement)
    def printTree(self, indent=0):
        printIndented("WHILE", indent)
        self.condition.printTree(indent + 1)
        self.action.printTree(indent + 1, "DO")

    @addToClass(AST.ForStatement)
    def printTree(self, indent=0):
        printIndented(f"FOR {self.loopVariable}", indent)
        self.valueRange.printTree(indent + 1)
        self.action.printTree(indent + 1, "DO")

    @addToClass(AST.TransposeExpression)
    def printTree(self, indent=0):
        printIndented("TRANSPOSE", indent)
        self.value.printTree(indent + 1)

    @addToClass(AST.RangeNode)
    def printTree(self, indent=0):
        printIndented("RANGE", indent)
        self.rangeStart.printTree(indent + 1)
        printIndented(":", indent + 1)
        self.rangeEnd.printTree(indent + 1)

    @addToClass(AST.Variable)
    def printTree(self, indent=0):
        printIndented(f"{self.name}", indent)

    @addToClass(AST.IndexedVariable)
    def printTree(self, indent=0):
        printIndented(f"{self.name} [", indent)
        self.indexes.printTree(indent + 1)
        printIndented("]", indent)

    @addToClass(AST.Matrix)
    def printTree(self, indent=0):
        printIndented("MATRIX", indent)
        self.values.printTree(indent + 1)
        if self.nextRow is not None:
            self.nextRow.printTree(indent + 1)

    @addToClass(AST.MatrixInitiator)
    def printTree(self, indent=0):
        printIndented(f"MATRIX {self.matrixType}", indent)
        self.size.printTree(indent + 1)

    @addToClass(AST.Error)
    def printTree(self, indent=0):
        pass    
        # fill in the body

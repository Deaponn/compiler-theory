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
        printIndented("START", indent)
        self.block.printTree(indent + 1)
        print(self.nextStart)
        if self.nextStart is not None:
            self.nextStart.printTree(indent)

    @addToClass(AST.Statement)
    def printTree(self, indent=0):
        printIndented("STATEMENT", indent)
        self.statement.printTree(indent + 1)
        if self.nextStatements is not None:
            self.nextStatements.printTree(indent)

    @addToClass(AST.AssignStatement)
    def printTree(self, indent=0):
        printIndented(f"ASSIGN {self.action}", indent)
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
        printIndented(f"LOOP_CTRL {self.action}", indent)

    @addToClass(AST.IndexList)
    def printTree(self, indent=0):
        printIndented(f"IDX {self.index}", indent)
        if self.nextItem is not None:
            self.nextItem.printTree(indent)

    @addToClass(AST.ValueList)
    def printTree(self, indent=0):
        printIndented(f"VAL LST {self.value}", indent)
        if self.nextItem is not None:
            self.nextItem.printTree(indent + 1)

    @addToClass(AST.ArithmeticExpression)
    def printTree(self, indent=0):
        printIndented(f"ARITH {self.action}", indent)
        self.leftExpr.printTree(indent + 1)
        self.rightExpr.printTree(indent + 1)

    @addToClass(AST.ComparisonExpression)
    def printTree(self, indent=0):
        printIndented(f"COMP {self.action}", indent)
        self.leftExpr.printTree(indent + 1)
        self.rightExpr.printTree(indent + 1)

    @addToClass(AST.BoundExpression)
    def printTree(self, indent=0):
        printIndented(f"BND {self.action}", indent)
        self.expr.printTree(indent + 1)

    @addToClass(AST.IfStatement)
    def printTree(self, indent=0):
        printIndented("IF", indent)
        self.condition.printTree(indent + 1)
        self.action.printTree(indent + 1)
        if self.elseAction is not None:
            self.elseAction.printTree(indent + 1)

    @addToClass(AST.WhileStatement)
    def printTree(self, indent=0):
        printIndented("WHL", indent)
        self.condition.printTree(indent + 1)
        self.action.printTree(indent + 1)

    @addToClass(AST.ForStatement)
    def printTree(self, indent=0):
        printIndented(f"FOR, ID={self.loopVariable}", indent)
        self.valueRange.printTree(indent + 1)
        self.action.printTree(indent + 1)

    @addToClass(AST.ApplyTransposition)
    def printTree(self, indent=0):
        printIndented("TRANS", indent)
        self.value.printTree(indent + 1)

    @addToClass(AST.RangeNode)
    def printTree(self, indent=0):
        printIndented("RANGE", indent)
        self.rangeStart.printTree(indent + 1)
        printIndented(":", indent)
        self.rangeEnd.printTree(indent + 1)

    @addToClass(AST.Variable)
    def printTree(self, indent=0):
        printIndented(f"VARIABLE {self.name}", indent)

    @addToClass(AST.IndexedVariable)
    def printTree(self, indent=0):
        printIndented(f"IDX VARIABLE {self.action} [ {self.indexes} ]", indent)

    @addToClass(AST.Outerlist)
    def printTree(self, indent=0):
        printIndented("OUTERLST", indent)
        self.values.printTree(indent + 1)
        if self.nextRow is not None:
            self.nextRow.printTree(indent)

    @addToClass(AST.MatrixInitiator)
    def printTree(self, indent=0):
        printIndented(f"MTRX {self.matrixType}", indent)
        self.size.printTree(indent + 1)

    @addToClass(AST.Error)
    def printTree(self, indent=0):
        pass    
        # fill in the body

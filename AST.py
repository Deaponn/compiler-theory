class Node(object):
    def __init__(self, lineno):
        self.lineno = lineno
    def visit(self, visitor):
        # try:
        func = getattr(visitor, f"visit_{self.__class__.__name__}")
        return func(self)
        # except AttributeError:
        #     print(f"Visitor {visitor.__class__.__name__} does not have visit_{self.__class__.__name__} implemented")

# used in productions from expr
class ValueNode(Node):
    def __init__(self, value, typeOfValue, lineno=-1):
        super().__init__(lineno)
        self.value = value
        self.typeOfValue = typeOfValue

# used in productions from start
class StartNode(Node):
    def __init__(self, block, nextStart=None, lineno=-1):
        super().__init__(lineno)
        self.block = block
        self.nextStart = nextStart

# used in productions from block and next_statements
class Statement(Node):
    def __init__(self, statement, nextStatements=None, lineno=-1):
        super().__init__(lineno)
        self.statement = statement
        self.nextStatements = nextStatements

# used in productions from block
class BlockStatement(Node):
    def __init__(self, nextStatements, lineno=-1):
        super().__init__(lineno)
        self.nextStatements = nextStatements

# used in productions from action_statement
class AssignStatement(Node):
    def __init__(self, variableId, action, newValue, lineno=-1):
        super().__init__(lineno)
        self.variableId = variableId
        self.action = action
        self.newValue = newValue

# used in productions from action_statement
class ReturnValue(Node):
    def __init__(self, value, lineno=-1):
        super().__init__(lineno)
        self.value = value

# used in productions from action_statement
class PrintValue(Node):
    def __init__(self, value, lineno=-1):
        super().__init__(lineno)
        self.value = value

# used in productions from action_statement
class LoopControlNode(Node):
    def __init__(self, action, lineno=-1):
        super().__init__(lineno)
        self.action = action

# used in production from values
class Vector(Node):
    def __init__(self, value, nextItem=None, lineno=-1):
        super().__init__(lineno)
        self.value = value
        self.nextItem = nextItem

class ValueList(Node):
    def __init__(self, value, nextItem=None, lineno=-1):
        super().__init__(lineno)
        self.value = value
        self.nextItem = nextItem

class IndexList(Node):
    def __init__(self, index, nextItem=None, lineno=-1):
        super().__init__(lineno)
        self.index = index
        self.nextItem = nextItem

# used in production from expr
class ArithmeticExpression(Node):
    def __init__(self, leftExpr, action, rightExpr, lineno=-1):
        super().__init__(lineno)
        self.leftExpr = leftExpr
        self.action = action
        self.rightExpr = rightExpr

# used in production from expr
class ComparisonExpression(Node):
    def __init__(self, leftExpr, action, rightExpr, lineno=-1):
        super().__init__(lineno)
        self.leftExpr = leftExpr
        self.action = action
        self.rightExpr = rightExpr

# used in production from expr
class NegateExpression(Node):
    def __init__(self, expr, lineno=-1):
        super().__init__(lineno)
        self.expr = expr

# used in production from flow_control_statement
class IfStatement(Node):
    def __init__(self, condition, action, elseAction=None, lineno=-1):
        super().__init__(lineno)
        self.condition = condition
        self.action = action
        self.elseAction = elseAction

# used in production from flow_control_statement
class WhileStatement(Node):
    def __init__(self, condition, action, lineno=-1):
        super().__init__(lineno)
        self.condition = condition
        self.action = action

# used in production from flow_control_statement
class ForStatement(Node):
    def __init__(self, loopVariable, valueRange, action, lineno=-1):
        super().__init__(lineno)
        self.loopVariable = loopVariable
        self.valueRange = valueRange
        self.action = action

# used in production from expr
class TransposeExpression(Node):
    def __init__(self, value, lineno=-1):
        super().__init__(lineno)
        self.value = value

# used in production from range
class RangeNode(Node):
    def __init__(self, rangeStart, rangeEnd, lineno=-1):
        super().__init__(lineno)
        self.rangeStart = rangeStart
        self.rangeEnd = rangeEnd

# used in productions from id_expr
class Variable(Node):
    def __init__(self, name, lineno=-1):
        super().__init__(lineno)
        self.name = name

# used in productions from expr
class IndexedVariable(Node):
    def __init__(self, name, indexes, lineno=-1):
        super().__init__(lineno)
        self.name = name
        self.indexes = indexes

# used in productions from expr
class MatrixInitiator(Node):
    def __init__(self, matrixType, size, lineno=-1):
        super().__init__(lineno)
        self.matrixType = matrixType
        self.size = size

class Error(Node):
    def __init__(self, lineno=-1):
        super().__init__(lineno)
        pass

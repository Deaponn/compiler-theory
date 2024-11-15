class Node(object):
    pass

# used in productions from expr
class ValueNode(Node):
    def __init__(self, value):
        self.value = value

# used in productions from start
class StartNode(Node):
    def __init__(self, block, nextStart=None):
        self.block = block
        self.nextStart = nextStart

# used in productions from block and next_statements
class Statement(Node):
    def __init__(self, statement, nextStatements=None):
        self.statement = statement
        self.nextStatements = nextStatements

# used in productions from block
class BlockStatement(Node):
    def __init__(self, nextStatements):
        self.nextStatements = nextStatements

# used in productions from action_statement
class AssignStatement(Node):
    def __init__(self, variableId, action, newValue):
        self.variableId = variableId
        self.action = action
        self.newValue = newValue

# used in productions from action_statement
class ReturnValue(Node):
    def __init__(self, value):
        self.value = value

# used in productions from action_statement
class PrintValue(Node):
    def __init__(self, value):
        self.value = value

# used in productions from action_statement
class LoopControlNode(Node):
    def __init__(self, action):
        self.action = action

# used in production from values
class ValueList(Node):
    def __init__(self, value, nextItem=None):
        self.value = value
        self.nextItem = nextItem

# used in production from expr
class ArithmeticExpression(Node):
    def __init__(self, leftExpr, action, rightExpr):
        self.leftExpr = leftExpr
        self.action = action
        self.rightExpr = rightExpr

# used in production from expr
class ComparisonExpression(Node):
    def __init__(self, leftExpr, action, rightExpr):
        self.leftExpr = leftExpr
        self.action = action
        self.rightExpr = rightExpr

# used in production from expr
class NegateExpression(Node):
    def __init__(self, expr):
        self.expr = expr

# used in production from flow_control_statement
class IfStatement(Node):
    def __init__(self, condition, action, elseAction=None):
        self.condition = condition
        self.action = action
        self.elseAction = elseAction

# used in production from flow_control_statement
class WhileStatement(Node):
    def __init__(self, condition, action):
        self.condition = condition
        self.action = action

# used in production from flow_control_statement
class ForStatement(Node):
    def __init__(self, loopVariable, valueRange, action):
        self.loopVariable = loopVariable
        self.valueRange = valueRange
        self.action = action

# used in production from expr
class TransposeExpression(Node):
    def __init__(self, value):
        self.value = value

# used in production from range
class RangeNode(Node):
    def __init__(self, rangeStart, rangeEnd):
        self.rangeStart = rangeStart
        self.rangeEnd = rangeEnd

# used in productions from id_expr
class Variable(Node):
    def __init__(self, name):
        self.name = name

# used in productions from expr
class IndexedVariable(Node):
    def __init__(self, name, indexes):
        self.name = name
        self.indexes = indexes

# used in productions from expr
class Outerlist(Node):
    def __init__(self, values, nextRow=None):
        self.values = values
        self.nextRow = nextRow

# used in productions from expr
class MatrixInitiator(Node):
    def __init__(self, matrixType, size):
        self.matrixType = matrixType
        self.size = size

class Error(Node):
    def __init__(self):
        pass

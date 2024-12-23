import AST
import SymbolTable
from Memory import *
from Exceptions import  *
from visit import *
import sys
from TypeChecker import TypeTable

sys.setrecursionlimit(10000)

class ValueInfo(object):
    def __init__(self, entityType, typeOfValue=None, shapeOfValue=None, content=None, name=None):
        # entity type is "undefined", "scalar", "vector", "matrix", "boolean" for variables
        # and "ok" or "err" for statements without distinct type like loops and assign statements
        self.entityType = entityType
        self.typeOfValue = typeOfValue
        self.shapeOfValue = shapeOfValue
        self.content = content
        self.name = name

class UndefinedValue(ValueInfo):
    def __init__(self):
        super().__init__("undefined")

class ScalarValue(ValueInfo):
    def __init__(self, typeOfValue, value, name=None):
        super().__init__("scalar", typeOfValue=typeOfValue, shapeOfValue=(), content=value, name=name)

    def columns(self): return 1

class VectorValue(ValueInfo):
    def __init__(self, typeOfValue, length, value, isProperVector=True, name=None):
        super().__init__("vector", typeOfValue=typeOfValue, shapeOfValue=(length,), content=value, name=name)
        self.isProperVector = isProperVector

    def rows(self): return 1

    def columns(self): return self.shapeOfValue[0]

    def valueAt(self, index):
        if self.content is None or index is None:
            return None
        return self.content[index]

class MatrixValue(ValueInfo):
    def __init__(self, typeOfValue, rows, columns, value, name=None):
        super().__init__("matrix", typeOfValue=typeOfValue, shapeOfValue=(rows, columns), content=value, name=name)

    def rows(self): return self.shapeOfValue[0]

    def columns(self): return self.shapeOfValue[1]

    def valueAt(self, row, column=None):
        if self.content is None or row is None:
            return None
        if column is None:
            return self.content[row]
        if row == ":":
            values = []
            for vector in self.content:
                values = [*values, vector[column]]
            return values
        return self.content[row][column]

class RangeValue(ValueInfo):
    def __init__(self, start=None, end=None):
        super().__init__("range")
        self.start = start
        self.end = end
        self.currentStep = self.start

    def getNext(self):
        if self.currentStep == self.end:
            return None
        output = self.currentStep
        self.currentStep += 1
        return output

class ErrorValue(ValueInfo):
    def __init__(self, reason):
        super().__init__("err", content=reason)
        print(reason)

class SuccessValue(ValueInfo):
    def __init__(self):
        super().__init__("ok")

class ContinueException(Exception):
    pass

class BreakException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value

class Interpreter(object):
    def __init__(self):
        self.typeTable = TypeTable()
        self.scopes = Memory()
        self.calculator = Calculator()

    @on('node')
    def visit(self, node):
        print("unknown node", node)

    @when(AST.ValueNode)
    def visit(self, node):
        return ScalarValue(node.typeOfValue, value=node.value)

    @when(AST.StartNode)
    def visit(self, node):
        try:
            output = self.visit(node.block)
            if node.nextStart is not None:
                newOutput = self.visit(node.nextStart)
                if isinstance(newOutput, ErrorValue):
                    output = newOutput
            return output
        except ReturnException as ret:
            print(f"Program returned with {ret.value}")

    @when(AST.Statement)
    def visit(self, node):
        output = self.visit(node.statement)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if isinstance(newOutput, ErrorValue):
                output = newOutput
        return output

    @when(AST.BlockStatement)
    def visit(self, node):
        self.scopes.pushScope()
        output = self.visit(node.nextStatements)
        self.scopes.popScope()
        return output

    @when(AST.AssignStatement)
    def visit(self, node):
        variableInfo = self.visit(node.variableId)
        if isinstance(variableInfo, ErrorValue):
            return variableInfo

        valueInfo = self.visit(node.newValue)
        if isinstance(valueInfo, ErrorValue) or isinstance(valueInfo, UndefinedValue):
            return valueInfo

        if node.action == "=":
            valueInfo.name = node.variableId.name
            self.scopes.put(node.variableId.name, valueInfo)
        else: # assign based on previous value
            if variableInfo.entityType != valueInfo.entityType:
                return ErrorValue(f"Line {node.lineno}: conflicting constructs {variableInfo.entityType} {node.action} {valueInfo.entityType}")
            if isinstance(variableInfo, UndefinedValue):
                return ErrorValue(f"Line {node.lineno}: operation-assignment to undefined variable {node.variableId.name}")

            newValue = self.calculator.calculate(node.action, [variableInfo, valueInfo])

            if newValue is None:
                return ErrorValue(f"Line {node.lineno}: incompatible types {variableInfo.typeOfValue} {node.action} {valueInfo.typeOfValue}")

            newValue.name = variableInfo.name
            self.scopes.put(variableInfo.name, newValue)
        return SuccessValue()

    @when(AST.ReturnValue)
    def visit(self, node):
        output = self.visit(node.value)
        if isinstance(output, ErrorValue) or isinstance(output, UndefinedValue):
            return output
        raise ReturnException(output.content)

    @when(AST.PrintValue)
    def visit(self, node):
        output = self.visit(node.value)
        if isinstance(output, ErrorValue) or isinstance(output, UndefinedValue):
            return output
        if isinstance(output, MatrixValue):
            print("[")
            for x in output.content:
                print(f"  {x},")
            print("]")
        else:
            print(output.content)
        return SuccessValue()

    @when(AST.LoopControlNode)
    def visit(self, node):
        if node.action == "continue":
            raise ContinueException
        raise BreakException

    @when(AST.Vector)
    def visit(self, node):
        valueInfo = self.visit(node.value)
        if isinstance(valueInfo, ErrorValue) or isinstance(valueInfo, UndefinedValue):
            return valueInfo

        if node.isMatrixHead:
            if isinstance(valueInfo, MatrixValue):
                return valueInfo
            else:
                return MatrixValue(valueInfo.typeOfValue, rows=1, columns=valueInfo.columns(), value=[valueInfo.content,])

        if node.nextItem is None:
            if isinstance(valueInfo, VectorValue):
                return VectorValue(valueInfo.typeOfValue, length=valueInfo.columns(), value=valueInfo.content)
            else:
                return VectorValue(valueInfo.typeOfValue, length=1, value=[valueInfo.content])

        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorValue) or isinstance(nextValueInfo, UndefinedValue):
            return nextValueInfo

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue or valueInfo.columns() != nextValueInfo.columns():
            return ErrorValue(f"Line {node.lineno}: inconsistent types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} or shapes {valueInfo.shapeOfValue} and {(nextValueInfo.shapeOfValue[-1],)}")

        nextValue = [valueInfo.content, *nextValueInfo.content] if not isinstance(nextValueInfo, VectorValue) else [valueInfo.content, nextValueInfo.content]

        return MatrixValue(valueInfo.typeOfValue, rows=nextValueInfo.rows() + 1, columns=nextValueInfo.columns(), value=nextValue)

    @when(AST.ValueList)
    def visit(self, node):
        valueInfo = self.visit(node.value)
        if isinstance(valueInfo, ErrorValue) or isinstance(valueInfo, UndefinedValue):
            return valueInfo

        if node.nextItem is None:
            return valueInfo
        
        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorValue) or isinstance(nextValueInfo, UndefinedValue):
            return nextValueInfo

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue:
            return ErrorValue(f"Line {node.lineno}: types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} are inconsistent")

        nextValue = [valueInfo.content, *nextValueInfo.content] if not isinstance(nextValueInfo, ScalarValue) else [valueInfo.content, nextValueInfo.content]

        return VectorValue(valueInfo.typeOfValue, length=nextValueInfo.columns() + 1, value=nextValue, isProperVector=False)

    @when(AST.IndexList)
    def visit(self, node):
        valueInfo = self.visit(node.index)
        if isinstance(valueInfo, ErrorValue) or isinstance(valueInfo, UndefinedValue):
            return valueInfo

        if node.nextItem is None:
            if not isinstance(valueInfo, ScalarValue) or valueInfo.typeOfValue != "integer":
                return ErrorValue(f"Line {node.lineno}: indexes are not integer or too many indexes")
            return valueInfo

        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorValue) or isinstance(nextValueInfo, UndefinedValue):
            return nextValueInfo

        if not isinstance(nextValueInfo, ScalarValue) or nextValueInfo.typeOfValue != "integer":
            return ErrorValue(f"Line {node.lineno}: indexes are not integer or too many indexes")

        return VectorValue("integer", length=2, value=[valueInfo.content, nextValueInfo.content])

    @when(AST.ArithmeticExpression)
    def visit(self, node):
        leftObject = self.visit(node.leftExpr)
        if isinstance(leftObject, ErrorValue) or isinstance(leftObject, UndefinedValue):
            return leftObject

        rightObject = self.visit(node.rightExpr)
        if isinstance(rightObject, ErrorValue) or isinstance(rightObject, UndefinedValue):
            return rightObject

        if leftObject.entityType != rightObject.entityType:
            return ErrorValue(f"Line {node.lineno}: cant do arithmetics between {leftObject.entityType} and {rightObject.entityType}")

        if (leftObject.entityType != "scalar") and "." not in node.action:
            return ErrorValue(f"Line {node.lineno}: cant do arithmetics using unary operators with {leftObject.entityType} and {rightObject.entityType}")

        return self.calculator.calculate(
            node.action,
            [leftObject, rightObject]
        )

    @when(AST.ComparisonExpression)
    def visit(self, node):
        leftObject = self.visit(node.leftExpr)
        if isinstance(leftObject, ErrorValue) or isinstance(leftObject, UndefinedValue):
            return leftObject

        rightObject = self.visit(node.rightExpr)
        if isinstance(rightObject, ErrorValue) or isinstance(rightObject, UndefinedValue):
            return rightObject

        return self.calculator.calculate(
            node.action,
            [leftObject, rightObject]
        )

    @when(AST.NegateExpression)
    def visit(self, node):
        output = self.visit(node.expr)
        if isinstance(output, ErrorValue) or isinstance(output, UndefinedValue):
            return output
        return self.calculator.calculate("-", [output])

    @when(AST.IfStatement)
    def visit(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            return ErrorValue(f"Line {node.lineno}: invalid condition")
        if conditionOutput.content:
            return self.visit(node.action)
        elif node.elseAction is not None:
            return self.visit(node.elseAction)
        return SuccessValue()

    @when(AST.WhileStatement)
    def visit(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            return ErrorValue(f"Line {node.lineno}: invalid condition")

        try:
            while conditionOutput.content:
                try:
                    actionOutput = self.visit(node.action)
                    if isinstance(actionOutput, ErrorValue):
                        return actionOutput
                    conditionOutput = self.visit(node.condition)
                    if conditionOutput.typeOfValue != "boolean":
                        return ErrorValue(f"Line {node.lineno}: invalid condition")
                except ContinueException:
                    pass
        except BreakException:
            pass

        return SuccessValue()

    @when(AST.ForStatement)
    def visit(self, node):
        rangeOutput = self.visit(node.valueRange)
        if isinstance(rangeOutput, ErrorValue):
            return rangeOutput

        loopVariableValue = rangeOutput.getNext()

        try:
            while loopVariableValue is not None:
                try:
                    self.scopes.put(node.loopVariable, ScalarValue("integer", value=loopVariableValue))

                    actionOutput = self.visit(node.action)
                    if isinstance(actionOutput, ErrorValue):
                        return actionOutput

                    loopVariableValue = rangeOutput.getNext()
                except ContinueException:
                    pass
        except BreakException:
            pass

        return SuccessValue()

    @when(AST.TransposeExpression)
    def visit(self, node):
        output = self.visit(node.value)
        if isinstance(output, ErrorValue) or isinstance(output, UndefinedValue):
            return output
        return self.calculator.calculate("'", [output])

    @when(AST.RangeNode)
    def visit(self, node):
        valueStart = self.visit(node.rangeStart)
        valueEnd = self.visit(node.rangeEnd)
        if not isinstance(valueStart, ScalarValue) or not isinstance(valueEnd, ScalarValue):
            return ErrorValue(f"Line {node.lineno}: range start or end are not scalars but {valueStart.entityType} and {valueEnd.entityType}")
        if valueStart.typeOfValue != "integer" or valueEnd.typeOfValue != "integer":
            return ErrorValue(f"Line {node.lineno}: invalid range types {valueStart.typeOfValue} : {valueEnd.typeOfValue}")
        return RangeValue(start=valueStart.content, end=valueEnd.content)

    @when(AST.Variable)
    def visit(self, node):
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return UndefinedValue()
        return variableInfo

    # TODO: support assigning to indexed vector/matrix ex. M[1, 2] = 3 now overrides the whole matrix variable
    @when(AST.IndexedVariable)
    def visit(self, node):
        indexes = self.visit(node.indexes)
        if isinstance(indexes, ErrorValue) or isinstance(indexes, UndefinedValue):
            return indexes

        variable = self.scopes.get(node.name)
        if variable is None:
            return ErrorValue(f"Line {node.lineno}: indexed variable is undefined")

        if indexes.content == ":" or indexes.content == (":", ":"):
            return variable

        if isinstance(indexes, ScalarValue):
            if indexes.content >= variable.columns():
                return ErrorValue(f"Line {node.lineno}: index {indexes.content} out of range for {variable.columns()}")
            if isinstance(variable, VectorValue):
                return ScalarValue(variable.typeOfValue, value=variable.valueAt(indexes.content))
            if isinstance(variable, MatrixValue):
                return VectorValue(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content))

        if isinstance(variable, VectorValue):
            return ErrorValue(f"Line {node.lineno}: too many indexes")

        if indexes.content[0] != ":" and indexes.content[0] > variable.rows():
            return ErrorValue(f"Line {node.lineno}: row index out of bounds {indexes.content[0]} for matrix of shape {variable.shapeOfValue}")
        if indexes.content[1] != ":" and indexes.content[1] > variable.columns():
            return ErrorValue(f"Line {node.lineno}: column index out of bounds {indexes.content[1]} for matrix of shape {variable.shapeOfValue}")

        if indexes.content[0] == ":":
            return VectorValue(variable.typeOfValue, length=variable.rows(), value=variable.valueAt(None, indexes.content[1]), name=node.name)
        if indexes.content[1] == ":":
            return VectorValue(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content[0]), name=node.name)

        return ScalarValue(variable.typeOfValue, value=variable.valueAt(*indexes.content), name=node.name)

    @when(AST.MatrixInitiator)
    def visit(self, node):
        matrixSize = self.visit(node.size)
        if isinstance(matrixSize, MatrixValue) or matrixSize.typeOfValue != "integer":
            return ErrorValue(f"Line {node.lineno}: matrix initiator dimensions are non-scalar or non-vector but {matrixSize.entityType}, or non-int {matrixSize.typeOfValue}")
        if isinstance(matrixSize, ScalarValue):
            return MatrixValue("integer", rows=matrixSize.content, columns=matrixSize.content, value=self.calculator.getMatrixValues(node.matrixType, matrixSize.content, matrixSize.content))
        if matrixSize.columns() > 2:
            return ErrorValue(f"Line {node.lineno}: too many values while initiating the matrix")
        return MatrixValue("integer", rows=matrixSize.content[0], columns=matrixSize.content[1], value=self.calculator.getMatrixValues(node.matrixType, matrixSize.content[0], matrixSize.content[1]))

def transpose(matrix):
    rows, cols = len(matrix), len(matrix[0])
    output = [[0] * rows for _ in range(cols)]

    for row in range(rows):
        for col in range(cols):
            output[col][row] = matrix[row][col]

    return output

def applyElementwiseOneArg(fun):
    def f(x):
        output = [None] * len(x)
        if not isinstance(x[0], list): # vector
            for idx in range(len(x)):
                output[idx] = fun(x[idx])
        else: # matrix
            for idx in range(len(x)):
                output[idx] = f(x[idx])
        return output
    return f

def applyElementwiseTwoArg(fun):
    def f(x, y):
        output = [None] * len(x)
        if not isinstance(x[0], list): # vector
            for idx in range(len(x)):
                output[idx] = fun(x[idx], y[idx])
        else: # matrix
            for idx in range(len(x)):
                output[idx] = f(x[idx], y[idx])
        return output
    return f

class Calculator():
    def __init__(self):
        self.typeTable = TypeTable()
        self.operationTable = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "neg": lambda x: -x,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y,
            ".+": applyElementwiseTwoArg(lambda x, y: x + y),
            ".-": applyElementwiseTwoArg(lambda x, y: x - y),
            ".neg": applyElementwiseOneArg(lambda x: -x),
            ".*": applyElementwiseTwoArg(lambda x, y: x * y),
            "./": applyElementwiseTwoArg(lambda x, y: x / y),
            "'": transpose,
            "<": lambda x, y: x < y,
            ">": lambda x, y: x > y,
            "<=": lambda x, y: x <= y,
            ">=": lambda x, y: x >= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
        }

    def calculate(self, operation, args):
        operation = operation.replace("=", "") if operation[0] in "+-*/" else operation
        if len(args) == 1:
            return self._calculateSingle(args[0], operation)
        return self._calculateDouble(args[0], operation, args[1])

    def _calculateSingle(self, objectOfInterest, operation):
        if operation == "-":
            if isinstance(objectOfInterest, ScalarValue):
                operation = "neg"
            else:
                operation = ".neg"
        if operation == "'" and not isinstance(objectOfInterest, MatrixValue):
            return objectOfInterest

        newValue = self.operationTable[operation](objectOfInterest.content)

        if isinstance(objectOfInterest, ScalarValue):
            return ScalarValue(objectOfInterest.typeOfValue, newValue)
        if isinstance(objectOfInterest, VectorValue):
            return VectorValue(objectOfInterest.typeOfValue, objectOfInterest.length, newValue)
        if isinstance(objectOfInterest, MatrixValue):
            return MatrixValue(objectOfInterest.typeOfValue, objectOfInterest.shapeOfValue[1], objectOfInterest.shapeOfValue[0], newValue)

    def _calculateDouble(self, leftObject, operation, rightObject):
        newType = self.typeTable.getType(leftObject.typeOfValue, operation, rightObject.typeOfValue)
        newValue = self.operationTable[operation](leftObject.content, rightObject.content)

        if isinstance(leftObject, ScalarValue):
            return ScalarValue(newType, newValue)
        if isinstance(leftObject, VectorValue):
            return VectorValue(newType, leftObject.columns(), newValue)
        return MatrixValue(newType, leftObject.rows(), leftObject.columns(), newValue)

    def getMatrixValues(self, valueType, rows, columns):
        value = 1 if valueType == "ones" else 0
        values = [[value] * columns for _ in range(rows)]
        if valueType == "eye":
            for idx in range(min(rows, columns)):
                values[idx][idx] = 1
        return values

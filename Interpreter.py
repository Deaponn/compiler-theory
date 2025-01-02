import AST
from Memory import Memory
from visit import *
import sys
from TypeChecker import TypeTable, TypeInfo, ScalarType, VectorType, MatrixType, RangeType, SuccessType as SuccessValue, UndefinedType as UndefinedValue

sys.setrecursionlimit(10000)

class ScalarValue(ScalarType):
    def __init__(self, typeOfValue, value, name=None, indexIterator=None):
        super().__init__(typeOfValue=typeOfValue, value=value, name=name)
        self.indexIterator = indexIterator

    def rows(self): return 1

    def valueAt(self, _ignore, __ignore):
        return self.content

    def setValue(self, _ignore, __ignore, value):
        self.content = value

class VectorValue(VectorType):
    def __init__(self, typeOfValue, length, value, isProperVector=True, name=None, indexIterator=None):
        super().__init__(typeOfValue=typeOfValue, length=length, value=value, isProperVector=isProperVector, name=name)
        self.indexIterator = indexIterator

    def valueAt(self, _ignore, index):
        return self.content[index]

    def setValue(self, _ignore, column, value):
        self.content[column] = value

class MatrixValue(MatrixType):
    def __init__(self, typeOfValue, rows, columns, value, name=None, indexIterator=None):
        super().__init__(typeOfValue=typeOfValue, rows=rows, columns=columns, value=value, name=name)
        self.indexIterator = indexIterator

    def valueAt(self, row, column):
        if column is None or column == ":":
            return self.content[row]
        if row == ":":
            values = []
            for vector in self.content:
                values = [*values, vector[column]]
            return values
        return self.content[row][column]

    def setValue(self, row, column, value):
        self.content[row][column] = value

class RangeValue(RangeType):
    def __init__(self, start=None, end=None):
        super().__init__(start, end)
        self.currentStep = self.start

    def getNext(self):
        if self.currentStep > self.end:
            return None
        output = self.currentStep
        self.currentStep += 1
        return output

class ContinueException(Exception):
    pass

class BreakException(Exception):
    pass

class RuntimeException(Exception):
    def __init__(self, value):
        super().__init__()
        print(value)

class ReturnException(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value

def createIndexGenerator(varRowStart, varRowEnd, varColStart, varColEnd):
    i = 0
    if varColStart == varColEnd: # alternative version when we need to iterate over a vector top-down
        for row in range(varRowStart, varRowEnd + 1):
            j = 0
            for col in range(varColStart, varColEnd + 1):
                yield row, col, j, i
                j += 1
            i += 1
    else:
        for row in range(varRowStart, varRowEnd + 1):
            j = 0
            for col in range(varColStart, varColEnd + 1):
                yield row, col, i, j
                j += 1
            i += 1

class Interpreter(object):
    def __init__(self):
        self.typeTable = TypeTable()
        self.scopes = Memory()
        self.calculator = Calculator()

    @on('node')
    def visit(self, node):
        pass

    @when(AST.ValueNode)
    def visit(self, node):
        return ScalarValue(node.typeOfValue, value=node.value)

    @when(AST.StartNode)
    def visit(self, node):
        try:
            self.visit(node.block)
            if node.nextStart is not None:
                self.visit(node.nextStart)
            return SuccessValue()
        except ReturnException as ret:
            print(f"Program returned with {ret.value}")
        except RuntimeException:
            print("Terminating further execution")
            sys.exit(0)

    @when(AST.Statement)
    def visit(self, node):
        self.visit(node.statement)
        if node.nextStatements is not None:
            self.visit(node.nextStatements)
        return SuccessValue()

    @when(AST.BlockStatement)
    def visit(self, node):
        self.scopes.pushScope()
        self.visit(node.nextStatements)
        self.scopes.popScope()
        return SuccessValue()

    @when(AST.AssignStatement)
    def visit(self, node):
        variableInfo = self.visit(node.variableId)
        valueInfo = self.visit(node.newValue)

        if node.action == "=":
            if variableInfo.isType(UndefinedValue) or not isinstance(node.variableId, AST.IndexedVariable):
                valueInfo.name = node.variableId.name
                self.scopes.put(node.variableId.name, valueInfo)
            else:
                variable = self.scopes.get(node.variableId.name)
                for varRowIdx, varColIdx, valRowIdx, valColIdx in variableInfo.indexIterator:
                    variable.setValue(varRowIdx, varColIdx, valueInfo.valueAt(valRowIdx, valColIdx))
        else: # assign based on previous value
            newValue = self.calculator.calculate(node.action, [variableInfo, valueInfo])

            if newValue is None:
                raise RuntimeException(f"Line {node.lineno}: incompatible types {variableInfo.typeOfValue} {node.action} {valueInfo.typeOfValue}")
                
            if variableInfo.indexIterator is not None:
                variable = self.scopes.get(node.variableId.name)
                if variable.typeOfValue != newValue.typeOfValue:
                    raise RuntimeException(f"Line {node.lineno}: new value of type {valueInfo.typeOfValue} is incorrect for type {variable.typeOfValue}")
                for varRowIdx, varColIdx, valRowIdx, valColIdx in variableInfo.indexIterator:
                    variable.setValue(varRowIdx, varColIdx, newValue.valueAt(valRowIdx, valColIdx))
            else:
                newValue.name = variableInfo.name
                self.scopes.put(variableInfo.name, newValue)
        return SuccessValue()

    @when(AST.ReturnValue)
    def visit(self, node):
        output = self.visit(node.value)
        raise ReturnException(output.content)

    @when(AST.PrintValue)
    def visit(self, node):
        output = self.visit(node.value)
        if output.isType(MatrixValue):
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
        if node.isMatrixHead:
            if valueInfo.isType(MatrixValue):
                return valueInfo
            else:
                return MatrixValue(valueInfo.typeOfValue, rows=1, columns=valueInfo.columns(), value=[valueInfo.content,])

        if node.nextItem is None:
            if valueInfo.isType(VectorValue):
                return VectorValue(valueInfo.typeOfValue, length=valueInfo.columns(), value=valueInfo.content)
            else:
                return VectorValue(valueInfo.typeOfValue, length=1, value=[valueInfo.content])

        nextValueInfo = self.visit(node.nextItem)
        nextValue = [valueInfo.content, *nextValueInfo.content] if not nextValueInfo.isType(VectorValue) else [valueInfo.content, nextValueInfo.content]
        return MatrixValue(valueInfo.typeOfValue, rows=nextValueInfo.rows() + 1, columns=nextValueInfo.columns(), value=nextValue)

    @when(AST.ValueList)
    def visit(self, node):
        valueInfo = self.visit(node.value)

        if node.nextItem is None:
            return valueInfo
        
        nextValueInfo = self.visit(node.nextItem)
        nextValue = [valueInfo.content, *nextValueInfo.content] if not nextValueInfo.isType(ScalarValue) else [valueInfo.content, nextValueInfo.content]
        return VectorValue(valueInfo.typeOfValue, length=nextValueInfo.columns() + 1, value=nextValue, isProperVector=False)

    @when(AST.IndexList)
    def visit(self, node):
        valueInfo = self.visit(node.index)
        if node.nextItem is None:
            if not valueInfo.isType(ScalarValue) or valueInfo.typeOfValue != "integer":
                raise RuntimeException(f"Line {node.lineno}: first index is not integer or too many indexes")
            return valueInfo

        nextValueInfo = self.visit(node.nextItem)
        if not nextValueInfo.isType(ScalarValue) or nextValueInfo.typeOfValue != "integer":
            raise RuntimeException(f"Line {node.lineno}: second index is not integer or too many indexes")

        return VectorValue("integer", length=2, value=[valueInfo.content, nextValueInfo.content])

    @when(AST.ArithmeticExpression)
    def visit(self, node):
        leftObject = self.visit(node.leftExpr)
        rightObject = self.visit(node.rightExpr)

        if not leftObject.correctShapes(rightObject):
            raise RuntimeException(f"Line {node.lineno}: incorrect shapes {leftObject.shapeOfValue} and {rightObject.shapeOfValue}")

        return self.calculator.calculate(
            node.action,
            [leftObject, rightObject]
        )

    @when(AST.ComparisonExpression)
    def visit(self, node):
        leftObject = self.visit(node.leftExpr)
        rightObject = self.visit(node.rightExpr)
        return self.calculator.calculate(
            node.action,
            [leftObject, rightObject]
        )

    @when(AST.NegateExpression)
    def visit(self, node):
        output = self.visit(node.expr)
        return self.calculator.calculate("-", [output])

    @when(AST.IfStatement)
    def visit(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.content:
            return self.visit(node.action)
        elif node.elseAction is not None:
            return self.visit(node.elseAction)
        return SuccessValue()

    @when(AST.WhileStatement)
    def visit(self, node):
        conditionOutput = self.visit(node.condition)
        try:
            while conditionOutput.content:
                try:
                    self.visit(node.action)
                    conditionOutput = self.visit(node.condition)
                except ContinueException:
                    pass
        except BreakException:
            pass

        return SuccessValue()

    @when(AST.ForStatement)
    def visit(self, node):
        rangeOutput = self.visit(node.valueRange)
        loopVariableValue = rangeOutput.getNext()

        try:
            while loopVariableValue is not None:
                try:
                    self.scopes.put(node.loopVariable, ScalarValue("integer", value=loopVariableValue))
                    self.visit(node.action)
                    loopVariableValue = rangeOutput.getNext()
                except ContinueException:
                    pass
        except BreakException:
            pass

        return SuccessValue()

    @when(AST.TransposeExpression)
    def visit(self, node):
        output = self.visit(node.value)
        return self.calculator.calculate("'", [output])

    @when(AST.RangeNode)
    def visit(self, node):
        valueStart = self.visit(node.rangeStart)
        valueEnd = self.visit(node.rangeEnd)
        if valueStart.typeOfValue != "integer" or valueEnd.typeOfValue != "integer":
            raise RuntimeException(f"Line {node.lineno}: invalid range types {valueStart.typeOfValue} : {valueEnd.typeOfValue}")
        return RangeValue(start=valueStart.content, end=valueEnd.content)

    @when(AST.Variable)
    def visit(self, node):
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return UndefinedValue()
        return variableInfo

    @when(AST.IndexedVariable)
    def visit(self, node):
        indexes = self.visit(node.indexes)
        variable = self.scopes.get(node.name)
        if indexes.content == ":" or indexes.content == (":", ":"):
            variable.indexIterator = createIndexGenerator(0, variable.rows() - 1, 0, variable.columns() - 1)
            return variable

        if indexes.isType(ScalarValue):
            if indexes.content >= variable.columns():
                raise RuntimeException(f"Line {node.lineno}: index {indexes.content} out of range for {variable.columns()}")
            if variable.isType(VectorValue):
                indexIterator = createIndexGenerator(0, 0, indexes.content, indexes.content)
                return ScalarValue(variable.typeOfValue, value=variable.valueAt(None, indexes.content), name=node.name, indexIterator=indexIterator)
            if variable.isType(MatrixValue):
                indexIterator = createIndexGenerator(indexes.content, indexes.content, 0, variable.columns() - 1)
                return VectorValue(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content, None), name=node.name, indexIterator=indexIterator)

        if indexes.content[0] != ":" and indexes.content[0] > variable.rows():
            raise RuntimeException(f"Line {node.lineno}: row index out of bounds {indexes.content[0]} for matrix of shape {variable.shapeOfValue}")
        if indexes.content[1] != ":" and indexes.content[1] > variable.columns():
            raise RuntimeException(f"Line {node.lineno}: column index out of bounds {indexes.content[1]} for matrix of shape {variable.shapeOfValue}")

        if indexes.content[0] == ":":
            indexIterator = createIndexGenerator(0, variable.rows() - 1, indexes.content[1], indexes.content[1])
            return VectorValue(variable.typeOfValue, length=variable.rows(), value=variable.valueAt(":", indexes.content[1]), name=node.name, indexIterator=indexIterator)
        if indexes.content[1] == ":":
            indexIterator = createIndexGenerator(indexes.content[0], indexes.content[0], 0, variable.columns() - 1)
            return VectorValue(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content[0], ":"), name=node.name, indexIterator=indexIterator)

        indexIterator = createIndexGenerator(indexes.content[0], indexes.content[0], indexes.content[1], indexes.content[1])
        return ScalarValue(variable.typeOfValue, value=variable.valueAt(*indexes.content), name=node.name, indexIterator=indexIterator)

    @when(AST.MatrixInitiator)
    def visit(self, node):
        matrixSize = self.visit(node.size)
        if matrixSize.isType(MatrixValue) or matrixSize.typeOfValue != "integer":
            raise RuntimeException(f"Line {node.lineno}: matrix initiator dimensions are non-scalar or non-vector but {matrixSize.entityType}, or non-int but {matrixSize.typeOfValue}")
        if matrixSize.isType(ScalarValue):
            return MatrixValue("integer", rows=matrixSize.content, columns=matrixSize.content, value=self.calculator.getMatrixValues(node.matrixType, matrixSize.content, matrixSize.content))
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
        if operation != operation.replace("=", "") and operation[0] in "+-*/":
            operation = operation.replace("=", "")
            if args[0].isType(VectorValue) or args[0].isType(MatrixValue):
                operation = "." + operation
        if len(args) == 1:
            return self._calculateSingle(args[0], operation)
        return self._calculateDouble(args[0], operation, args[1])

    def _calculateSingle(self, objectOfInterest, operation):
        if operation == "-":
            if objectOfInterest.isType(ScalarValue):
                operation = "neg"
            else:
                operation = ".neg"
        if operation == "'" and not objectOfInterest.isType(MatrixValue):
            return objectOfInterest

        newValue = self.operationTable[operation](objectOfInterest.content)

        if objectOfInterest.isType(ScalarValue):
            return ScalarValue(objectOfInterest.typeOfValue, newValue)
        if objectOfInterest.isType(VectorValue):
            return VectorValue(objectOfInterest.typeOfValue, objectOfInterest.length, newValue)
        if objectOfInterest.isType(MatrixValue):
            return MatrixValue(objectOfInterest.typeOfValue, len(newValue), len(newValue[0]), newValue)

    def _calculateDouble(self, leftObject, operation, rightObject):
        newType = self.typeTable.getType(leftObject.typeOfValue, operation, rightObject.typeOfValue)
        newValue = self.operationTable[operation](leftObject.content, rightObject.content)

        if leftObject.isType(ScalarValue):
            return ScalarValue(newType, newValue)
        if leftObject.isType(VectorValue):
            return VectorValue(newType, leftObject.columns(), newValue)
        return MatrixValue(newType, leftObject.rows(), leftObject.columns(), newValue)

    def getMatrixValues(self, valueType, rows, columns):
        value = 1 if valueType == "ones" else 0
        values = [[value] * columns for _ in range(rows)]
        if valueType == "eye":
            for idx in range(min(rows, columns)):
                values[idx][idx] = 1
        return values

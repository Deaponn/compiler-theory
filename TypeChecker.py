from SymbolTable import VariableSymbol, SymbolTable, TypeTable
from AST import Vector, IndexedVariable

class TypeInfo(object):
    def __init__(self, entityType, typeOfValue=None, shapeOfValue=None, content=None, name=None):
        # entity type is "undefined", "scalar", "vector", "matrix", "boolean" for variables
        # and "ok" or "err" for statements without distinct type like loops and assign statements
        self.entityType = entityType
        self.typeOfValue = typeOfValue
        self.shapeOfValue = shapeOfValue
        self.content = content
        self.name = name

    def isType(self, other): return isinstance(self, other)

class UndefinedType(TypeInfo):
    def __init__(self):
        super().__init__("undefined")

class ScalarType(TypeInfo):
    def __init__(self, typeOfValue, value, name=None):
        super().__init__("scalar", typeOfValue=typeOfValue, shapeOfValue=(), content=value, name=name)

    def columns(self): return 1

    def correctShapes(self, other): return True

class VectorType(TypeInfo):
    def __init__(self, typeOfValue, length, value, isProperVector=True, name=None):
        super().__init__("vector", typeOfValue=typeOfValue, shapeOfValue=(length,), content=value, name=name)
        self.isProperVector = isProperVector

    def rows(self): return 1

    def columns(self): return self.shapeOfValue[0]

    def valueAt(self, index):
        if self.content is None or index is None:
            return None
        return self.content[index]

    def correctShapes(self, other):
        if self.shapeOfValue[0] is None or other.shapeOfValue[0] is None:
            return True
        return self.shapeOfValue[0] == other.shapeOfValue[0]

class MatrixType(TypeInfo):
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
            values = ()
            for vector in self.content:
                values = (*values, vector[column])
            return values
        return self.content[row][column]

    def correctShapes(self, other):
        if self.shapeOfValue[0] is None or other.shapeOfValue[0] is None:
            if self.shapeOfValue[1] is None or other.shapeOfValue[1] is None:
                return True
            return self.shapeOfValue[1] == other.shapeOfValue[1]

        if self.shapeOfValue[1] is None or other.shapeOfValue[1] is None:
            return self.shapeOfValue[0] == other.shapeOfValue[0]

        return self.shapeOfValue[0] == other.shapeOfValue[0] and self.shapeOfValue[1] == other.shapeOfValue[1]

class RangeType(TypeInfo):
    def __init__(self, start=None, end=None):
        super().__init__("range")
        self.start = start
        self.end = end

class ErrorType(TypeInfo):
    def __init__(self, reason):
        super().__init__("err", content=reason)
        print(reason)

class SuccessType(TypeInfo):
    def __init__(self):
        super().__init__("ok")

class NodeVisitor(object):
    def visit(self, node):
        response = node.visit(self)
        return response

class TypeChecker(NodeVisitor):
    def __init__(self):
        self.scopes = SymbolTable()
        self.typeTable = TypeTable()

    def visit_ValueNode(self, node):
        return ScalarType(node.typeOfValue, value=node.value)

    def visit_StartNode(self, node):
        output = self.visit(node.block)
        if node.nextStart is not None:
            newOutput = self.visit(node.nextStart)
            if newOutput.isType(ErrorType):
                output = newOutput
        return output

    def visit_Statement(self, node):
        output = self.visit(node.statement)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if newOutput.isType(ErrorType):
                output = newOutput
        return output

    def visit_BlockStatement(self, node):
        self.scopes.pushScope()
        output = self.visit(node.nextStatements)
        self.scopes.popScope()
        return output

    def visit_AssignStatement(self, node):
        variableInfo = self.visit(node.variableId)
        if variableInfo.isType(ErrorType):
            return variableInfo

        valueInfo = self.visit(node.newValue)
        if valueInfo.isType(ErrorType):
            return valueInfo
        if valueInfo.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: right side of assignment is undefined")

        if node.action == "=":
            if isinstance(node.variableId, IndexedVariable):
                if variableInfo.typeOfValue != valueInfo.typeOfValue:
                    return ErrorType(f"Line {node.lineno}: trying to assign type {valueInfo.typeOfValue} to an index of variable of type {variableInfo.typeOfValue}")
                return SuccessType()
            self.scopes.put(node.variableId.name, valueInfo)
        else: # assign based on previous value
            if variableInfo.entityType != valueInfo.entityType:
                return ErrorType(f"Line {node.lineno}: conflicting constructs {variableInfo.entityType} {node.action} {valueInfo.entityType}")
            if variableInfo.isType(UndefinedType):
                return ErrorType(f"Line {node.lineno}: operation-assignment to undefined variable {node.variableId.name}")

            newType = self.typeTable.getType(variableInfo.typeOfValue, node.action, valueInfo.typeOfValue)
            
            if newType is None:
                return ErrorType(f"Line {node.lineno}: incompatible types {variableInfo.typeOfValue} {node.action} {valueInfo.typeOfValue}")

            if isinstance(node.variableId, IndexedVariable):
                return SuccessType()
            self.scopes.put(variableInfo.name, valueInfo)
        return SuccessType()

    def visit_ReturnValue(self, node):
        output = self.visit(node.value)
        if output.isType(ErrorType):
            return output
        if output.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: value that is to be returned is undefined")
        return SuccessType()

    def visit_PrintValue(self, node):
        output = self.visit(node.value)
        if output.isType(ErrorType):
            return output
        if output.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: value that is to be printed is undefined")
        return SuccessType()

    def visit_LoopControlNode(self, node):
        if not self.scopes.isInsideLoop():
            return ErrorType(f"Line {node.lineno}: break or continue in illegal place")
        return SuccessType()

    def visit_Vector(self, node):
        valueInfo = self.visit(node.value)
        if valueInfo.isType(ErrorType):
            return valueInfo
        if valueInfo.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: value of a vector is undefined")

        if node.isMatrixHead:
            if valueInfo.isType(MatrixType):
                return valueInfo
            else:
                return MatrixType(valueInfo.typeOfValue, rows=1, columns=valueInfo.columns(), value=(valueInfo.content,))

        if node.nextItem is None:
            if valueInfo.isType(VectorType):
                return VectorType(valueInfo.typeOfValue, length=valueInfo.columns(), value=valueInfo.content)
            else:
                return VectorType(valueInfo.typeOfValue, length=1, value=(valueInfo.content,))

        nextValueInfo = self.visit(node.nextItem)
        if nextValueInfo.isType(ErrorType):
            return nextValueInfo
        if nextValueInfo.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: value of a vector is undefined")

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue or valueInfo.columns() != nextValueInfo.columns():
            return ErrorType(f"Line {node.lineno}: inconsistent types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} or shapes {valueInfo.shapeOfValue} and {(nextValueInfo.shapeOfValue[-1],)}")

        nextValue = (valueInfo.content, *nextValueInfo.content) if not nextValueInfo.isType(VectorType) else (valueInfo.content, nextValueInfo.content)

        return MatrixType(valueInfo.typeOfValue, rows=nextValueInfo.rows() + 1, columns=nextValueInfo.columns(), value=nextValue)

    def visit_ValueList(self, node):
        valueInfo = self.visit(node.value)
        if valueInfo.isType(ErrorType) or valueInfo.isType(UndefinedType):
            return valueInfo

        if node.nextItem is None:
            return valueInfo
        
        nextValueInfo = self.visit(node.nextItem)
        if nextValueInfo.isType(ErrorType) or nextValueInfo.isType(UndefinedType):
            return nextValueInfo

        if not node.weak and valueInfo.typeOfValue != nextValueInfo.typeOfValue:
            return ErrorType(f"Line {node.lineno}: types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} are inconsistent")

        nextValue = (valueInfo.content, *nextValueInfo.content) if not nextValueInfo.isType(ScalarType) else (valueInfo.content, nextValueInfo.content)

        return VectorType(valueInfo.typeOfValue, length=nextValueInfo.columns() + 1, value=nextValue, isProperVector=False)

    def visit_IndexList(self, node):
        valueInfo = self.visit(node.index)
        if valueInfo.isType(ErrorType):
            return valueInfo
        if valueInfo.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: first index is undefined")

        if node.nextItem is None:
            if not valueInfo.isType(ScalarType) or valueInfo.typeOfValue != "integer":
                return ErrorType(f"Line {node.lineno}: indexes are not integer or too many indexes")
            return valueInfo

        nextValueInfo = self.visit(node.nextItem)
        if nextValueInfo.isType(ErrorType):
            return nextValueInfo
        if nextValueInfo.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: second index is undefined")

        if not nextValueInfo.isType(ScalarType) or nextValueInfo.typeOfValue != "integer":
            return ErrorType(f"Line {node.lineno}: indexes are not integer or too many indexes")

        return VectorType("integer", length=2, value=(valueInfo.content, nextValueInfo.content))

    def visit_ArithmeticExpression(self, node):
        leftObject = self.visit(node.leftExpr)
        if leftObject.isType(ErrorType):
            return leftObject
        if leftObject.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: left side of arithmetic expression is undefined")

        rightObject = self.visit(node.rightExpr)
        if rightObject.isType(ErrorType):
            return rightObject
        if rightObject.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: right side of arithmetic expression is undefined")

        if leftObject.entityType != rightObject.entityType:
            return ErrorType(f"Line {node.lineno}: cant do arithmetics between {leftObject.entityType} and {rightObject.entityType}")

        if (leftObject.entityType != "scalar") and "." not in node.action:
            return ErrorType(f"Line {node.lineno}: cant do arithmetics using unary operators with {leftObject.entityType} and {rightObject.entityType}")

        newType = self.typeTable.getType(
            leftObject.typeOfValue,
            node.action,
            rightObject.typeOfValue
        )

        if newType is None:
            return ErrorType(f"Line {node.lineno}: cant do arithmetic {leftObject.typeOfValue} {node.action} {rightObject.typeOfValue}")

        if "." in node.action:
            if not leftObject.correctShapes(rightObject):
                return ErrorType(f"Line {node.lineno}: incompatible shapes {leftObject.shapeOfValue} and {rightObject.shapeOfValue}")

        if leftObject.isType(ScalarType):
            return ScalarType(newType, value=None)
        if leftObject.isType(VectorType):
            return VectorType(newType, leftObject.columns(), value=None)
        return MatrixType(newType, leftObject.rows(), leftObject.columns(), value=None)

    def visit_ComparisonExpression(self, node):
        leftType = self.visit(node.leftExpr)
        if leftType.isType(ErrorType):
            return leftType
        if leftType.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: left value of comparison is undefined")

        rightType = self.visit(node.rightExpr)
        if rightType.isType(ErrorType):
            return rightType
        if rightType.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: right value of comparison is undefined")

        newType = self.typeTable.getType(
            leftType.typeOfValue,
            node.action,
            rightType.typeOfValue
        )

        if newType is None:
            return ErrorType(f"Line {node.lineno}: cant compare {leftType.typeOfValue} {node.action} {rightType.typeOfValue}")

        return ScalarType(newType, None)

    def visit_NegateExpression(self, node):
        output = self.visit(node.expr)
        if output.isType(ErrorType):
            return output
        if output.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: variable that is to be negated is undefined")
        if output.typeOfValue == "string":
            return ErrorType(f"Line {node.lineno}: cant negate string")
        return output

    def visit_IfStatement(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.isType(ErrorType):
            return conditionOutput
        if conditionOutput.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: one of variables used is undefined")
        if conditionOutput.typeOfValue != "boolean":
            return ErrorType(f"Line {node.lineno}: invalid condition, type is {conditionOutput.typeOfValue}")
        
        actionOutput = self.visit(node.action)
        if actionOutput.isType(ErrorType):
            return actionOutput

        if node.elseAction is not None:
            elseActionOutput = self.visit(node.elseAction)
            if elseActionOutput.isType(ErrorType):
                return elseActionOutput

        return SuccessType()

    def visit_WhileStatement(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            return ErrorType(f"Line {node.lineno}: invalid condition")

        self.scopes.modifyLoopCount(1)

        actionOutput = self.visit(node.action)
        if actionOutput.isType(ErrorType):
            return actionOutput

        self.scopes.modifyLoopCount(-1)
        
        return SuccessType()

    def visit_ForStatement(self, node):
        rangeOutput = self.visit(node.valueRange)
        self.scopes.put(node.loopVariable, ScalarType("integer", value=rangeOutput.start))

        self.scopes.modifyLoopCount(1)

        actionOutput = self.visit(node.action)
        if rangeOutput.isType(ErrorType):
            return rangeOutput
        if actionOutput.isType(ErrorType):
            return actionOutput

        self.scopes.modifyLoopCount(-1)

        return SuccessType()

    def visit_TransposeExpression(self, node):
        output = self.visit(node.value)
        if output.isType(ErrorType):
            return output
        if output.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: variable that is to be transposed is undefined")
        if output.isType(VectorType):
            return output
        if output.isType(MatrixType):
            return MatrixType(output.typeOfValue, rows=output.shapeOfValue[1], columns=output.shapeOfValue[0], value=None)
        return ErrorType(f"Line {node.lineno}: cant transpose {output.entityType}")

    def visit_RangeNode(self, node):
        typeStart = self.visit(node.rangeStart)
        typeEnd = self.visit(node.rangeEnd)
        if not typeStart.isType(ScalarType) or not typeEnd.isType(ScalarType):
            return ErrorType(f"Line {node.lineno}: range start or end are not scalars but {typeStart.entityType} and {typeEnd.entityType}")
        if typeStart.typeOfValue != "integer" or typeEnd.typeOfValue != "integer":
            return ErrorType(f"Line {node.lineno}: invalid range types {typeStart.typeOfValue} : {typeEnd.typeOfValue}")
        return RangeType(start=typeStart.content, end=typeEnd.content)

    def visit_Variable(self, node):
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return UndefinedType()
        return variableInfo

    def visit_IndexedVariable(self, node):
        indexes = self.visit(node.indexes)
        if indexes.isType(ErrorType):
            return indexes
        if indexes.isType(UndefinedType):
            return ErrorType(f"Line {node.lineno}: indexes of the variable are undefined")

        variable = self.scopes.get(node.name)
        if variable is None:
            return ErrorType(f"Line {node.lineno}: indexed variable is undefined")
        if variable.isType(ScalarType):
            return ErrorType(f"Line {node.lineno}: cant index a scalar variable")

        if indexes.content == ":" or indexes.content == (":", ":"):
            return variable

        if indexes.isType(ScalarType):
            if indexes.content is not None and indexes.content >= variable.columns():
                return ErrorType(f"Line {node.lineno}: index {indexes.content} out of range for {variable.columns()}")
            if variable.isType(VectorType):
                return ScalarType(variable.typeOfValue, value=variable.valueAt(indexes.content), name=node.name)
            if variable.isType(MatrixType):
                return VectorType(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content), name=node.name)

        if variable.isType(VectorType):
            return ErrorType(f"Line {node.lineno}: too many indexes")

        if indexes.content[0] is not None and indexes.content[0] != ":" and indexes.content[0] > variable.rows():
            return ErrorType(f"Line {node.lineno}: row index out of bounds {indexes.content[0]} for matrix of shape {variable.shapeOfValue}")
        if indexes.content[1] is not None and indexes.content[1] != ":" and indexes.content[1] > variable.columns():
            return ErrorType(f"Line {node.lineno}: column index out of bounds {indexes.content[1]} for matrix of shape {variable.shapeOfValue}")

        if indexes.content[0] == ":":
            return VectorType(variable.typeOfValue, length=variable.rows(), value=variable.valueAt(None, indexes.content[1]), name=node.name)
        if indexes.content[1] == ":":
            return VectorType(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content[0]), name=node.name)

        return ScalarType(variable.typeOfValue, value=variable.valueAt(*indexes.content), name=node.name)

    def visit_MatrixInitiator(self, node):
        matrixSize = self.visit(node.size)
        if matrixSize.isType(MatrixType) or matrixSize.typeOfValue != "integer":
            return ErrorType(f"Line {node.lineno}: matrix initiator dimensions are non-scalar or non-vector but {matrixSize.entityType}, or non-int {matrixSize.typeOfValue}")
        if matrixSize.isType(ScalarType):
            return MatrixType("integer", rows=matrixSize.content, columns=matrixSize.content, value=getMatrixValues(node.matrixType, matrixSize.content, matrixSize.content))
        if matrixSize.columns() > 2:
            return ErrorType(f"Line {node.lineno}: too many values while initiating the matrix")
        return MatrixType("integer", rows=matrixSize.content[0], columns=matrixSize.content[1], value=getMatrixValues(node.matrixType, matrixSize.content[0], matrixSize.content[1]))

def getMatrixValues(valueType, rows, columns):
    if rows is None or columns is None:
        return None
    value = 1 if valueType == "ones" else 0
    values = [[value] * columns for _ in range(rows)]
    if valueType == "eye":
        for idx in range(min(rows, columns)):
            values[idx][idx] = 1
    return values

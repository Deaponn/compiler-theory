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

class UndefinedType(TypeInfo):
    def __init__(self):
        super().__init__("undefined")

class ScalarType(TypeInfo):
    def __init__(self, typeOfValue, value, name=None):
        super().__init__("scalar", typeOfValue=typeOfValue, shapeOfValue=(), content=value, name=name)

    def columns(self): return 1

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
            if isinstance(newOutput, ErrorType):
                output = newOutput
        return output

    def visit_Statement(self, node):
        output = self.visit(node.statement)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if isinstance(newOutput, ErrorType):
                output = newOutput
        return output

    def visit_BlockStatement(self, node):
        self.scopes.pushScope()
        output = self.visit(node.nextStatements)
        self.scopes.popScope()
        return output

    def visit_AssignStatement(self, node):
        variableInfo = self.visit(node.variableId)
        if isinstance(variableInfo, ErrorType):
            return variableInfo

        valueInfo = self.visit(node.newValue)
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.action == "=":
            if isinstance(node.variableId, IndexedVariable):
                if variableInfo.typeOfValue != valueInfo.typeOfValue:
                    return ErrorType(f"Line {node.lineno}: trying to assign type {valueInfo.typeOfValue} to an index of variable of type {variableInfo.typeOfValue}")
                return SuccessType()
            self.scopes.put(node.variableId.name, valueInfo)
        else: # assign based on previous value
            if variableInfo.entityType != valueInfo.entityType:
                return ErrorType(f"Line {node.lineno}: conflicting constructs {variableInfo.entityType} {node.action} {valueInfo.entityType}")
            if isinstance(variableInfo, UndefinedType):
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
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        return SuccessType()

    def visit_PrintValue(self, node):
        output = self.visit(node.value)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        return SuccessType()

    def visit_LoopControlNode(self, node):
        if not self.scopes.isInsideLoop():
            return ErrorType(f"Line {node.lineno}: break or continue in illegal place")
        return SuccessType()

    def visit_Vector(self, node):
        valueInfo = self.visit(node.value)
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.isMatrixHead:
            if isinstance(valueInfo, MatrixType):
                return valueInfo
            else:
                return MatrixType(valueInfo.typeOfValue, rows=1, columns=valueInfo.columns(), value=(valueInfo.content,))

        if node.nextItem is None:
            if isinstance(valueInfo, VectorType):
                return VectorType(valueInfo.typeOfValue, length=valueInfo.columns(), value=valueInfo.content)
            else:
                return VectorType(valueInfo.typeOfValue, length=1, value=(valueInfo.content,))

        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            return nextValueInfo

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue or valueInfo.columns() != nextValueInfo.columns():
            return ErrorType(f"Line {node.lineno}: inconsistent types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} or shapes {valueInfo.shapeOfValue} and {(nextValueInfo.shapeOfValue[-1],)}")

        nextValue = (valueInfo.content, *nextValueInfo.content) if not isinstance(nextValueInfo, VectorType) else (valueInfo.content, nextValueInfo.content)

        return MatrixType(valueInfo.typeOfValue, rows=nextValueInfo.rows() + 1, columns=nextValueInfo.columns(), value=nextValue)

    def visit_ValueList(self, node):
        valueInfo = self.visit(node.value)
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.nextItem is None:
            return valueInfo
        
        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            return nextValueInfo

        if not node.weak and valueInfo.typeOfValue != nextValueInfo.typeOfValue:
            return ErrorType(f"Line {node.lineno}: types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} are inconsistent")

        nextValue = (valueInfo.content, *nextValueInfo.content) if not isinstance(nextValueInfo, ScalarType) else (valueInfo.content, nextValueInfo.content)

        return VectorType(valueInfo.typeOfValue, length=nextValueInfo.columns() + 1, value=nextValue, isProperVector=False)

    def visit_IndexList(self, node):
        valueInfo = self.visit(node.index)
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.nextItem is None:
            if not isinstance(valueInfo, ScalarType) or valueInfo.typeOfValue != "integer":
                return ErrorType(f"Line {node.lineno}: indexes are not integer or too many indexes")
            return valueInfo

        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            return nextValueInfo

        if not isinstance(nextValueInfo, ScalarType) or nextValueInfo.typeOfValue != "integer":
            return ErrorType(f"Line {node.lineno}: indexes are not integer or too many indexes")

        return VectorType("integer", length=2, value=(valueInfo.content, nextValueInfo.content))

    def visit_ArithmeticExpression(self, node):
        leftObject = self.visit(node.leftExpr)
        if isinstance(leftObject, ErrorType) or isinstance(leftObject, UndefinedType):
            return leftObject

        rightObject = self.visit(node.rightExpr)
        if isinstance(rightObject, ErrorType) or isinstance(rightObject, UndefinedType):
            return rightObject

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
            if leftObject.shapeOfValue != rightObject.shapeOfValue:
                return ErrorType(f"Line {node.lineno}: incompatible shapes {leftObject.shapeOfValue} and {rightObject.shapeOfValue}")

        if isinstance(leftObject, ScalarType):
            return ScalarType(newType, value=None)
        if isinstance(leftObject, VectorType):
            return VectorType(newType, leftObject.columns(), value=None)
        return MatrixType(newType, leftObject.rows(), leftObject.columns(), value=None)

    def visit_ComparisonExpression(self, node):
        leftType = self.visit(node.leftExpr)
        if isinstance(leftType, ErrorType) or isinstance(leftType, UndefinedType):
            return leftType

        rightType = self.visit(node.rightExpr)
        if isinstance(rightType, ErrorType) or isinstance(rightType, UndefinedType):
            return rightType

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
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        if output.typeOfValue == "string":
            return ErrorType(f"Line {node.lineno}: cant negate string")
        return output

    def visit_IfStatement(self, node):
        conditionOutput = self.visit(node.condition)
        if isinstance(conditionOutput, ErrorType):
            return conditionOutput
        if isinstance(conditionOutput, UndefinedType):
            return ErrorType(f"Line {node.lineno}: one of variables used is undefined")
        if conditionOutput.typeOfValue != "boolean":
            return ErrorType(f"Line {node.lineno}: invalid condition, type is {conditionOutput.typeOfValue}")
        
        actionOutput = self.visit(node.action)

        elseActionOutput = None
        if node.elseAction is not None:
            elseActionOutput = self.visit(node.elseAction)

        if isinstance(actionOutput, ErrorType):
            return actionOutput
        if isinstance(elseActionOutput, ErrorType):
            return elseActionOutput
        return SuccessType()

    def visit_WhileStatement(self, node):
        errorMessage = ""
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            errorMessage = f"Line {node.lineno}: invalid condition"

        self.scopes.modifyLoopCount(1)

        actionOutput = self.visit(node.action)
        if errorMessage != "":
            return ErrorType(errorMessage)
        if isinstance(actionOutput, ErrorType):
            return actionOutput

        self.scopes.modifyLoopCount(-1)
        
        return SuccessType()

    def visit_ForStatement(self, node):
        rangeOutput = self.visit(node.valueRange)
        self.scopes.put(node.loopVariable, ScalarType("integer", value=rangeOutput.start))

        self.scopes.modifyLoopCount(1)

        actionOutput = self.visit(node.action)
        if isinstance(rangeOutput, ErrorType):
            return rangeOutput
        if isinstance(actionOutput, ErrorType):
            return actionOutput

        self.scopes.modifyLoopCount(-1)

        return SuccessType()

    def visit_TransposeExpression(self, node):
        output = self.visit(node.value)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        if isinstance(output, VectorType):
            return output
        if isinstance(output, MatrixType):
            return MatrixType(output.typeOfValue, rows=output.shapeOfValue[1], columns=output.shapeOfValue[0], value=None)
        return ErrorType(f"Line {node.lineno}: cant transpose {output.entityType}")

    def visit_RangeNode(self, node):
        typeStart = self.visit(node.rangeStart)
        typeEnd = self.visit(node.rangeEnd)
        if not isinstance(typeStart, ScalarType) or not isinstance(typeEnd, ScalarType):
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
        if isinstance(indexes, ErrorType) or isinstance(indexes, UndefinedType):
            return indexes

        variable = self.scopes.get(node.name)
        if variable is None:
            return ErrorType(f"Line {node.lineno}: indexed variable is undefined")

        if indexes.content == ":" or indexes.content == (":", ":"):
            return variable

        if isinstance(indexes, ScalarType):
            if indexes.content is not None and indexes.content >= variable.columns():
                return ErrorType(f"Line {node.lineno}: index {indexes.content} out of range for {variable.columns()}")
            if isinstance(variable, VectorType):
                return ScalarType(variable.typeOfValue, value=variable.valueAt(indexes.content), name=node.name)
            if isinstance(variable, MatrixType):
                return VectorType(variable.typeOfValue, length=variable.columns(), value=variable.valueAt(indexes.content), name=node.name)

        if isinstance(variable, VectorType):
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
        if isinstance(matrixSize, MatrixType) or matrixSize.typeOfValue != "integer":
            return ErrorType(f"Line {node.lineno}: matrix initiator dimensions are non-scalar or non-vector but {matrixSize.entityType}, or non-int {matrixSize.typeOfValue}")
        if isinstance(matrixSize, ScalarType):
            return MatrixType("integer", rows=matrixSize.content, columns=matrixSize.content, value=getMatrixValues(node.matrixType, matrixSize.content, matrixSize.content))
        if matrixSize.columns() > 2:
            return ErrorType(f"Line {node.lineno}: too many values while initiating the matrix")
        return MatrixType("integer", rows=matrixSize.content[0], columns=matrixSize.content[1], value=getMatrixValues(node.matrixType, matrixSize.content[0], matrixSize.content[1]))

def getMatrixValues(valueType, rows, columns):
    value = 1 if valueType == "ones" else 0
    values = [[value] * columns for _ in range(rows)]
    if valueType == "eye":
        for idx in range(min(rows, columns)):
            values[idx][idx] = 1
    return values

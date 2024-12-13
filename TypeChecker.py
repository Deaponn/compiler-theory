from SymbolTable import VariableSymbol, SymbolTable, TypeTable
from AST import Vector

# TODO: handle vector return type when accessing ex. M[:, 3]
# TODO: fix indexing like M[:, :], in ValueList
# TODO: artihmetic expression for matrix, fix so it would work for vector too
# TODO: add initializing zeros, ones, and eye by passing value list by dimension ex ones(3, 4)
# TODO: add checking of matrix index out of bounds when idx is hardcoded
# TODO: make sure errors are handled after every visit
# TODO: move error printing to the very line that returns the ErrorType(reason)

logs = False

class TypeInfo(object):
    def __init__(self, entityType, typeOfValue=None, shapeOfValue=None, content=None):
        # entity type is "undefined", "scalar", "vector", "matrix", "boolean" for variables
        # and "ok" or "err" for statements without distinct type like loops and assign statements
        self.entityType = entityType
        self.typeOfValue = typeOfValue
        self.shapeOfValue = shapeOfValue
        self.content = content

    def cast(self, cast_to):
        if cast_to == self.typeOfValue: 
            return self
        return TypeInfo(self.entityType, cast_to, self.shapeOfValue)

class UndefinedType(TypeInfo):
    def __init__(self):
        super().__init__("undefined")

class ScalarType(TypeInfo):
    def __init__(self, typeOfValue, value=None):
        super().__init__("scalar", typeOfValue, (), value)

    def columns(self): return 1

class VectorType(TypeInfo):
    def __init__(self, typeOfValue, length, value=None, isProperVector=True):
        super().__init__("vector", typeOfValue, (length,), value)
        self.isProperVector = isProperVector

    def rows(self): return 1

    def columns(self): return self.shapeOfValue[0]

class MatrixType(TypeInfo):
    def __init__(self, typeOfValue, rows, columns, value=None):
        super().__init__("matrix", typeOfValue, (rows, columns), value)

    def rows(self): return self.shapeOfValue[0]

    def columns(self): return self.shapeOfValue[1]

class RangeType(TypeInfo):
    def __init__(self):
        super().__init__("range")

class ErrorType(TypeInfo):
    def __init__(self, reason):
        super().__init__("err", content=reason)

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
        return ScalarType(node.typeOfValue, node.value)

    def visit_StartNode(self, node):
        if logs: print("StartNode")
        output = self.visit(node.block)
        if node.nextStart is not None:
            newOutput = self.visit(node.nextStart)
            if isinstance(output, ErrorType):
                output = newOutput
        return output

    def visit_Statement(self, node):
        if logs: print("Statement")
        output = self.visit(node.statement)
        if logs: print("statement", output.entityType)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if logs: print("statement", newOutput.entityType)
            if isinstance(output, ErrorType):
                output = newOutput
        return output

    def visit_BlockStatement(self, node):
        if logs: print("BlockStatement")
        self.scopes.pushScope()
        output = self.visit(node.nextStatements)
        self.scopes.popScope()
        return output

    def visit_AssignStatement(self, node):
        if logs: print(f"AssignStatement {node.variableId} {node.action} {node.newValue}")
        variableInfo = self.visit(node.variableId)
        if isinstance(variableInfo, ErrorType):
            return variableInfo
        valueInfo = self.visit(node.newValue)
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo
        if node.action == "=":
            self.scopes.put(node.variableId.name, valueInfo)
        else: # assign based on previous value
            # variableType = self.scopes.get(variableInfo.name)
            if not isinstance(variableType, valueInfo):
                error = f"Line {node.lineno}: conflicting types {variableType.typeOfValue} {node.action} {node.valueInfo.typeOfValue}"
                print(error)
                return ErrorType(error)
            # if variableType is None:
            if isinstance(variableInfo, UndefinedType):
                error = f"Line {node.lineno}: operation-assignment to undefined variable {node.variableId.name}"
                print(error)
                return ErrorType(error)

            newType = self.typeTable.getType(variableType.typeOfValue, node.action, node.newValue.typeOfValue)
            self.scopes.put(variableInfo.name, valueInfo)
        return SuccessType()

    def visit_ReturnValue(self, node):
        if logs: print(f"ReturnValue {node.value}")
        output = self.visit(node.value)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        return SuccessType()

    def visit_PrintValue(self, node):
        if logs: print(f"PrintValue {node.value}")
        output = self.visit(node.value)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            return output
        return SuccessType()

    def visit_LoopControlNode(self, node):
        if logs: print(f"LoopControlNode {node.action}")
        if self.scopes.isOuterScope():
            error = f"Line {node.lineno}: break or continue in illegal place"
            print(error)
            return ErrorType(error)
        return SuccessType()

    def visit_Vector(self, node):
        valueInfo = self.visit(node.value)

        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.isMatrixHead:
            if isinstance(valueInfo, MatrixType):
                return valueInfo
            else:
                return MatrixType(valueInfo.typeOfValue, 1, valueInfo.columns(), (valueInfo.content))

        if node.nextItem is None:
            if isinstance(valueInfo, VectorType):
                return VectorType(valueInfo.typeOfValue, valueInfo.columns(), valueInfo.content)
            else:
                return VectorType(valueInfo.typeOfValue, 1, valueInfo.content)

        nextValueInfo = self.visit(node.nextItem)

        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            return nextValueInfo

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue or valueInfo.columns() != nextValueInfo.columns():
            error = f"Line {node.lineno}: inconsistent types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} or shapes {valueInfo.shapeOfValue} and {(nextValueInfo.shapeOfValue[-1],)}"
            print(error)
            return ErrorType(error)

        return MatrixType(valueInfo.typeOfValue, nextValueInfo.rows() + 1, nextValueInfo.columns())

    def visit_ValueList(self, node):
        valueInfo = self.visit(node.value)

        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            return valueInfo

        if node.nextItem is None:
            return valueInfo
        
        nextValueInfo = self.visit(node.nextItem)

        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            return nextValueInfo

        if valueInfo.typeOfValue != nextValueInfo.typeOfValue:
            error = f"Line {node.lineno}: types {valueInfo.typeOfValue} and {nextValueInfo.typeOfValue} are inconsistent"
            print(error)
            return ErrorType(error)

        return VectorType(valueInfo.typeOfValue, valueInfo.columns() + 1, isProperVector=False)

    def visit_IndexList(self, node):
        if logs: print("IndexList")

        thisIndex = ":"
        if node.index != ":": # if its not full row/column indicator
            output = self.visit(node.index)
            if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
                error = f"Line {node.lineno}: undefined variable"
                print(error)
                return output
            if not isinstance(output, ScalarType) or output.typeOfValue != "integer":
                error = f"Line {node.lineno}: indexes should be of type scalar integer, not {output.entityType} {output.typeOfValue}"
                print(error)
                return ErrorType(error)
            thisIndex = output.content

        if node.nextItem is None:
            return ScalarType("index-integer", thisIndex)
        
        output = self.visit(node.nextItem)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            error = f"Line {node.lineno}: undefined variable"
            print(error)
            return output
        if not isinstance(output, ScalarType) or output.typeOfValue != "integer":
            error = f"Line {node.lineno}: indexes should be of type scalar integer, not {output.entityType} {output.typeOfValue}"
            print(error)
            return ErrorType(error)

        return VectorType("index-integer", 2, (thisIndex, output.content))

    def visit_ArithmeticExpression(self, node):
        if logs: print(f"ArithmeticExpression {node.action}")

        leftObject = self.visit(node.leftExpr)
        if isinstance(leftObject, ErrorType) or isinstance(leftObject, UndefinedType):
            return leftObject

        rightObject = self.visit(node.rightExpr)
        if isinstance(rightObject, ErrorType) or isinstance(rightObject, UndefinedType):
            return rightObject

        if leftObject.entityType != rightObject.entityType:
            error = f"Line {node.lineno}: cant do arithmetics between {leftObject.entityType} and {rightObject.entityType}"
            print(error)
            return ErrorType(error)

        if (leftObject.entityType != "scalar" or rightObject.entityType != "scalar") and "." not in node.action:
            error = f"Line {node.lineno}: cant do arithmetics using unary operators with {leftObject.entityType} and {rightObject.entityType}"
            print(error)
            return ErrorType(error)

        newType = self.typeTable.getType(
            leftObject.typeOfValue,
            node.action,
            rightObject.typeOfValue
        )

        if newType is None:
            error = f"Line {node.lineno}: cant do arithmetic {leftObject.typeOfValue} {node.action} {rightObject.typeOfValue}"
            print(error)
            return ErrorType(error)

        if "." in node.action:
            if leftObject.shapeOfValue != rightObject.shapeOfValue:
                error = f"Line {node.lineno}: incompatible shapes {leftObject.shapeOfValue} and {rightObject.shapeOfValue}"
                print(error)
                return ErrorType(error)

        return leftObject.cast(newType)

    def visit_ComparisonExpression(self, node):
        if logs: print(f"ComparisonExpression {node.action}")

        leftType = self.visit(node.leftExpr)
        if isinstance(leftType, ErrorType) or isinstance(leftType, UndefinedType):
            print(f"Line {node.lineno}: undefined variable")
            return leftType

        rightType = self.visit(node.rightExpr)
        if isinstance(rightType, ErrorType) or isinstance(rightType, UndefinedType):
            print(f"Line {node.lineno}: undefined variable")
            return rightType

        newType = self.typeTable.getType(
            leftType.typeOfValue,
            node.action,
            rightType.typeOfValue
        )

        if newType is None:
            error = f"Line {node.lineno}: cant compare {leftType.typeOfValue} {node.action} {rightType.typeOfValue}"
            print(error)
            return ErrorType(error)

        return ScalarType(newType)

    def visit_NegateExpression(self, node):
        if logs: print("NegateExpression")
        output = self.visit(node.expr)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            print(f"Line {node.lineno}: an error occured negate expr")
            return output
        if output.typeOfValue == "string":
            error = f"Line {node.lineno}: cant negate string"
            print(error)
            return ErrorType(error)
        return output

    def visit_IfStatement(self, node):
        if logs: print("IfStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        if node.elseAction is not None:
            self.visit(node.elseAction)
        return SuccessType()

    def visit_WhileStatement(self, node):
        if logs: print("WhileStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        return SuccessType()

    def visit_ForStatement(self, node):
        if logs: print(f"ForStatement on bound {node.loopVariable}")
        self.scopes.put(node.loopVariable, ScalarType("integer"))
        rangeOutput = self.visit(node.valueRange)
        self.visit(node.action)
        return SuccessType()

    def visit_TransposeExpression(self, node):
        if logs: print("TransposeExpression")
        output = self.visit(node.value)
        if isinstance(output, ErrorType) or isinstance(output, UndefinedType):
            print(f"Line {node.lineno}: an error occured transpose expr")
            return output

        if isinstance(output, VectorType):
            return output
        if isinstance(output, MatrixType):
            return MatrixType(output.typeOfValue, output.shapeOfValue[1], output.shapeOfValue[0])

        error = f"Line {node.lineno}: cant transpose {output.entityType}"
        print(error)
        return ErrorType(error)

    def visit_RangeNode(self, node):
        if logs: print(f"RangeNode {node.rangeStart} : {node.rangeEnd}")
        typeStart = self.visit(node.rangeStart)
        typeEnd = self.visit(node.rangeEnd)
        if not isinstance(typeStart, ScalarType) or not isinstance(typeEnd, ScalarType):
            error = f"Line {node.lineno}: range start or end are not scalars but {typeStart.entityType} and {typeEnd.entityType}"
            print(error)
            return ErrorType(error)
        if typeStart.typeOfValue != "integer" or typeEnd.typeOfValue != "integer":
            error = f"Line {node.lineno}: invalid range {typeStart} : {typeEnd}"
            print(error)
            return ErrorType(error)
        return RangeType()

    def visit_Variable(self, node):
        if logs: print(f"Variable {node.name}")
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return UndefinedType()
        return variableInfo

    # when indexing n-dimensional matrix with k-long indexes, the output is (n-k)-dimensional
    def visit_IndexedVariable(self, node):
        if logs: print(f"IndexedVariable {node.name} [ {node.indexes} ]")
        indexes = self.visit(node.indexes)

        if isinstance(indexes, ErrorType) or isinstance(indexes, UndefinedType):
            print(f"Line {node.lineno}: an error occured transpose expr")
            return indexes

        if not isinstance(indexes, ScalarType) and not isinstance(indexes, VectorType):
            error = f"Line {node.lineno}: illegal indexes {indexes.entityType}"
            print(error)
            return ErrorType(error)

        numIndexes, typeOfValue = len(indexes.shapeOfValue) + 1, indexes.typeOfValue
        valueType = self.scopes.get(node.name)

        # print(numIndexes, indexes.shapeOfValue)

        if valueType is None:
            error = f"Line {node.lineno}: undefined variable {node.name}"
            print(error)
            return ErrorType(error)

        dimensionality = len(valueType.shapeOfValue) - numIndexes

        if dimensionality < 0:
            error = f"Line {node.lineno}: too many indexes {indexes.content} for {dimensionality}d variable"
            print(error)
            return ErrorType(error)

        if dimensionality == 1:
            return VectorType(valueType.typeOfValue, valueType.shapeOfValue[0])
        return ScalarType(valueType.typeOfValue)

    def visit_MatrixInitiator(self, node):
        if logs: print(f"MatrixInitiator type {node.matrixType}")
        matrixSize = self.visit(node.size)
        if not isinstance(matrixSize, ScalarType) or matrixSize.typeOfValue != "integer":
            error = f"Line {node.lineno}: matrix initiator dimensions are non-scalar {matrixSize.entityType} or non-int {matrixSize.typeOfValue}"
            print(error)
            return ErrorType(error)
        return MatrixType("integer", matrixSize.content, matrixSize.content)

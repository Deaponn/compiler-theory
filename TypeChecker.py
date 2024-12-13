from SymbolTable import VariableSymbol, SymbolTable, TypeTable
from AST import Vector

# TODO: add initializing zeros, ones, and eye by passing value list by dimension ex ones(3, 4)
# TODO: add checking of matrix index out of bounds when idx is hardcoded
# TODO: make sure errors are handled after every visit
# TODO: modify ErrorType so it prints the message in __init__

class TypeInfo(object):
    def __init__(self, entityType, typeOfValue=None, shapeOfValue=None, content=None, name=None):
        # entity type is "undefined", "scalar", "vector", "matrix", "boolean" for variables
        # and "ok" or "err" for statements without distinct type like loops and assign statements
        self.entityType = entityType
        self.typeOfValue = typeOfValue
        self.shapeOfValue = shapeOfValue
        self.content = content
        self.name = name

    def cast(self, cast_to):
        if cast_to == self.typeOfValue: 
            return self
        return TypeInfo(self.entityType, cast_to, self.shapeOfValue)

class UndefinedType(TypeInfo):
    def __init__(self):
        super().__init__("undefined")

class ScalarType(TypeInfo):
    def __init__(self, typeOfValue, value=None, name=None):
        super().__init__("scalar", typeOfValue=typeOfValue, shapeOfValue=(), content=value, name=name)

    def columns(self): return 1

class VectorType(TypeInfo):
    def __init__(self, typeOfValue, length, value=None, isProperVector=True, name=None):
        super().__init__("vector", typeOfValue=typeOfValue, shapeOfValue=(length,), content=value, name=name)
        self.isProperVector = isProperVector

    def rows(self): return 1

    def columns(self): return self.shapeOfValue[0]

    def valueAt(self, index):
        if self.content is None or index is None:
            return None
        return self.content[index]

class MatrixType(TypeInfo):
    def __init__(self, typeOfValue, rows, columns, value=None, name=None):
        super().__init__("matrix", typeOfValue=typeOfValue, shapeOfValue=(rows, columns), content=value, name=name)
        # print("what i got by index [:, 1]", self.valueAt(":", 1))

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
        output = self.visit(node.block)
        if node.nextStart is not None:
            newOutput = self.visit(node.nextStart)
            if isinstance(output, ErrorType):
                output = newOutput
        return output

    def visit_Statement(self, node):
        output = self.visit(node.statement)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if isinstance(output, ErrorType):
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
            self.scopes.put(node.variableId.name, valueInfo)
        else: # assign based on previous value
            if variableInfo.entityType != valueInfo.entityType:
                error = f"Line {node.lineno}: conflicting constructs {variableInfo.entityType} {node.action} {valueInfo.entityType}"
                print(error)
                return ErrorType(error)
            if isinstance(variableInfo, UndefinedType):
                error = f"Line {node.lineno}: operation-assignment to undefined variable {node.variableId.name}"
                print(error)
                return ErrorType(error)

            newType = self.typeTable.getType(variableInfo.typeOfValue, node.action, node.newValue.typeOfValue)
            
            if newType is None:
                error = f"Line {node.lineno}: incompatible types {variableInfo.typeOfValue} {node.action} {valueInfo.typeOfValue}"
                print(error)
                return ErrorType(error)

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

        return VectorType(valueInfo.typeOfValue, nextValueInfo.columns() + 1, isProperVector=False)

    def visit_IndexList(self, node):
        valueInfo = self.visit(node.index)
        
        if isinstance(valueInfo, ErrorType) or isinstance(valueInfo, UndefinedType):
            error = f"Line {node.lineno}: undefined variable"
            print(error)
            return valueInfo

        if node.nextItem is None:
            if not isinstance(valueInfo, ScalarType) or valueInfo.typeOfValue != "integer":
                error = f"Line {node.lineno}: indexes are not integer or too many indexes"
                print(error)
                return ErrorType(error)
            return valueInfo

        nextValueInfo = self.visit(node.nextItem)
        if isinstance(nextValueInfo, ErrorType) or isinstance(nextValueInfo, UndefinedType):
            error = f"Line {node.lineno}: undefined variable"
            print(error)
            return nextValueInfo

        if not isinstance(nextValueInfo, ScalarType) or nextValueInfo.typeOfValue != "integer":
            error = f"Line {node.lineno}: indexes are not integer or too many indexes"
            print(error)
            return ErrorType(error)

        return VectorType("integer", 2, (valueInfo.content, nextValueInfo.content))

    def visit_ArithmeticExpression(self, node):
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

        if (leftObject.entityType != "scalar") and "." not in node.action:
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
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        if node.elseAction is not None:
            self.visit(node.elseAction)
        return SuccessType()

    def visit_WhileStatement(self, node):
        conditionOutput = self.visit(node.condition)
        if conditionOutput.typeOfValue != "boolean":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        return SuccessType()

    def visit_ForStatement(self, node):
        self.scopes.put(node.loopVariable, ScalarType("integer"))
        rangeOutput = self.visit(node.valueRange)
        self.visit(node.action)
        return SuccessType()

    def visit_TransposeExpression(self, node):
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
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return UndefinedType()
        return variableInfo

    # when indexing n-dimensional matrix with k-long indexes, the output is (n-k)-dimensional
    def visit_IndexedVariable(self, node):
        indexes = self.visit(node.indexes)

        if isinstance(indexes, ErrorType) or isinstance(indexes, UndefinedType):
            return indexes

        variable = self.scopes.get(node.name)
        if variable is None:
            error = f"Line {node.lineno}: indexed variable is undefined"
            print(error)
            return ErrorType(error)

        if indexes.content == ":" or indexes.content == (":", ":"):
            return variable

        if isinstance(indexes, ScalarType):
            if isinstance(variable, VectorType):
                return ScalarType(variable.typeOfValue, variable.valueAt(indexes.content), name=node.name)
            if isinstance(variable, MatrixType):
                return VectorType(variable.typeOfValue, variable.columns(), variable.valueAt(indexes.content), name=node.name)

        if isinstance(variable, VectorType):
            error = f"Line {node.lineno}: too many indexes"
            print(error)
            ErrorType(error)

        if indexes.content[0] == ":":
            return VectorType(variable.typeOfValue, variable.rows(), variable.valueAt(*indexes.content), name=node.name)
        if indexes.content[1] == ":":
            return VectorType(variable.typeOfValue, variable.columns(), variable.valueAt(indexes.content[0]), name=node.name)

        return ScalarType(variable.typeOfValue, variable.valueAt(*indexes.content), name=node.name)

    def visit_MatrixInitiator(self, node):
        matrixSize = self.visit(node.size)
        if not isinstance(matrixSize, ScalarType) or matrixSize.typeOfValue != "integer":
            error = f"Line {node.lineno}: matrix initiator dimensions are non-scalar {matrixSize.entityType} or non-int {matrixSize.typeOfValue}"
            print(error)
            return ErrorType(error)
        return MatrixType("integer", matrixSize.content, matrixSize.content)

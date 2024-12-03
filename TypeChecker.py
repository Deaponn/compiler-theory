from SymbolTable import VariableSymbol, SymbolTable, TypeTable

# TODO: handle vector return type when accessing ex. M[:, 3]
# TODO: fix indexing like M[:, :], in ValueList
# TODO: artihmetic expression for matrix, fix so it would work for vector too
# TODO: add initializing zeros, ones, and eye by passing value list by dimension ex ones(3, 4)
# TODO: add checking of matrix index out of bounds when idx is hardcoded

logs = False

class TypeInfo(object):
    def __init__(self, typeOfValue, classOfValue, shapeOfValue=-1):
        self.typeOfValue = typeOfValue
        self.classOfValue = classOfValue
        self.shapeOfValue = shapeOfValue

class GenericType(object):
    def __init__(self, objectType):
        self.objectType = objectType

class Undefined(GenericType):
    def __init__(self, name):
        super().__init__("undefined")
        self.name = name

class ValueType(GenericType):
    def __init__(self, typeOfValue, name=None, value=None):
        super().__init__("scalar")
        self.typeOfValue = typeOfValue
        self.name = name
        self.value = value

class VectorType(GenericType):
    def __init__(self, typeOfValue, length, name=None):
        super().__init__("vector")
        self.typeOfValue = typeOfValue
        self.length = length
        self.name = name

class MatrixType(GenericType):
    def __init__(self, typeOfValue, rows, columns, name=None):
        super().__init__("matrix")
        self.typeOfValue = typeOfValue
        self.rows = rows
        self.columns = columns
        self.name = name

class ErrorType(GenericType):
    def __init__(self):
        super().__init__("err")

class SuccessType(GenericType):
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
        return ValueType(node.typeOfValue, value=node.value)

    def visit_StartNode(self, node):
        if logs: print("StartNode")
        output = self.visit(node.block)
        if node.nextStart is not None:
            newOutput = self.visit(node.nextStart)
            if output.objectType != "err":
                output = newOutput
        return output

    def visit_Statement(self, node):
        if logs: print("Statement")
        output = self.visit(node.statement)
        if logs: print("statement", output.objectType)
        if node.nextStatements is not None:
            newOutput = self.visit(node.nextStatements)
            if logs: print("statement", newOutput.objectType)
            if output.objectType != "err":
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
        variable = self.visit(node.variableId)
        if variable.objectType == "err":
            return variable
        value = self.visit(node.newValue)
        if value.objectType == "err" or value.objectType == "undefined":
            return value
        if node.action == "=":
            if value.objectType == "scalar":
                self.scopes.put(variable.name, TypeInfo(value.typeOfValue, value.objectType))
            elif value.objectType == "vector":
                self.scopes.put(variable.name, TypeInfo(value.typeOfValue, value.objectType, value.length))
            else:
                self.scopes.put(variable.name, TypeInfo(value.typeOfValue, value.objectType, (value.rows, value.columns)))
        else: # assign based on previous value
            leftType = self.scopes.get(variable.name)
            if leftType is None:
                print(f"Line {node.lineno}: operation-assignment to unexisting variable {node.variableId}")
                return ErrorType()
            newType = self.typeTable.getType(leftType.typeOfValue, node.action, node.newValue.typeOfValue)
            if newType is None:
                print(f"Line {node.lineno}: conflicting types {leftType.typeOfValue} {node.action} {node.newValue.typeOfValue}")
                return ErrorType()
                
            self.scopes.put(variable.name, TypeInfo(newType, leftType.classOfValue))

            if leftType.classOfValue == "scalar":
                self.scopes.put(variable.name, TypeInfo(newType, leftType.classOfValue))
            elif leftType.classOfValue == "vector":
                self.scopes.put(variable.name, TypeInfo(newType, leftType.classOfValue, leftType.length))
            else:
                self.scopes.put(variable.name, TypeInfo(newType, leftType.classOfValue, (leftType.rows, leftType.columns)))
        return SuccessType()

    def visit_ReturnValue(self, node):
        if logs: print(f"ReturnValue {node.value}")
        output = self.visit(node.value)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: error in return")
            return output
        return SuccessType()

    def visit_PrintValue(self, node):
        if logs: print(f"PrintValue {node.value}")
        output = self.visit(node.value)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: error in print")
            return output
        return SuccessType()

    def visit_LoopControlNode(self, node):
        if logs: print(f"LoopControlNode {node.action}")
        if self.scopes.isOuterScope():
            print(f"Line {node.lineno}: break or continue in illegal place")
            return ErrorType()
        return SuccessType()

    def visit_Vector(self, node):
        if logs: print("Vector")
        output = self.visit(node.value)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: error in vector value")
            return output
        typeOfValue = output.typeOfValue
        length = output.length

        if node.nextItem is None:
            return VectorType(typeOfValue, output.length)

        output = self.visit(node.nextItem)
        if typeOfValue != output.typeOfValue or length != output.length:
            print(f"Line {node.lineno}: inconsistent vector types or length")
            return ErrorType()
        return VectorType(typeOfValue, output.length)

    def visit_ValueList(self, node):
        if logs: print("ValueList")
        typeOfValue = ":"
        if node.value != ":": # if its not full row/column indicator
            output = self.visit(node.value)
            if output.objectType == "err" or output.objectType == "undefined":
                print(f"Line {node.lineno}: undefined variable")
                return output
            typeOfValue = output.typeOfValue

        if node.nextItem is None:
            return VectorType(typeOfValue, 1)
        
        output = self.visit(node.nextItem)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: undefined variable")
            return output
        if output.typeOfValue != typeOfValue:
            typeOfValue = "inconsistent"
        return VectorType(typeOfValue, output.length + 1)

    def visit_ArithmeticExpression(self, node):
        if logs: print(f"ArithmeticExpression {node.action}")
        leftObject = self.visit(node.leftExpr)
        if leftObject.objectType == "err" or leftObject.objectType == "undefined":
            return leftObject

        rightObject = self.visit(node.rightExpr)
        if rightObject.objectType == "err" or rightObject.objectType == "undefined":
            return rightObject

        if leftObject.objectType != rightObject.objectType:
            print(f"Line {node.lineno}: cant do arithmetics between {leftObject.objectType} and {rightObject.objectType}")
            return ErrorType()

        if leftObject.objectType == "matrix" and "." not in node.action:
            print(f"Line {node.lineno}: cant do arithmetics using unary operators with {leftObject.objectType} and {rightObject.objectType}")
            return ErrorType()

        newType = self.typeTable.getType(
            leftObject.typeOfValue,
            node.action,
            rightObject.typeOfValue
        )

        if newType is None:
            print(f"Line {node.lineno}: cant do arithmetic {leftObject.typeOfValue} {node.action} {rightObject.typeOfValue}")
            return ErrorType()

        if "." in node.action:
            if leftObject.objectType != "matrix" or rightObject.objectType != "matrix":
                print(f"Line {node.lineno}: matrix arithmetic onto non-matrix")
                return ErrorType()
            elif leftObject.rows != rightObject.rows or leftObject.columns != rightObject.columns:
                print(f"Line {node.lineno}: incompatible shapes")
                return ErrorType()

        return ValueType(newType)

    def visit_ComparisonExpression(self, node):
        if logs: print(f"ComparisonExpression {node.action}")
        leftType = self.visit(node.leftExpr)
        if leftType.objectType == "err" or leftType.objectType == "undefined":
            print(f"Line {node.lineno}: undefined variable")
            return leftType

        rightType = self.visit(node.rightExpr)
        if rightType.objectType == "err" or leftType.objectType == "undefined":
            print(f"Line {node.lineno}: undefined variable")
            return rightType

        newType = self.typeTable.getType(
            leftType.typeOfValue,
            node.action,
            rightType.typeOfValue
        )

        if newType is None:
            print(f"Line {node.lineno}: cant compare {leftType.typeOfValue} {node.action} {rightType.typeOfValue}")
            return ErrorType()
        return SuccessType()

    def visit_NegateExpression(self, node):
        if logs: print("NegateExpression")
        output = self.visit(node.expr)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: an error occured negate expr")
            return output
        if output.typeOfValue == "string":
            return ErrorType()
        return output

    def visit_IfStatement(self, node):
        if logs: print("IfStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.objectType == "err" or conditionOutput.objectType == "undefined":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        if node.elseAction is not None:
            self.visit(node.elseAction)
        return SuccessType()

    def visit_WhileStatement(self, node):
        if logs: print("WhileStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.objectType == "err" or conditionOutput.objectType == "undefined":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        return SuccessType()

    def visit_ForStatement(self, node):
        if logs: print(f"ForStatement on bound {node.loopVariable}")
        self.scopes.put(node.loopVariable, TypeInfo("integer", "scalar"))
        rangeOutput = self.visit(node.valueRange)
        if rangeOutput.objectType == "err" or rangeOutput.objectType == "undefined":
            print(f"Line {node.lineno}: invalid loop range")
        self.visit(node.action)
        return SuccessType()

    def visit_TransposeExpression(self, node):
        if logs: print("TransposeExpression")
        output = self.visit(node.value)
        if output.objectType == "err" or output.objectType == "undefined":
            print(f"Line {node.lineno}: an error occured transpose expr")
            return output
        if output.objectType == "scalar":
            print(f"Line {node.lineno}: cant transpose scalars")
            return ErrorType()
        return MatrixType("float", output.columns, output.rows)

    def visit_RangeNode(self, node):
        if logs: print(f"RangeNode {node.rangeStart} : {node.rangeEnd}")
        typeStart = self.visit(node.rangeStart)
        typeEnd = self.visit(node.rangeEnd)
        if typeStart.objectType != "scalar" or typeEnd.objectType != "scalar":
            print(f"Line {node.lineno}: range start and end are not scalars")
            return ErrorType()
        if typeStart.typeOfValue != "integer" or typeEnd.typeOfValue != "integer":
            print(f"Line {node.lineno}: invalid range {typeStart} : {typeEnd}")
            return ErrorType()
        return SuccessType()

    def visit_Variable(self, node):
        if logs: print(f"Variable {node.name}")
        variableInfo = self.scopes.get(node.name)
        if variableInfo is None:
            return Undefined(node.name)
        if variableInfo.classOfValue == "scalar":
            return ValueType(variableInfo.typeOfValue, node.name)
        elif variableInfo.classOfValue == "vector":
            return VectorType(variableInfo.typeOfValue, variableInfo.shapeOfValue, node.name)
        else:
            return MatrixType(variableInfo.typeOfValue, variableInfo.shapeOfValue[0], variableInfo.shapeOfValue[1], node.name)

    def visit_IndexedVariable(self, node):
        if logs: print(f"IndexedVariable {node.name} [ {node.indexes} ]")
        indexes = self.visit(node.indexes)
        if indexes.objectType != "vector":
            print(f"Line {node.lineno}: illegal indexes")
            return ErrorType()
        numIndexes, typeOfValue = indexes.length, indexes.typeOfValue
        wholeType = self.scopes.get(node.name)
        if wholeType is None:
            return ErrorType()
        return ValueType(wholeType.typeOfValue, node.name)

    def visit_Matrix(self, node):
        if logs: print("Matrix")
        rows = 1
        vectorOutput = self.visit(node.values)
        if vectorOutput.objectType != "vector":
            print(f"Line {node.lineno}: error occured visit matrix")
            return vectorOutput
        columns, matrixType = vectorOutput.length, vectorOutput.typeOfValue
        if node.nextRow is not None:
            nextVectorOutput = self.visit(node.nextRow)
            if nextVectorOutput.objectType != "vector":
                print(f"Line {node.lineno}: error occured visit matrix")
                return nextVectorOutput

            nextColumns, nextMatrixType = nextVectorOutput.length, nextVectorOutput.typeOfValue

            if nextColumns != columns or matrixType != nextMatrixType:
                print(f"Line {node.lineno}: invalid matrix initialization, dimensions {columns} and {nextColumns} or types {matrixType} and {nextMatrixType}")
                return ErrorType()

            rows += 1
        return MatrixType(matrixType, rows, columns)

    def visit_MatrixInitiator(self, node):
        if logs: print(f"MatrixInitiator type {node.matrixType}")
        matrixSize = self.visit(node.size)
        if matrixSize.typeOfValue != "integer":
            print(f"Line {node.lineno}: non-int matrix initiator dimensions {matrixSize.typeOfValue}")
            return ErrorType()
        return MatrixType("integer", matrixSize.value, matrixSize.value)

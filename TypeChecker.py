from SymbolTable import VariableSymbol, SymbolTable, TypeTable

# TODO: handle vector return type when accessing ex. M[:, 3]
# TODO: implement matrix size analysis
# TODO: fix indexing like M[:, :], in ValueList

logs = False

class Undefined(object):
    def __init__(self, name):
        self.objectType = "undefined"
        self.name = name

class ValueType(object):
    def __init__(self, typeOfValue, name=None):
        self.objectType = "scalar"
        self.typeOfValue = typeOfValue
        self.name = name

class VectorType(object):
    def __init__(self, typeOfValue, length):
        self.objectType = "vector"
        self.typeOfValue = typeOfValue
        self.length = length

class MatrixType(object):
    def __init__(self, typeOfValue, rows, columns):
        self.objectType = "matrix"
        self.typeOfValue = typeOfValue
        self.rows = rows
        self.columns = columns

class ErrorType(object):
    def __init__(self):
        self.objectType = "err"

class SuccessType(object):
    def __init__(self, where=None):
        self.objectType = "ok"
        self.where = where

class NodeVisitor(object):
    def visit(self, node):
        response = node.visit(self)
        return response

class TypeChecker(NodeVisitor):
    def __init__(self):
        self.scopes = SymbolTable()
        self.typeTable = TypeTable()

    def visit_ValueNode(self, node):
        return ValueType(node.typeOfValue)

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
        if value.objectType == "err":
            return value
        if node.action == "=":
            self.scopes.put(variable.name, value.typeOfValue)
        else: # assign based on previous value
            leftType = self.scopes.get(variable.name)
            if leftType is None:
                print(f"Line {node.lineno}: operation-assignment to unexisting variable {node.variableId}")
                return ErrorType()
            newType = self.typeTable.getType(leftType, node.action, node.newValue)
            if newType is None:
                print(f"Line {node.lineno}: conflicting types {leftType} {node.action} {node.newValue}")
                return ErrorType()
            self.scopes.put(variable.name, newType)
        return SuccessType("assign")

    def visit_ReturnValue(self, node):
        if logs: print(f"ReturnValue {node.value}")
        output = self.visit(node.value)
        if output.objectType == "err":
            print(f"Line {node.lineno}: error in return")
            return output
        return SuccessType("return")

    def visit_PrintValue(self, node):
        if logs: print(f"PrintValue {node.value}")
        output = self.visit(node.value)
        if output.objectType == "err":
            print(f"Line {node.lineno}: error in print")
            return output
        return SuccessType("print")

    def visit_LoopControlNode(self, node):
        if logs: print(f"LoopControlNode {node.action}")
        if self.scopes.isOuterScope():
            print(f"Line {node.lineno}: break or continue in illegal place")
            return ErrorType()
        return SuccessType("loop control")

    def visit_Vector(self, node):
        if logs: print("Vector")
        output = self.visit(node.value)
        if output.objectType == "err":
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
        leftType = self.visit(node.leftExpr)
        if leftType.objectType == "err":
            return leftType

        rightType = self.visit(node.rightExpr)
        if rightType.objectType == "err":
            return leftType

        newType = self.typeTable.getType(
            leftType.typeOfValue,
            node.action,
            rightType.typeOfValue
        )

        if newType is None:
            print(f"Line {node.lineno}: cant do arithmetic {leftType.typeOfValue} {node.action} {rightType.typeOfValue}")
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
        return SuccessType("comparison")

    def visit_NegateExpression(self, node):
        if logs: print("NegateExpression")
        output = self.visit(node.expr)
        if output.objectType == "err":
            print(f"Line {node.lineno}: an error occured negate expr")
            return output
        if output.typeOfValue == "string":
            return ErrorType()
        return SuccessType("negation")

    def visit_IfStatement(self, node):
        if logs: print("IfStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.objectType == "err":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        if node.elseAction is not None:
            self.visit(node.elseAction)
        return SuccessType("if stmt")

    def visit_WhileStatement(self, node):
        if logs: print("WhileStatement")
        conditionOutput = self.visit(node.condition)
        if conditionOutput.objectType == "err":
            print(f"Line {node.lineno}: invalid condition")
        self.visit(node.action)
        return SuccessType("while stmt")

    def visit_ForStatement(self, node):
        if logs: print(f"ForStatement on bound {node.loopVariable}")
        rangeOutput = self.visit(node.valueRange)
        if rangeOutput.objectType == "err":
            print(f"Line {node.lineno}: invalid loop range")
        self.visit(node.action)
        return SuccessType("for stmt")

    def visit_TransposeExpression(self, node):
        if logs: print("TransposeExpression")
        output = self.visit(node.value)
        if output.objectType == "err":
            print(f"Line {node.lineno}: an error occured transpose expr")
            return output
        if output.objectType != "matrix" or output.typeOfValue == "string":
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
        return SuccessType("range node")

    def visit_Variable(self, node):
        if logs: print(f"Variable {node.name}")
        if self.scopes.get(node.name) is None:
            return Undefined(node.name)
        return ValueType(self.scopes.get(node.name), node.name)

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
        return ValueType(wholeType.replace(" matrix", "").replace(" vector", ""), node.name)

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
        if logs: print(matrixSize)
        if matrixSize.typeOfValue != "integer":
            print(f"Line {node.lineno}: non-int matrix initiator dimensions {matrixSize.typeOfValue}")
            return ErrorType()
        return MatrixType("integer", 0, 0)

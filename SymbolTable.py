class VariableSymbol(object):
    def __init__(self, name, typeOfVariable):
        self.name = name
        self.typeOfVariable = typeOfVariable

class SymbolTable(object):
    def __init__(self): # parent scope and symbol table name
        self.scopes = [{}]

    def put(self, name, typeOfValue): # put variable symbol or fundef under <name> entry
        self.scopes[-1][name] = typeOfValue

    def get(self, name): # get variable symbol or fundef from <name> entry
        for scope_idx in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[scope_idx]:
                return self.scopes[scope_idx][name]
        return None

    def pushScope(self):
        self.scopes.append({})

    def popScope(self):
        self.scopes.pop()

    def isOuterScope(self):
        return len(self.scopes) == 1

class TypeTable(object):
    def __init__(self):
        self.typeTable = {}

        self.typeTable["+"] = {}
        self.typeTable["+"]["integer"] = {}
        self.typeTable["+"]["integer"]["integer"] = "integer"
        self.typeTable["+"]["integer"]["float"] = "float"
        self.typeTable["+"]["float"] = {}
        self.typeTable["+"]["float"]["integer"] = "float"
        self.typeTable["+"]["float"]["float"] = "float"
        self.typeTable["+"]["string"] = {}
        self.typeTable["+"]["string"]["string"] = "string"

        self.typeTable["-"] = {}
        self.typeTable["-"]["integer"] = {}
        self.typeTable["-"]["integer"]["integer"] = "integer"
        self.typeTable["-"]["integer"]["float"] = "float"
        self.typeTable["-"]["float"] = {}
        self.typeTable["-"]["float"]["integer"] = "float"
        self.typeTable["-"]["float"]["float"] = "float"

        self.typeTable["*"] = {}
        self.typeTable["*"]["integer"] = {}
        self.typeTable["*"]["integer"]["integer"] = "integer"
        self.typeTable["*"]["integer"]["float"] = "float"
        self.typeTable["*"]["float"] = {}
        self.typeTable["*"]["float"]["integer"] = "float"
        self.typeTable["*"]["float"]["float"] = "float"

        self.typeTable["/"] = {}
        self.typeTable["/"]["integer"] = {}
        self.typeTable["/"]["integer"]["integer"] = "float"
        self.typeTable["/"]["integer"]["float"] = "float"
        self.typeTable["/"]["float"] = {}
        self.typeTable["/"]["float"]["integer"] = "float"
        self.typeTable["/"]["float"]["float"] = "float"

        self.typeTable["MPLUS"] = {}
        self.typeTable["MPLUS"]["integer matrix"] = {}
        self.typeTable["MPLUS"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable["MPLUS"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable["MPLUS"]["float matrix"] = {}
        self.typeTable["MPLUS"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable["MPLUS"]["float matrix"]["float matrix"] = "float matrix"
        self.typeTable["MPLUS"]["string matrix"] = {}
        self.typeTable["MPLUS"]["string matrix"]["string matrix"] = "string matrix"

        self.typeTable["MMINUS"] = {}
        self.typeTable["MMINUS"]["integer matrix"] = {}
        self.typeTable["MMINUS"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable["MMINUS"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable["MMINUS"]["float matrix"] = {}
        self.typeTable["MMINUS"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable["MMINUS"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable["MTIMES"] = {}
        self.typeTable["MTIMES"]["integer matrix"] = {}
        self.typeTable["MTIMES"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable["MTIMES"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable["MTIMES"]["float matrix"] = {}
        self.typeTable["MTIMES"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable["MTIMES"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable["MDIVIDE"] = {}
        self.typeTable["MDIVIDE"]["integer matrix"] = {}
        self.typeTable["MDIVIDE"]["integer matrix"]["integer matrix"] = "float matrix"
        self.typeTable["MDIVIDE"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable["MDIVIDE"]["float matrix"] = {}
        self.typeTable["MDIVIDE"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable["MDIVIDE"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable["PASSIGN"] = self.typeTable["+"]
        self.typeTable["MASSIGN"] = self.typeTable["-"]
        self.typeTable["TASSIGN"] = self.typeTable["*"]
        self.typeTable["DASSIGN"] = self.typeTable["/"]

        self.typeTable["<"] = {}
        self.typeTable["<"]["integer"] = {}
        self.typeTable["<"]["integer"]["integer"] = "boolean"
        self.typeTable["<"]["integer"]["float"] = "boolean"
        self.typeTable["<"]["float"] = {}
        self.typeTable["<"]["float"]["integer"] = "boolean"
        self.typeTable["<"]["float"]["float"] = "boolean"

        self.typeTable[">"] = self.typeTable["<"]
        self.typeTable["<="] = self.typeTable["<"]
        self.typeTable[">="] = self.typeTable["<"]
        self.typeTable["=="] = self.typeTable["<"]
        self.typeTable["!="] = self.typeTable["<"]

    def getType(self, leftType, action, rightType):
        if action not in self.typeTable:
            print(f"unknown action {action}")
            return None
        if leftType not in self.typeTable[action]:
            print(f"illegal left type {leftType} {action}")
            return None
        if rightType not in self.typeTable[action][leftType]:
            print(f"illegal right type {leftType} {action} {rightType}")
            return None
        return self.typeTable[action][leftType][rightType]

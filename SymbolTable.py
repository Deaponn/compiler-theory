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

        self.typeTable[".+"] = {}
        self.typeTable[".+"]["integer matrix"] = {}
        self.typeTable[".+"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable[".+"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable[".+"]["float matrix"] = {}
        self.typeTable[".+"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable[".+"]["float matrix"]["float matrix"] = "float matrix"
        self.typeTable[".+"]["string matrix"] = {}
        self.typeTable[".+"]["string matrix"]["string matrix"] = "string matrix"

        self.typeTable[".-"] = {}
        self.typeTable[".-"]["integer matrix"] = {}
        self.typeTable[".-"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable[".-"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable[".-"]["float matrix"] = {}
        self.typeTable[".-"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable[".-"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable[".*"] = {}
        self.typeTable[".*"]["integer matrix"] = {}
        self.typeTable[".*"]["integer matrix"]["integer matrix"] = "integer matrix"
        self.typeTable[".*"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable[".*"]["float matrix"] = {}
        self.typeTable[".*"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable[".*"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable["./"] = {}
        self.typeTable["./"]["integer matrix"] = {}
        self.typeTable["./"]["integer matrix"]["integer matrix"] = "float matrix"
        self.typeTable["./"]["integer matrix"]["float matrix"] = "float matrix"
        self.typeTable["./"]["float matrix"] = {}
        self.typeTable["./"]["float matrix"]["integer matrix"] = "float matrix"
        self.typeTable["./"]["float matrix"]["float matrix"] = "float matrix"

        self.typeTable[".+"] = self.typeTable["+"]
        self.typeTable[".-"] = self.typeTable["-"]
        self.typeTable[".*"] = self.typeTable["*"]
        self.typeTable["./"] = self.typeTable["/"]

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

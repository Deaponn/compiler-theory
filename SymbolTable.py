class VariableSymbol(object):
    def __init__(self, name, typeOfVariable):
        self.name = name
        self.typeOfVariable = typeOfVariable

class SymbolTable(object):
    def __init__(self): # parent scope and symbol table name
        self.scopes = [{}]
        self.loopDepth = 0

    def put(self, name, typeOfValue): # put variable symbol or fundef under <name> entry
        self.scopes[-1][name] = typeOfValue

    def get(self, name): # get variable symbol or fundef from <name> entry
        for scope_idx in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[scope_idx]:
                return self.scopes[scope_idx][name]
        return None

    def erase(self, name):
        if name is None:
            return
        for scope_idx in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[scope_idx]:
                del self.scopes[scope_idx][name]

    def pushScope(self):
        self.scopes.append({})

    def popScope(self):
        self.scopes.pop()

    def modifyLoopCount(self, delta):
        self.loopDepth += delta

    def isInsideLoop(self):
        return self.loopDepth > 0

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
        action = action.replace("=", "") if action[0] in "+-*/" else action
        if action not in self.typeTable:
            # print(f"unknown action {action}")
            return None
        if leftType not in self.typeTable[action]:
            # print(f"illegal left type {leftType} {action}")
            return None
        if rightType not in self.typeTable[action][leftType]:
            # print(f"illegal right type {leftType} {action} {rightType}")
            return None
        return self.typeTable[action][leftType][rightType]

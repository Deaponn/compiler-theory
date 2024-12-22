class VariableSymbol(object):
    def __init__(self, name, typeOfVariable):
        self.name = name
        self.typeOfVariable = typeOfVariable

# TODO: add string comparison to TypeTable

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
        self.typeTable = {
            "+": {
                "integer": {
                    "integer": "integer",
                    "float": "float"
                },
                "float": {
                    "integer": "float",
                    "float": "float"
                },
                "string": {
                    "string": "string"
                }
            },
            "-": {
                "integer": {
                    "integer": "integer",
                    "float": "float"
                },
                "float": {
                    "integer": "float",
                    "float": "float"
                }
            },
            "*": {
                "integer": {
                    "integer": "integer",
                    "float": "float",
                    "string": "string"
                },
                "float": {
                    "integer": "float",
                    "float": "float"
                },
                "string": {
                    "integer": "string"
                }
            },
            "/": {
                "integer": {
                    "integer": "float",
                    "float": "float"
                },
                "float": {
                    "integer": "float",
                    "float": "float"
                }
            },
            "<": {
                "integer": {
                    "integer": "boolean",
                    "float": "boolean"
                },
                "float": {
                    "integer": "boolean",
                    "float": "boolean"
                }
            }
        }

        self.typeTable[".+"] = self.typeTable["+"]
        self.typeTable[".-"] = self.typeTable["-"]
        self.typeTable[".*"] = self.typeTable["*"]
        self.typeTable["./"] = self.typeTable["/"]

        self.typeTable[">"] = self.typeTable["<"]
        self.typeTable["<="] = self.typeTable["<"]
        self.typeTable[">="] = self.typeTable["<"]
        self.typeTable["=="] = self.typeTable["<"]
        self.typeTable["!="] = self.typeTable["<"]

    def getType(self, leftType, action, rightType):
        action = action.replace("=", "") if action[0] in "+-*/" else action
        if action not in self.typeTable:
            return None
        if leftType not in self.typeTable[action]:
            return None
        if rightType not in self.typeTable[action][leftType]:
            return None
        return self.typeTable[action][leftType][rightType]

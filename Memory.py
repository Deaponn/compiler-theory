class Memory:
    def __init__(self):
        self.scopes = [{}]

    def get(self, name):
        for scope_idx in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[scope_idx]:
                return self.scopes[scope_idx][name]
        return None

    def put(self, name, value):
        for scope_idx in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[scope_idx]:
                self.scopes[scope_idx][name] = value
                return
        self.scopes[-1][name] = value

    def pushScope(self):
        self.scopes.append({})

    def popScope(self):
        self.scopes.pop()

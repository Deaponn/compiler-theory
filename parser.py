from sly import Parser as SlyParser
from scanner import Scanner
from AST import *

# TODO: change if "..." in p._namemap to something better

class Parser(SlyParser):

    tokens = Scanner.tokens

    debugfile = 'parser.out'

    precedence = (
        ("nonassoc", IFX),
        ("nonassoc", ELSE),
        ("nonassoc", '<', LEQ, '>', GEQ, EQ, NEQ),
        ("left", '+', MPLUS, '-', MMINUS),
        ("left", '*', MTIMES, '/', MDIVIDE),
        ('right', UMINUS, "\'"),
    )

    def __init__(self):
        self.names = { }

    @_('block start', 'block')
    def start(self, p):
        if "start" in p._namemap:
            return StartNode(p.block, p.start)
        else:
            return StartNode(p.block)

    @_('statement', '"{" next_statements "}"')
    def block(self, p):
        if "statement" in p._namemap:
            return Statement(p.statement)
        else:
            return p.next_statements

    @_('statement next_statements', 'statement')
    def next_statements(self, p):
        if "next_statements" in p._namemap:
            return Statement(p.statement, p.next_statements)
        else:
            return Statement(p.statement)

    @_('action_statement ";"', 'flow_control_statement')
    def statement(self, p):
        return p[0]

    @_('id_expr "=" expr', 'id_expr PASSIGN expr', 'id_expr MASSIGN expr', 'id_expr TASSIGN expr',
        'id_expr DASSIGN expr', 'PRINT values', 'RETURN expr', 'CONTINUE', 'BREAK')
    def action_statement(self, p):
        if len(p) == 3: # must handle "left hand of assign is not an ID" error
            return AssignStatement(p.id_expr, p[1], p.expr)
        elif "RETURN" in p._namemap:
            return ReturnValue(p.expr)
        elif "PRINT" in p._namemap:
            return PrintValue(p.values)
        else:
            return LoopControlNode(p[0]) # catch both CONTINUE and BREAK
        # print("def statement, id = expr")
        # self.names[p.ID] = p.expr

    @_('INT "," indexes', 'INT')
    def indexes(self, p):
        if "indexes" in p._namemap:
            return IndexList(p.INT, p.indexes)
        else:
            return IndexList(p.INT)

    @_('expr "," values', 'expr')
    def values(self, p):
        if "values" in p._namemap:
            return ValueList(p.expr, p.values)
        else:
            return ValueList(p.expr)

    @_('IF expr block %prec IFX', 'IF expr block ELSE block',
        'WHILE expr block', 'FOR ID "=" range block')
    def flow_control_statement(self, p):
        if "IF" in p._namemap and "ELSE" in p._namemap:
            return IfStatement(p.expr, p.block0, p.block1)
        elif "IF" in p._namemap:
            return IfStatement(p.expr, p.block)
        elif "WHILE" in p._namemap:
            return WhileStatement(p.expr, p.block)
        elif "FOR" in p._namemap:
            return ForStatement(p.ID, p.range, p.block)

    @_('expr "+" expr', 'expr "-" expr',
        'expr "*" expr', 'expr "/" expr',
        'expr MPLUS expr', 'expr MMINUS expr',
        'expr MTIMES expr', 'expr MDIVIDE expr')
    def expr(self, p):
        return ArithmeticExpression(p.expr0, p[1], p.expr1)
        # return p.expr0 + p.expr1

        # if p.expr0.shape != p.expr1.shape:
        #     print("incompatible matrix dimensions")
        #     raise
        # return p.expr0 + p.expr1

    @_('"-" expr %prec UMINUS', '"\'" expr %prec "\'"')
    def expr(self, p):
        return BoundExpression(p.expr, p[0])
        # return -p.expr

    @_('expr "<" expr', 'expr LEQ expr',
        'expr ">" expr', 'expr GEQ expr',
        'expr EQ expr', 'expr NEQ expr', )
    def expr(self, p):
        return ComparisonExpression(p.expr0, p[1], p.expr1)

    @_('"(" expr ")"')
    def expr(self, p):
        return ValueNode(p.expr)
        # return p.expr

    # TODO: check if this production is necessary
    @_('expr "\'"')
    def expr(self, p):
        return ApplyTransposition(p.expr)
        # if not isinstance(p.expr, np.ndarray):
        #     print("variable is not a matrix and cannot be transposed")
        #     raise
        # return p.expr.T

    @_('expr ":" expr')
    def range(self, p):
        return RangeNode(p.expr0, p.expr1)

    @_('INT', 'FLOAT', 'STRING', 'id_expr')
    def expr(self, p):
        if "id_expr" in p._namemap:
            return p.id_expr
        else:
            return ValueNode(p[0])
        # return p[0]
        # try:
        #     return self.names[p.ID]
        # except LookupError:
        #     print("Undefined ID '%s'" % p.ID)
        #     return 0

    @_('ID', 'ID "[" indexes "]"')
    def id_expr(self, p):
        if "indexes" in p._namemap:
            return IndexedVariable(p.ID, p.indexes)
        else:
            return Variable(p.ID)

    @_('"[" outerlist "]"')
    def expr(self, p):
        return Outerlist(p.outerlist)

    @_('"[" values "]" "," outerlist', '"[" values "]"')
    def outerlist(self, p):
        if "outerlist" in p._namemap:
            return Outerlist(p.values, p.outerlist)
        else:
            return Outerlist(p.values)

    @_('ZEROS "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.ZEROS, p.expr)

    @_('ONES "(" expr ")"') 
    def expr(self, p):
        return MatrixInitiator(p.ONES, p.expr)

    @_('EYE "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.EYE, p.expr)

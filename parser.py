from sly import Parser as SlyParser
from scanner import Scanner
from AST import *

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

    @_('block')
    def start(self, p):
        return StartNode(p.block)

    @_('block start')
    def start(self, p):
        return StartNode(p.block, p.start)

    @_('statement')
    def block(self, p):
        return Statement(p.statement)

    @_('"{" next_statements "}"')
    def block(self, p):
        return p.next_statements

    @_('statement')
    def next_statements(self, p):
        return Statement(p.statement)

    @_('statement next_statements')
    def next_statements(self, p):
        return Statement(p.statement, p.next_statements)

    @_('action_statement ";"', 'flow_control_statement')
    def statement(self, p):
        return p[0]

    @_('id_expr "=" expr', 'id_expr PASSIGN expr', 'id_expr MASSIGN expr',
        'id_expr TASSIGN expr', 'id_expr DASSIGN expr')
    def action_statement(self, p):
        return AssignStatement(p.id_expr, p[1], p.expr)

    @_('PRINT values')
    def action_statement(self, p):
        return PrintValue(p.values)

    @_('RETURN expr')
    def action_statement(self, p):
        return ReturnValue(p.expr)

    @_('CONTINUE', 'BREAK')
    def action_statement(self, p):
        return LoopControlNode(p[0])

    @_('INT')
    def indexes(self, p):
        return IndexList(p.INT)

    @_('INT "," indexes')
    def indexes(self, p):
        return IndexList(p.INT, p.indexes)

    @_('expr')
    def values(self, p):
        return ValueList(p.expr)

    @_('expr "," values')
    def values(self, p):
        return ValueList(p.expr, p.values)

    @_('IF expr block %prec IFX')
    def flow_control_statement(self, p):
        return IfStatement(p.expr, p.block)

    @_('IF expr block ELSE block')
    def flow_control_statement(self, p):
        return IfStatement(p.expr, p.block0, p.block1)

    @_('WHILE expr block')
    def flow_control_statement(self, p):
        return WhileStatement(p.expr, p.block)

    @_('FOR ID "=" range block')
    def flow_control_statement(self, p):
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

    @_('INT', 'FLOAT', 'STRING')
    def expr(self, p):
        return ValueNode(p[0])

    @_('id_expr')
    def expr(self, p):
        return p.id_expr
        # try:
        #     return self.names[p.ID]
        # except LookupError:
        #     print("Undefined ID '%s'" % p.ID)
        #     return 0

    @_('ID')
    def id_expr(self, p):
        return Variable(p.ID)

    @_('ID "[" indexes "]"')
    def id_expr(self, p):
        return IndexedVariable(p.ID, p.indexes)

    @_('"[" outerlist "]"')
    def expr(self, p):
        return Outerlist(p.outerlist)

    @_('"[" values "]"')
    def outerlist(self, p):
        return Outerlist(p.values)

    @_('"[" values "]" "," outerlist')
    def outerlist(self, p):
        return Outerlist(p.values, p.outerlist)

    @_('ZEROS "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.ZEROS, p.expr)

    @_('ONES "(" expr ")"') 
    def expr(self, p):
        return MatrixInitiator(p.ONES, p.expr)

    @_('EYE "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.EYE, p.expr)

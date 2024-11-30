from sly import Parser as SlyParser
from scanner import Scanner
from AST import *

class Parser(SlyParser):

    tokens = Scanner.tokens

    debugfile = 'parser.out'

    precedence = (
        ("nonassoc", IFX),
        ("nonassoc", ELSE),
        ("nonassoc", "<", LEQ, ">", GEQ, EQ, NEQ),
        ("left", "+", MPLUS, "-", MMINUS),
        ("left", "*", MTIMES, "/", MDIVIDE),
        ("right", UMINUS, "'"),
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
        return BlockStatement(p.next_statements)

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

    @_('expr')
    def values(self, p):
        return ValueList(p.expr)

    @_('expr "," values')
    def values(self, p):
        return ValueList(p.expr, p.values)

    @_('"[" values "]"')
    def expr(self, p):
        return Vector(p.values)

    @_('"[" matrix "]"')
    def expr(self, p):
        return Matrix(p.matrix)

    @_('"[" values "]"')
    def matrix(self, p):
        return Vector(p.values)

    @_('"[" values "]" , matrix')
    def matrix(self, p):
        return Vector(p.values, p.matrix)

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

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return NegateExpression(p.expr)

    @_('expr "\'"')
    def expr(self, p):
        return TransposeExpression(p.expr)

    @_('expr "<" expr', 'expr LEQ expr',
        'expr ">" expr', 'expr GEQ expr',
        'expr EQ expr', 'expr NEQ expr', )
    def expr(self, p):
        return ComparisonExpression(p.expr0, p[1], p.expr1)

    @_('"(" expr ")"')
    def expr(self, p):
        return ValueNode(p.expr)

    @_('expr ":" expr')
    def range(self, p):
        return RangeNode(p.expr0, p.expr1)

    @_('INT', 'FLOAT', 'STRING')
    def expr(self, p):
        return ValueNode(p[0])

    @_('id_expr')
    def expr(self, p):
        return p.id_expr

    @_('ID')
    def id_expr(self, p):
        return Variable(p.ID)

    @_('ID "[" values "]"')
    def id_expr(self, p):
        return IndexedVariable(p.ID, p.values)

    @_('ZEROS "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.ZEROS, p.expr)

    @_('ONES "(" expr ")"') 
    def expr(self, p):
        return MatrixInitiator(p.ONES, p.expr)

    @_('EYE "(" expr ")"')
    def expr(self, p):
        return MatrixInitiator(p.EYE, p.expr)

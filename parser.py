from sly import Parser as SlyParser
from scanner import Scanner
from AST import *

class Parser(SlyParser):

    tokens = Scanner.tokens

    debugfile = 'parser.out'

    precedence = (
        ("right", ",", "]"),
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
        return StartNode(p.block, lineno=p.lineno)

    @_('block start')
    def start(self, p):
        return StartNode(p.block, p.start, lineno=p.lineno)

    @_('statement')
    def block(self, p):
        return Statement(p.statement, lineno=p.lineno)

    @_('"{" next_statements "}"')
    def block(self, p):
        return BlockStatement(p.next_statements, lineno=p.lineno)

    @_('statement')
    def next_statements(self, p):
        return Statement(p.statement, lineno=p.lineno)

    @_('statement next_statements')
    def next_statements(self, p):
        return Statement(p.statement, p.next_statements, lineno=p.lineno)

    @_('action_statement ";"', 'flow_control_statement')
    def statement(self, p):
        return p[0]

    @_('id_expr "=" expr', 'id_expr PASSIGN expr', 'id_expr MASSIGN expr',
        'id_expr TASSIGN expr', 'id_expr DASSIGN expr')
    def action_statement(self, p):
        return AssignStatement(p.id_expr, p[1], p.expr, lineno=p.lineno)

    @_('PRINT values')
    def action_statement(self, p):
        p.values.weak = True
        return PrintValue(p.values, lineno=p.lineno)

    @_('RETURN expr')
    def action_statement(self, p):
        return ReturnValue(p.expr, lineno=p.lineno)

    @_('CONTINUE', 'BREAK')
    def action_statement(self, p):
        return LoopControlNode(p[0], lineno=p.lineno)

    @_('expr')
    def values(self, p):
        return ValueList(p.expr, lineno=p.lineno)

    @_('expr "," values')
    def values(self, p):
        return ValueList(p.expr, p.values, lineno=p.lineno)

    @_('"[" values "]"')
    def expr(self, p):
        return Vector(p.values, lineno=p.lineno)

    @_('"[" "[" values "]" "]"')
    def expr(self, p):
        return Vector(Vector(p.values, lineno=p.lineno), isMatrixHead=True, lineno=p.lineno)

    @_('"[" "[" values "]" , next_values "]"')
    def expr(self, p):
        return Vector(Vector(p.values, p.next_values, lineno=p.lineno), isMatrixHead=True, lineno=p.lineno)

    @_('"[" values "]"')
    def next_values(self, p):
        return Vector(p.values, lineno=p.lineno)

    @_('"[" values "]" , next_values')
    def next_values(self, p):
        return Vector(p.values, p.next_values, lineno=p.lineno)

    @_('IF "(" expr ")" block %prec IFX')
    def flow_control_statement(self, p):
        return IfStatement(p.expr, p.block, lineno=p.lineno)

    @_('IF "(" expr ")" block ELSE block')
    def flow_control_statement(self, p):
        return IfStatement(p.expr, p.block0, p.block1, lineno=p.lineno)

    @_('WHILE "(" expr ")" block')
    def flow_control_statement(self, p):
        return WhileStatement(p.expr, p.block, lineno=p.lineno)

    @_('FOR ID "=" range block')
    def flow_control_statement(self, p):
        return ForStatement(p.ID, p.range, p.block, lineno=p.lineno)

    @_('expr "+" expr', 'expr "-" expr',
        'expr "*" expr', 'expr "/" expr',
        'expr MPLUS expr', 'expr MMINUS expr',
        'expr MTIMES expr', 'expr MDIVIDE expr')
    def expr(self, p):
        return ArithmeticExpression(p.expr0, p[1], p.expr1, lineno=p.lineno)

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return NegateExpression(p.expr, lineno=p.lineno)

    @_('expr "\'"')
    def expr(self, p):
        return TransposeExpression(p.expr, lineno=p.lineno)

    @_('expr "<" expr', 'expr LEQ expr',
        'expr ">" expr', 'expr GEQ expr',
        'expr EQ expr', 'expr NEQ expr', )
    def expr(self, p):
        return ComparisonExpression(p.expr0, p[1], p.expr1, lineno=p.lineno)

    @_('expr ":" expr')
    def range(self, p):
        return RangeNode(p.expr0, p.expr1, lineno=p.lineno)

    @_('STRING')
    def expr(self, p):
        return ValueNode(p[0][1:-1], "string", lineno=p.lineno)

    @_('FLOAT')
    def expr(self, p):
        return ValueNode(p[0], "float", lineno=p.lineno)

    @_('INT')
    def expr(self, p):
        return ValueNode(p[0], "integer", lineno=p.lineno)

    @_('expr')
    def idx_values(self, p):
        return IndexList(p.expr, lineno=p.lineno)

    @_('":"')
    def idx_values(self, p):
        return IndexList(ValueNode(p[0], "integer"), lineno=p.lineno)

    @_('expr "," idx_values')
    def idx_values(self, p):
        return IndexList(p.expr, p.idx_values, lineno=p.lineno)

    @_('":" "," idx_values')
    def idx_values(self, p):
        return IndexList(ValueNode(p[0], "integer"), p.idx_values, lineno=p.lineno)

    @_('id_expr')
    def expr(self, p):
        return p.id_expr

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('ID')
    def id_expr(self, p):
        return Variable(p.ID, lineno=p.lineno)

    @_('ID "[" idx_values "]"')
    def id_expr(self, p):
        return IndexedVariable(p.ID, p.idx_values, lineno=p.lineno)

    @_('ZEROS "(" values ")"')
    def expr(self, p):
        return MatrixInitiator(p.ZEROS, p.values, lineno=p.lineno)

    @_('ONES "(" values ")"') 
    def expr(self, p):
        return MatrixInitiator(p.ONES, p.values, lineno=p.lineno)

    @_('EYE "(" values ")"')
    def expr(self, p):
        return MatrixInitiator(p.EYE, p.values, lineno=p.lineno)

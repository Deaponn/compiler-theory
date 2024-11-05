from sly import Parser as SlyParser
from scanner import Scanner

class Parser(SlyParser):

    tokens = Scanner.tokens

    debugfile = 'parser.out'

    precedence = (
        ("nonassoc", '<', LEQ, '>', GEQ, EQ, NEQ),
        ("left", IF, WHILE, FOR),
        ("left", '+', MPLUS, '-', MMINUS),
        ("left", '*', MTIMES, '/', MDIVIDE),
        # ('right', ELSE, UMINUS, "\'"),
        ('right', ELSE, "\'"),
    )

    def __init__(self):
        self.names = { }

    @_('')
    def empty(self, p):
        pass

    @_('statement start', '"{" start "}" start')
    def start(self, p):
        pass
        # return p.statement
    
    @_('empty')
    def start(self, p):
        pass

    @_('left_assign "=" expr ";"', 'left_assign PASSIGN expr ";"', 'left_assign MASSIGN expr ";"',
        'left_assign TASSIGN expr ";"', 'left_assign DASSIGN expr ";"', 'RETURN expr ";"', 'CONTINUE ";"', 'BREAK ";"')
    def statement(self, p):
        pass
        # print("def statement, id = expr")
        # self.names[p.ID] = p.expr

    @_('ID', 'ID "[" indexes "]"')
    def left_assign(self, p):
        pass

    @_('INT "," indexes', 'INT')
    def indexes(self, p):
        pass

    @_('expr ";"')
    def statement(self, p):
        pass
        # print("def statement, expr", p.expr)

    @_('PRINT values')
    def statement(self, p):
        pass

    @_('expr "," values', 'expr ";"')
    def values(self, p):
        pass

    @_('IF expr block', 'IF expr block ELSE block',
        'WHILE expr block', 'FOR ID "=" range block')
    def statement(self, p):
        pass

    @_('statement', '"{" start "}"')
    def block(self, p):
        pass

    @_('expr "+" expr', 'expr "-" expr',
        'expr "*" expr', 'expr "/" expr',
        'expr MPLUS expr', 'expr MMINUS expr',
        'expr MTIMES expr', 'expr MDIVIDE expr')
    def expr(self, p):
        pass
        # return p.expr0 + p.expr1

        # if p.expr0.shape != p.expr1.shape:
        #     print("incompatible matrix dimensions")
        #     raise
        # return p.expr0 + p.expr1

    # @_('"-" expr %prec UMINUS')
    # def expr(self, p):
    #     pass
        # return -p.expr


    @_('"\'" expr %prec "\'"')
    def expr(self, p):
        pass

    @_('expr "<" expr', 'expr LEQ expr',
        'expr ">" expr', 'expr GEQ expr',
        'expr EQ expr', 'expr NEQ expr', )
    def expr(self, p):
        pass

    @_('"(" expr ")"')
    def expr(self, p):
        pass
        # return p.expr

    @_('expr "\'"')
    def expr(self, p):
        pass
        # if not isinstance(p.expr, np.ndarray):
        #     print("variable is not a matrix and cannot be transposed")
        #     raise
        # return p.expr.T

    @_('INT ":" INT', 'ID ":" ID', 'ID ":" INT', 'INT ":" ID')
    def range(self, p):
        pass

    @_('INT', 'FLOAT', 'STRING')
    def expr(self, p):
        pass
        # return p[0]

    @_('"[" outerlist "]"')
    def expr(self, p):
        pass

    @_('outerlist "," "[" innerlist "]"')
    def outerlist(self, p):
        pass

    @_('"[" innerlist "]"')
    def outerlist(self, p):
        pass

    @_('innerlist "," elem')
    def innerlist(self, p):
        pass

    @_('elem')
    def innerlist(self, p):
        pass

    @_('INT', 'FLOAT', 'STRING')
    def elem(self, p):
        pass

    @_('ID')
    def expr(self, p):
        pass
        # try:
        #     return self.names[p.ID]
        # except LookupError:
        #     print("Undefined ID '%s'" % p.ID)
        #     return 0

    @_('ZEROS "(" expr ")"')
    def expr(self, p):
        pass
        # return self.get_zeros(p.expr)

    @_('ONES "(" expr ")"') 
    def expr(self, p):
        pass
        # return self.get_ones(p.expr)

    @_('EYE "(" expr ")"')
    def expr(self, p):
        pass
        # return self.get_eye(p.expr)

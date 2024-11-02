from sly import Parser as SlyParser
from scanner import Scanner

class Parser(SlyParser):

    tokens = Scanner.tokens

    debugfile = 'parser.out'

    precedence = (
        ("nonassoc", LSS, LEQ, GTR, GEQ, '=', EQ, NEQ),
        ("left", '+', MPLUS, '-', MMINUS),
        ("left", '*', MTIMES, '/', MDIVIDE),
        ('right', UMINUS),   
    )

    def __init__(self):
        self.names = { }

    @_('')
    def empty(self, p):
        pass

    @_('statement ";" start')
    def start(self, p):
        return p.statement
    
    @_('empty')
    def start(self, p):
        pass

    @_('ID "=" expr')
    def statement(self, p):
        print("def statement, id = expr")
        self.names[p.ID] = p.expr

    @_('expr')
    def statement(self, p):
        print("def statement, expr", p.expr)

    @_('expr "+" expr')
    def expr(self, p):
        return p.expr0 + p.expr1

    @_('expr MPLUS expr')
    def expr(self, p):
        if p.expr0.shape != p.expr1.shape:
            print("incompatible matrix dimensions")
        return p.expr0 + p.expr1

    @_('expr "-" expr')
    def expr(self, p):
        return p.expr0 - p.expr1

    @_('expr "*" expr')
    def expr(self, p):
        return p.expr0 * p.expr1

    @_('expr "/" expr')
    def expr(self, p):
        return p.expr0 / p.expr1

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return -p.expr

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('INT', 'FLOAT')
    def expr(self, p):
        return p[0]

    @_('ID')
    def expr(self, p):
        try:
            return self.names[p.ID]
        except LookupError:
            print("Undefined ID '%s'" % p.ID)
            return 0

    @_('ZEROS "(" expr ")"')
    def expr(self, p):
        return self.get_zeros(p.expr)

    @_('ONES "(" expr ")"') 
    def expr(self, p):
        return self.get_ones(p.expr)

    @_('EYE "(" expr ")"')
    def expr(self, p):
        return self.get_eye(p.expr)

    def get_zeros(self, n):
        return [[0] * n for _ in range(n)]

    def get_ones(self, n):
        return [[1] * n for _ in range(n)]

    def get_eye(self, n):
        return [[1 if row == col else 0 for row in range(n)] for col in range(n)]
    
    def get_dim(self, matrix):
        return (len(matrix), len(matrix[0]))

    # @_("expr PLUS expr",
    #     "expr MPLUS expr",
    #     "expr MINUS expr",
    #     "expr MMINUS expr",
    #     "expr TIMES expr",
    #     "expr MTIMES expr",
    #     "expr DIVIDE expr",
    #     "expr MDIVIDE expr",
    # )
    # def expr(self, p):
    #     return p.expr0

    # @_('instructions_opt')
    # def p_program(p):
    #     pass

    # @_('instructions')
    # def p_instructions_opt(p):
    #     pass

    # @_('')
    # def p_instructions_opt(p):
    #     pass

    # @_('instructions instruction')
    # def p_instructions(p):
    #     pass

    # @_('instruction')
    # def p_instructions(p):
    #     pass


    # to finish the grammar
    # ....


from sly import Lexer


class Scanner(Lexer):
    # Set of token names.   This is always required
    tokens = { PLUS, MINUS, TIMES, DIVIDE, MPLUS, MMINUS, MTIMES, MDIVIDE,
               ASSIGN, PASSIGN, MASSIGN, TASSIGN, DASSIGN,
               LSS, LEQ, GTR, GEQ, EQ, NEQ,
               LBRCKR, RBRCKR, LBRCKS, RBRCKS, LBRCKC, RBRCKC,
               RANGE, TRANSPOSITION, COMMA, SEMICOLON,
               IF, ELSE, FOR, WHILE, BREAK, CONTINUE, RETURN,
               EYE, ZEROS, ONES, PRINT,
               ID, INT, FLOAT, STRING }

    # String containing ignored characters between tokens
    ignore = ' \t'
    ignore_comment = r'#.*'

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # Compute column.
    #     input is the input text string
    #     token is a token instance
    def find_column(self, token):
        last_cr = self.text.rfind('\n', 0, token.index)
        if last_cr < 0:
            last_cr = 0
        column = (token.index - last_cr) + 1
        return column

    # Error handling rule
    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {self.lineno}, column {self.find_column(t)}")
        self.index += 1

    literals = { '+', '-', '*', '/', '=', '<', '>', '\'',
                 '(', ')', '[', ']', '{', '}', ':', ';', ',' }

    # Regular expression rules for tokens
    # FLOAT           = r'[+-]?([0-9]*([.][0-9]*))'
    FLOAT           = r'[-+]?(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([eE][-+]?\d+)?'
    INT             = r'[+-]?[0-9]+'
    STRING          = r'["].+["]'
    ID              = r'[a-zA-Z_][a-zA-Z0-9_]*'
    ID['if']        = IF
    ID['else']      = ELSE
    ID['for']       = FOR
    ID['while']     = WHILE
    ID['break']     = BREAK
    ID['continue']  = CONTINUE
    ID['return']    = RETURN
    ID['eye']       = EYE
    ID['zeros']     = ZEROS
    ID['ones']      = ONES
    ID['print']     = PRINT
    MPLUS           = r'[.][+]'
    MMINUS          = r'[.]-'
    MTIMES          = r'[.][*]'
    MDIVIDE         = r'[.]/'
    PASSIGN         = r'[+]='
    MASSIGN         = r'-='
    TASSIGN         = r'[*]='
    DASSIGN         = r'/='
    LEQ             = r'<='
    GEQ             = r'>='
    EQ              = r'=='
    NEQ             = r'!='

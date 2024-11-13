import sys
from scanner import Scanner
from parser import Parser
from TreePrinter import TreePrinter

if __name__ == '__main__':
    try:
        filename = sys.argv[1] if len(sys.argv) > 1 else "example.txt"
        file = open(filename, "r")
    except IOError:
        print("Cannot open {0} file".format(filename))
        sys.exit(0)

    text = file.read()
    lexer = Scanner()
    parser = Parser()

    for tok in lexer.tokenize(text):
        print(f"line {tok.lineno}: {tok.type} {tok.value}")

    ast = parser.parse(lexer.tokenize(text))
    ast.printTree()

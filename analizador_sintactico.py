
from contextvars import Token
from typing import List
from nodos_ast import Assign, BinOp, FunctionCall, Number, UnaryOp, Variable
from analizador_lexico import Token
   
class Parser:

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0] if tokens else None

    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peekType(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].type
        return None

    def eat(self, tokenType):
        if not self.current or self.current.type != tokenType:
            raise SyntaxError(f"Se esperaba {tokenType}")
        self.advance()

    def parse(self):
        if not self.current:
            raise SyntaxError("Entrada vacía")
        if self.current.type == 'ID' and self.peekType() == 'ASSIGN':
            return self.assignment()
        node = self.expr()
        if self.current:
            raise SyntaxError("Símbolos extra al final")
        return node

    def assignment(self):
        name = self.current.value
        self.advance()
        self.eat('ASSIGN')
        value = self.expr()
        return Assign(name, value)

    def expr(self):
        node = self.term()
        while self.current and self.current.type in ('PLUS', 'MINUS'):
            op = '+' if self.current.type == 'PLUS' else '-'
            self.advance()
            node = BinOp(node, op, self.term())
        return node

    def term(self):
        node = self.power()
        while self.current and self.current.type in ('MUL', 'DIV', 'MOD'):
            if self.current.type == 'MUL':
                op = '*'
            elif self.current.type == 'DIV':
                op = '/'
            else:
                op = '%'
            self.advance()
            node = BinOp(node, op, self.power())
        return node

    def power(self):
        node = self.unary()
        if self.current and self.current.type == 'POW':
            self.advance()
            node = BinOp(node, '^', self.power())
        return node

    def unary(self):
        if self.current and self.current.type == 'MINUS':
            self.advance()
            return UnaryOp('-', self.unary())
        if self.current and self.current.type == 'PLUS':
            self.advance()
            return self.unary()
        return self.atom()

    def atom(self):
        token = self.current
        if not token:
            raise SyntaxError("Expresión incompleta")
        if token.type == 'NUMBER':
            self.advance()
            return Number(float(token.value))
        if token.type == 'ID':
            name = token.value
            self.advance()
            if self.current and self.current.type == 'LPAREN':
                return self.functionCall(name)
            return Variable(name)
        if token.type == 'LPAREN':
            self.advance()
            node = self.expr()
            self.eat('RPAREN')
            return node
        raise SyntaxError(f"Token inválido {token.type}")

    def functionCall(self, name):
        self.eat('LPAREN')
        args = []
        if self.current and self.current.type != 'RPAREN':
            args.append(self.expr())
            while self.current and self.current.type == 'COMMA':
                self.advance()
                args.append(self.expr())
        self.eat('RPAREN')
        return FunctionCall(name, args)

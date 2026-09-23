import re
import math
import tkinter as tk
from tkinter import ttk, scrolledtext
from dataclasses import dataclass
from typing import List, Dict, Any

from analizador_semantico import SemanticAnalyzer, SemanticError
from visualizador import build_ast_graph, build_automaton_graph

@dataclass
class Token:
    type: str
    value: Any
    line: int
    column: int

TOKENS_PATTERNS = [
    ('NUMBER', r'\d+(\.\d*)?|\.\d+'),
    ('POW', r'\*\*|\^'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('MUL', r'\*'),
    ('DIV', r'/'),
    ('MOD', r'%'),
    ('ASSIGN', r'='),
    ('COMMA', r','),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('SKIP', r'[ \t]+'),
    ('NEWLINE', r'\n'),
    ('COMMENT', r'#.*'),
    ('MISMATCH', r'.'),
]

TOKEN_REGEX = [(t, re.compile(p)) for t, p in TOKENS_PATTERNS]

class Lexer:

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            match = None
            for tokenType, regex in TOKEN_REGEX:
                match = regex.match(self.text, self.pos)
                if not match:
                    continue
                value = match.group(0)
                if tokenType == 'NEWLINE':
                    self.pos += len(value)
                    self.line += 1
                    self.column = 1
                    break
                if tokenType in ('SKIP', 'COMMENT'):
                    self.pos += len(value)
                    self.column += len(value)
                    break
                if tokenType == 'MISMATCH':
                    raise SyntaxError(f"Carácter inválido '{value}' en línea {self.line}")
                tokens.append(Token(tokenType, value, self.line, self.column))
                self.pos += len(value)
                self.column += len(value)
                break
            if not match:
                raise SyntaxError("Error léxico desconocido")
        return tokens


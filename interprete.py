import math
from typing import Dict

class Interpreter:

    def __init__(self):
        self.symbols: Dict[str, float] = {
            'pi': math.pi,
            'e': math.e
        }
        self.functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log10,
            'ln': math.log,
            'exp': math.exp,
            'abs': abs,
            'floor': math.floor,
            'ceil': math.ceil,
            'round': round,
            'pow': pow,
            'max': max,
            'min': min
        }

    def visit(self, node):
        return getattr(self, f'visit{type(node).__name__}')(node)

    def visitNumber(self, node):
        return node.value

    def visitVariable(self, node):
        if node.name not in self.symbols:
            raise NameError(f"Variable no definida: {node.name}")
        return self.symbols[node.name]

    def visitAssign(self, node):
        value = self.visit(node.value)
        self.symbols[node.name] = value
        return value

    def visitUnaryOp(self, node):
        val = self.visit(node.expr)
        return -val if node.op == '-' else val

    def visitBinOp(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)
        if node.op == '+':
            return l + r
        if node.op == '-':
            return l - r
        if node.op == '*':
            return l * r
        if node.op == '/':
            if r == 0:
                raise ZeroDivisionError("División por cero")
            return l / r
        if node.op == '%':
            if r == 0:
                raise ZeroDivisionError("Módulo por cero")
            return l % r
        if node.op == '^':
            return l ** r

    def visitFunctionCall(self, node):
        fname = node.name.lower()
        if fname not in self.functions:
            raise NameError(f"Función desconocida: {node.name}")
        args = [self.visit(arg) for arg in node.args]
        try:
            return self.functions[fname](*args)
        except TypeError:
            raise TypeError(f"Número incorrecto de argumentos en {fname}")
        except ValueError:
            raise ValueError(f"Error matemático en {fname}({args})")

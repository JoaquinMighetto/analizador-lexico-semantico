import inspect
from dataclasses import dataclass
from typing import Any, Dict, Set


class SemanticError(Exception):
    pass


@dataclass
class SemanticAnalyzer:
    symbols: Dict[str, Any]
    functions: Dict[str, Any]

    def __post_init__(self):
        self._known_symbols: Set[str] = set(self.symbols.keys())
        self._known_functions = {name.lower(): func for name, func in self.functions.items()}

    def analyze(self, node):
        method = getattr(self, f"visit{type(node).__name__}", None)
        if method is None:
            raise SemanticError(f"Nodo semantico no soportado: {type(node).__name__}")
        return method(node)

    def visitNumber(self, node):
        return None

    def visitVariable(self, node):
        if node.name not in self._known_symbols:
            raise SemanticError(f"Variable no definida: {node.name}")

    def visitUnaryOp(self, node):
        self.analyze(node.expr)

    def visitBinOp(self, node):
        self.analyze(node.left)
        self.analyze(node.right)

    def visitAssign(self, node):
        self.analyze(node.value)
        self._known_symbols.add(node.name)

    def visitFunctionCall(self, node):
        fname = node.name.lower()
        if fname not in self._known_functions:
            raise SemanticError(f"Funcion desconocida: {node.name}")

        for arg in node.args:
            self.analyze(arg)

        self._validate_arity(fname, self._known_functions[fname], len(node.args))

    def _validate_arity(self, name, func, argc):
        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            return

        positional_params = []
        required_params = 0
        accepts_varargs = False

        for param in signature.parameters.values():
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                positional_params.append(param)
                if param.default is inspect._empty:
                    required_params += 1
            elif param.kind == param.VAR_POSITIONAL:
                accepts_varargs = True

        if argc < required_params:
            raise SemanticError(f"Numero insuficiente de argumentos en {name}")

        if not accepts_varargs and argc > len(positional_params):
            raise SemanticError(f"Numero incorrecto de argumentos en {name}")

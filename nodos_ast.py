from dataclasses import dataclass
from typing import List


class ASTNode:
    pass

@dataclass
class Number(ASTNode):
    value: float

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    expr: ASTNode

@dataclass
class Assign(ASTNode):
    name: str
    value: ASTNode

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]

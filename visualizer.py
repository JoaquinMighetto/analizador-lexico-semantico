from typing import Any, Dict, List


def build_ast_tree(node: Any) -> Dict[str, Any]:
    """Convierte un nodo del AST en una estructura simple para mostrar."""
    if node is None:
        return {"type": "None", "label": "None", "children": []}

    node_type = type(node).__name__
    if node_type == "Number":
        label = f"Number: {node.value}"
        children = []
    elif node_type == "Variable":
        label = f"Variable: {node.name}"
        children = []
    elif node_type == "UnaryOp":
        label = f"UnaryOp: {node.op}"
        children = [build_ast_tree(node.expr)]
    elif node_type == "BinOp":
        label = f"BinOp: {node.op}"
        children = [build_ast_tree(node.left), build_ast_tree(node.right)]
    elif node_type == "Assign":
        label = f"Assign: {node.name}"
        children = [build_ast_tree(node.value)]
    elif node_type == "FunctionCall":
        label = f"FunctionCall: {node.name}"
        children = [build_ast_tree(arg) for arg in node.args]
    else:
        label = node_type
        children = []

    return {"type": node_type, "label": label, "children": children}


def format_ast_tree(tree: Dict[str, Any], prefix: str = "") -> str:
    """Devuelve una representación en texto del árbol."""
    lines = [f"{prefix}{tree['label']}"]
    for child in tree.get("children", []):
        lines.append(format_ast_tree(child, prefix + "  "))
    return "\n".join(lines)


def build_automaton_steps(tokens: List[Any]) -> List[Dict[str, Any]]:
    """Genera una secuencia legible de pasos del autómata léxico."""
    steps = []
    for index, token in enumerate(tokens, start=1):
        if token.type in {"NUMBER"}:
            state = "NUMERO"
        elif token.type == "ID":
            state = "IDENTIFICADOR"
        elif token.type in {"PLUS", "MINUS", "MUL", "DIV", "MOD", "POW", "ASSIGN", "COMMA", "LPAREN", "RPAREN"}:
            state = "OPERADOR"
        else:
            state = "OTRO"

        steps.append(
            {
                "step": index,
                "state": state,
                "token_type": token.type,
                "value": token.value,
                "line": token.line,
                "column": token.column,
            }
        )

    if not steps:
        steps.append({"step": 0, "state": "SIN_TOKENS", "token_type": "", "value": "", "line": 0, "column": 0})

    return steps


def format_automaton_steps(steps: List[Dict[str, Any]]) -> str:
    """Devuelve una vista textual del recorrido del autómata."""
    lines = ["Autómata léxico", "================", ""]
    for step in steps:
        if step["step"] == 0:
            lines.append("No se reconocieron tokens.")
            continue
        lines.append(
            f"{step['step']}. {step['state']} -> {step['token_type']} '{step['value']}' "
            f"(línea {step['line']}, columna {step['column']})"
        )
    return "\n".join(lines)

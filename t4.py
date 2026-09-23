import re
import math
import tkinter as tk
from tkinter import ttk, scrolledtext
from dataclasses import dataclass
from typing import List, Dict, Any

from semantic_analyzer import SemanticAnalyzer, SemanticError
from visualizer import build_ast_graph, build_automaton_graph

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

class GUI:
	def __init__(self, root):
		root.title("Compilador")
		root.geometry("800x650")
		root.minsize(650, 500)
		bgMain = "#1e1e1e"
		bgPanel = "#252526"
		bgEntry = "#2d2d2d"
		fgText = "#d4d4d4"
		accent = "#3a8dde"

		style = ttk.Style()
		style.theme_use("clam")
		style.configure("TFrame", background=bgMain)
		style.configure("Card.TFrame", background=bgPanel)
		style.configure("TLabel", background=bgMain, foreground=fgText, font=("Segoe UI", 10))
		style.configure("TButton", background=bgPanel, foreground=fgText, padding=(10, 6), font=("Segoe UI", 10))
		style.configure("TLabelframe", background=bgMain, foreground=fgText)
		style.configure("TLabelframe.Label", background=bgMain, foreground=fgText, font=("Segoe UI", 10, "bold"))
		style.configure("TEntry", fieldbackground=bgEntry, foreground=fgText, padding=6, font=("Consolas", 11))
		style.configure("TNotebook", background=bgMain, borderwidth=0)
		style.configure("TNotebook.Tab", background="#2f2f31", foreground=fgText, padding=(10, 6), font=("Segoe UI", 9))
		style.map(
			"TButton",
			background=[("active", "#2d2d2d"), ("pressed", "#1f1f1f")],
			foreground=[("active", "#d4d4d4"), ("pressed", "#d4d4d4")]
		)
		style.map(
			"TNotebook.Tab",
			background=[("selected", accent), ("active", "#3b3b3d")],
			foreground=[("selected", "white"), ("active", fgText)]
		)
		root.configure(bg=bgMain)
		self.centerWindow(root, 1000, 680)
		self.interpreter = Interpreter()
		self.history = []
		self.histIndex = 0

		mainFrame = ttk.Frame(root, padding=10)
		mainFrame.pack(fill=tk.BOTH, expand=True)

		contentFrame = ttk.Frame(mainFrame)
		contentFrame.pack(fill=tk.BOTH, expand=True)

		leftFrame = ttk.Frame(contentFrame, padding=(0, 0, 10, 0))
		leftFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		rightFrame = ttk.Frame(contentFrame, width=360, padding=8)
		rightFrame.pack(side=tk.RIGHT, fill=tk.Y)
		rightFrame.pack_propagate(False)

		self.output = scrolledtext.ScrolledText(
			leftFrame,
			height=14,
			font=("Consolas", 11),
			bg="#111418",
			fg=fgText,
			insertbackground="white",
			wrap=tk.WORD,
			state='disabled',
			bd=0,
			highlightthickness=0
		)
		self.output.pack(fill=tk.BOTH, expand=True)

		inputFrame = ttk.Frame(leftFrame, padding=(0, 8, 0, 0))
		inputFrame.pack(fill=tk.X)

		ttk.Label(inputFrame, text="Expresión:").pack(side=tk.LEFT, padx=(0, 6))

		self.entry = ttk.Entry(inputFrame)
		self.entry.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, 6))

		self.entry.bind("<Return>", self.execute)
		self.entry.bind("<Up>", self.historyUp)
		self.entry.bind("<Down>", self.historyDown)

		ttk.Button(inputFrame, text="Ejecutar", command=self.execute).pack(side=tk.LEFT)

		varsFrame = ttk.LabelFrame(leftFrame, text="Variables", padding=8)
		varsFrame.pack(fill=tk.X, pady=8)

		self.varsText = scrolledtext.ScrolledText(
			varsFrame,
			height=6,
			font=("Consolas", 10),
			bg="#111418",
			fg=fgText,
			insertbackground="white",
			wrap=tk.WORD,
			state='disabled',
			bd=0,
			highlightthickness=0
		)
		self.varsText.pack(fill=tk.BOTH, expand=True)

		visualFrame = ttk.LabelFrame(rightFrame, text="Visualización de análisis", padding=8)
		visualFrame.pack(fill=tk.BOTH, expand=True)

		visualTabs = ttk.Notebook(visualFrame)
		visualTabs.pack(fill=tk.BOTH, expand=True)

		self.astFrame = ttk.Frame(visualTabs)
		self.astCanvas = tk.Canvas(self.astFrame, bg="#111418", highlightthickness=0)
		self.astCanvas.pack(fill=tk.BOTH, expand=True)
		self.astCanvas.bind("<ButtonPress-1>", self.startDrag)
		self.astCanvas.bind("<B1-Motion>", self.onDrag)
		self.astCanvas.bind("<MouseWheel>", self.onWheel)
		self.astCanvas.bind("<Button-4>", self.onWheel)
		self.astCanvas.bind("<Button-5>", self.onWheel)
		visualTabs.add(self.astFrame, text="Árbol sintáctico")

		self.automatonFrame = ttk.Frame(visualTabs)
		self.automatonCanvas = tk.Canvas(self.automatonFrame, bg="#111418", highlightthickness=0)
		self.automatonCanvas.pack(fill=tk.BOTH, expand=True)
		self.automatonCanvas.bind("<ButtonPress-1>", self.startDrag)
		self.automatonCanvas.bind("<B1-Motion>", self.onDrag)
		self.automatonCanvas.bind("<MouseWheel>", self.onWheel)
		self.automatonCanvas.bind("<Button-4>", self.onWheel)
		self.automatonCanvas.bind("<Button-5>", self.onWheel)
		visualTabs.add(self.automatonFrame, text="Autómata léxico")

		btnFrame = ttk.Frame(leftFrame)
		btnFrame.pack(fill=tk.X, pady=(8, 0))

		ttk.Button(btnFrame, text="Limpiar salida", command=self.clearOutput).pack(side=tk.LEFT, padx=(0, 6))
		ttk.Button(btnFrame, text="Limpiar variables", command=self.clearVariables).pack(side=tk.LEFT)
		ttk.Button(btnFrame, text="Salir", command=root.quit).pack(side=tk.RIGHT)

		self.output.tag_config("result", foreground="#4ec9b0")
		self.output.tag_config("error", foreground="#f44747")
		self.output.tag_config("info", foreground=accent)

		self.drag_data = {"canvas": None, "x": 0, "y": 0}
		self.view_scale = 1.0
		self.graph_offsets = {}
		self.graph_cache = {}
		self.zoom_levels = {}
		self.updateVariablesView()
	
	def centerWindow(self, root, w, h):
		root.update_idletasks()
		sw = root.winfo_screenwidth()
		sh = root.winfo_screenheight()
		x = (sw // 2) - (w // 2)
		y = (sh // 2) - (h // 2)
		root.geometry(f"{w}x{h}+{x}+{y}")
		
	def printOut(self, text, tag=None):
		self.output.configure(state='normal')
		start = self.output.index(tk.END)
		self.output.insert(tk.END, text + "\n")
		end = self.output.index(tk.END)
		if tag:
			self.output.tag_add(tag, start, end)
		self.output.configure(state='disabled')
		self.output.see(tk.END)

	def clearOutput(self):
		self.output.configure(state='normal')
		self.output.delete(1.0, tk.END)
		self.output.configure(state='disabled')
		if hasattr(self, 'astCanvas'):
			self.astCanvas.delete("all")
		if hasattr(self, 'automatonCanvas'):
			self.automatonCanvas.delete("all")
		self.graph_cache.pop(getattr(self, 'astCanvas', None), None)
		self.graph_cache.pop(getattr(self, 'automatonCanvas', None), None)
		self.graph_offsets.pop(getattr(self, 'astCanvas', None), None)
		self.graph_offsets.pop(getattr(self, 'automatonCanvas', None), None)
		self.zoom_levels.pop(getattr(self, 'astCanvas', None), None)
		self.zoom_levels.pop(getattr(self, 'automatonCanvas', None), None)
		
	def updateVariablesView(self):
		self.varsText.configure(state='normal')
		self.varsText.delete(1.0, tk.END)
		symbols = self.interpreter.symbols
		for name, value in sorted(symbols.items()):
			if name not in ('pi', 'e'):
				self.varsText.insert(tk.END, f"{name} = {value:g}\n")
		self.varsText.configure(state='disabled')

	def clearVariables(self):
		self.interpreter.symbols.clear()
		self.interpreter.symbols['pi'] = math.pi
		self.interpreter.symbols['e'] = math.e
		self.updateVariablesView()
		self.printOut("Variables reiniciadas", "info")

	def execute(self, event=None):
		expr = self.entry.get().strip()
		if not expr:
			return
		self.history.append(expr)
		self.histIndex = len(self.history)
		self.printOut(f">>> {expr}")
		try:
			tokens = Lexer(expr).tokenize()
			ast = Parser(tokens).parse()
			SemanticAnalyzer(self.interpreter.symbols, self.interpreter.functions).analyze(ast)
			result = self.interpreter.visit(ast)
			self.printOut(f"= {result:g}", "result")
			self.updateVariablesView()
			self.updateVisualization(ast, tokens)
		except SemanticError as e:
			self.printOut(f"Error semantico: {e}", "error")
		except Exception as e:
			self.printOut(f"Error: {e}", "error")
		self.entry.delete(0, tk.END)

	def startDrag(self, event):
		self.drag_data["canvas"] = event.widget
		self.drag_data["x"] = event.x
		self.drag_data["y"] = event.y

	def onDrag(self, event):
		canvas = event.widget
		if not self.drag_data["canvas"]:
			return
		if self.drag_data["canvas"] is not canvas:
			self.drag_data["canvas"] = canvas
			dx = 0
			dy = 0
		else:
			dx = event.x - self.drag_data["x"]
			dy = event.y - self.drag_data["y"]
		self.drag_data["x"] = event.x
		self.drag_data["y"] = event.y
		old_offset = self.graph_offsets.get(canvas, (0, 0))
		self.graph_offsets[canvas] = (old_offset[0] + dx, old_offset[1] + dy)
		if canvas in self.graph_cache:
			self.drawGraph(canvas, self.graph_cache[canvas])

	def onWheel(self, event):
		canvas = event.widget
		current_zoom = self.zoom_levels.get(canvas, 1.0)
		if event.num == 5 or event.delta < 0:
			new_zoom = max(0.6, current_zoom - 0.1)
		else:
			new_zoom = min(2.2, current_zoom + 0.1)
		self.zoom_levels[canvas] = new_zoom
		if canvas in self.graph_cache:
			self.drawGraph(canvas, self.graph_cache[canvas])

	def drawGraph(self, canvas, graph_data):
		canvas.delete("all")
		nodes = graph_data.get("nodes", [])
		edges = graph_data.get("edges", [])
		if not nodes:
			return

		children_map = {node["id"]: [] for node in nodes}
		incoming = {node["id"]: 0 for node in nodes}
		for edge in edges:
			children_map[edge["from"]].append(edge["to"])
			incoming[edge["to"]] += 1

		root = next((node["id"] for node in nodes if incoming[node["id"]] == 0), nodes[0]["id"])
		depths = {root: 0}
		queue = [root]
		while queue:
			current = queue.pop()
			for child in children_map[current]:
				if child not in depths:
					depths[child] = depths[current] + 1
					queue.append(child)

		for node in nodes:
			if node["id"] not in depths:
				depths[node["id"]] = 0

		by_depth = {}
		for node in nodes:
			by_depth.setdefault(depths[node["id"]], []).append(node)

		positions = {}
		max_depth = max(depths.values()) if depths else 0
		zoom = self.zoom_levels.get(canvas, 1.0)
		offset_x, offset_y = self.graph_offsets.get(canvas, (0, 0))
		for depth in sorted(by_depth):
			items = by_depth[depth]
			for index, node in enumerate(items):
				x = 80 + depth * 180 * zoom + offset_x
				y = 80 + index * 110 * zoom + offset_y
				positions[node["id"]] = (x, y)

		canvas_width = max(320, int(140 + (max_depth + 1) * 180 * zoom))
		canvas_height = max(280, int(120 + len(nodes) * 60 * zoom))
		canvas.config(width=canvas_width, height=canvas_height)

		for edge in edges:
			from_pos = positions[edge["from"]]
			to_pos = positions[edge["to"]]
			line_width = max(1, int(2 * zoom))
			canvas.create_line(
				from_pos[0] + 40 * zoom, from_pos[1],
				to_pos[0] - 40 * zoom, to_pos[1],
				fill="#4fc3f7", width=line_width, arrow=tk.LAST, smooth=True
			)
			canvas.create_text(
				(from_pos[0] + to_pos[0]) // 2,
				(from_pos[1] + to_pos[1]) // 2 - 12 * zoom,
				text=edge.get("label", ""),
				fill="#9cdcfe",
				font=("Segoe UI", int(9 * zoom))
			)

		for node in nodes:
			x, y = positions[node["id"]]
			label = node["label"]
			if len(label) > 24:
				label = label[:21] + "..."
			node_w = int(56 * zoom)
			node_h = int(24 * zoom)
			canvas.create_rectangle(x - node_w // 2, y - node_h // 2, x + node_w // 2, y + node_h // 2, fill="#263b4a", outline="#4fc3f7", width=max(1, int(2 * zoom)))
			canvas.create_text(x, y, text=label, fill="white", font=("Segoe UI", int(10 * zoom), "bold"))

	def updateVisualization(self, ast, tokens):
		ast_graph = build_ast_graph(ast)
		automaton_graph = build_automaton_graph(tokens)
		self.graph_cache[self.astCanvas] = ast_graph
		self.graph_cache[self.automatonCanvas] = automaton_graph
		self.drawGraph(self.astCanvas, ast_graph)
		self.drawGraph(self.automatonCanvas, automaton_graph)

	def historyUp(self, event):
		if self.history:
			self.histIndex = max(0, self.histIndex - 1)
			self.entry.delete(0, tk.END)
			self.entry.insert(0, self.history[self.histIndex])

	def historyDown(self, event):
		if self.history:
			self.histIndex = min(len(self.history), self.histIndex + 1)
			self.entry.delete(0, tk.END)
			if self.histIndex < len(self.history):
				self.entry.insert(0, self.history[self.histIndex])

if __name__ == "__main__":
    root = tk.Tk()
    GUI(root)
    root.mainloop()
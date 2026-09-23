import math
import tkinter as tk
from tkinter import ttk, scrolledtext
from analizador_lexico import Lexer
from analizador_sintactico import Parser
from interprete import Interpreter
from analizador_semantico import SemanticAnalyzer, SemanticError
from visualizador import build_ast_graph, build_automaton_graph

class GUI:
	def __init__(self, root):
		root.title("Compilador")
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
		style.configure("TButton", background=bgPanel, foreground=fgText, padding=(10, 6), font=("Segoe UI", 10), focuscolor="")
		style.configure("TLabelframe", background=bgMain, foreground=fgText)
		style.configure("TLabelframe.Label", background=bgMain, foreground=fgText, font=("Segoe UI", 10, "bold"))
		style.configure("TEntry", fieldbackground=bgEntry, foreground=fgText, padding=6, font=("Consolas", 11))
		style.configure("TNotebook", background=bgMain, borderwidth=0)
		style.configure("TNotebook.Tab", background="#2f2f31", foreground=fgText, padding=(10, 6), font=("Segoe UI", 9))
		style.map(
			"TButton",
			background=[("active", "#2d2d2d"), ("pressed", "#1f1f1f")],
			foreground=[("active", "#d4d4d4"), ("pressed", "#d4d4d4")], 
			focuscolor=[("focus", "")]
		)
		style.map(
			"TNotebook.Tab",
			background=[("selected", accent), ("active", "#3b3b3d")],
			foreground=[("selected", "white"), ("active", fgText)]
		)
		root.configure(bg=bgMain)
		self.centerWindow(root, 1200, 680)
		self.interpreter = Interpreter()
		self.history = []
		self.histIndex = 0

		mainFrame = ttk.Frame(root, padding=10)
		mainFrame.pack(fill=tk.BOTH, expand=True)

		contentFrame = ttk.Frame(mainFrame)
		contentFrame.pack(fill=tk.BOTH, expand=True)

		leftFrame = ttk.Frame(contentFrame, padding=(0, 0, 10, 0))
		leftFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		rightFrame = ttk.Frame(contentFrame, width=500, padding=8)
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
		y = (sh // 2) - (h // 2) - 30
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

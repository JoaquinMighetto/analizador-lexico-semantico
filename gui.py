import math
import tkinter as tk
from tkinter import ttk, scrolledtext
from analizador_lexico import Lexer
from analizador_sintactico import Parser
from interprete import Interpreter
from analizador_semantico import SemanticAnalyzer, SemanticError
from visualizador import build_ast_graph, build_automaton_graph, mark_graph_changes, mark_graph_completed, progressive_graph

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
		self.root = root
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

		legendFrame = ttk.Frame(visualFrame)
		legendFrame.pack(fill=tk.X, pady=(6, 0))
		ttk.Label(legendFrame, text="Nuevo", background="#246b45", foreground="white", padding=(6, 2)).pack(side=tk.LEFT, padx=(0, 4))
		ttk.Label(legendFrame, text="Modificado", background="#8a5528", foreground="white", padding=(6, 2)).pack(side=tk.LEFT)
		ttk.Label(legendFrame, text="Finalizado", background="#216e78", foreground="white", padding=(6, 2)).pack(side=tk.LEFT, padx=(4, 0))

		simulationFrame = ttk.Frame(visualFrame)
		simulationFrame.pack(fill=tk.X, pady=(6, 0))
		self.stepButton = ttk.Button(simulationFrame, text="Iniciar simulación", command=self.toggleStepVisualization)
		self.stepButton.pack(side=tk.LEFT, padx=(0, 6))
		self.stepDelay = tk.DoubleVar(value=1.0)
		self.speedScale = ttk.Scale(simulationFrame, from_=0.5, to=5.0, variable=self.stepDelay, command=self.updateStepDelay, length=100)
		self.speedScale.pack(side=tk.LEFT, padx=(0, 4))
		self.speedLabel = ttk.Label(simulationFrame, text="1.0 s")
		self.speedLabel.pack(side=tk.LEFT, padx=(0, 6))
		self.stepStatus = ttk.Label(simulationFrame, text="Simulación: inactiva")
		self.stepStatus.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
		self.step_running = False
		self.step_job = None
		self.simulation_graph = None
		self.simulation_index = 0
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
		self.resetStepVisualization()
		
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
		self.resetStepVisualization()
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

	def resetStepVisualization(self):
		if self.step_job is not None:
			self.root.after_cancel(self.step_job)
			self.step_job = None
		self.step_running = False
		self.simulation_graph = None
		self.simulation_index = 0
		self.stepStatus.configure(text="Simulación: inactiva")
		self.stepButton.configure(text="Iniciar simulación")

	def updateStepDelay(self, value):
		self.speedLabel.configure(text=f"{float(value):.1f} s")

	def toggleStepVisualization(self):
		if self.step_running:
			self.step_running = False
			if self.step_job is not None:
				self.root.after_cancel(self.step_job)
				self.step_job = None
			self.stepButton.configure(text="Continuar análisis")
			self.stepStatus.configure(text=self.stepStatus.cget("text") + " | pausado")
			return

		if self.simulation_graph is None:
			self.stepStatus.configure(text="Ejecuta una expresión antes de iniciar la simulación")
			return
		if self.simulation_index >= len(self.simulation_graph.get("nodes", [])):
			self.simulation_index = 0
			self.graph_offsets[self.astCanvas] = (0, 0)
			self.astCanvas.delete("all")
		self.step_running = True
		self.stepButton.configure(text="Pausar simulación")
		self.stepVisualization()

	def stepVisualization(self):
		if self.simulation_graph is None:
			self.resetStepVisualization()
			self.stepStatus.configure(text="Ejecuta una expresión antes de iniciar la simulación")
			return

		self.step_job = None
		nodes = self.simulation_graph.get("nodes", [])
		self.simulation_index += 1
		visible_graph = progressive_graph(self.simulation_graph, self.simulation_index)
		visible_graph["nodes"][-1]["change"] = "new"
		visible_graph["nodes"][-1]["active"] = True
		if self.simulation_index >= len(nodes):
			visible_graph = mark_graph_completed(visible_graph)
		self.graph_cache[self.astCanvas] = visible_graph
		self.drawGraph(self.astCanvas, visible_graph, animate=True)
		self.stepStatus.configure(text=f"Nodo {self.simulation_index}/{len(nodes)}: {nodes[self.simulation_index - 1]['label']}")
		if self.simulation_index >= len(nodes):
			self.step_running = False
			self.stepButton.configure(text="Reiniciar simulación")
			self.stepStatus.configure(text=self.stepStatus.cget("text") + " | árbol finalizado")
		else:
			self.scheduleNextStep()

	def scheduleNextStep(self):
		if self.step_running:
			self.step_job = self.root.after(int(self.stepDelay.get() * 1000), self.stepVisualization)

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

	def drawGraph(self, canvas, graph_data, animate=False):
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
		max_width = max((len(items) for items in by_depth.values()), default=1)
		zoom = self.zoom_levels.get(canvas, 1.0)
		offset_x, offset_y = self.graph_offsets.get(canvas, (0, 0))
		for depth in sorted(by_depth):
			items = by_depth[depth]
			for index, node in enumerate(items):
				x = 80 + index * 180 * zoom + offset_x
				y = 80 + depth * 110 * zoom + offset_y
				positions[node["id"]] = (x, y)

		canvas_width = max(320, int(140 + max_width * 180 * zoom))
		canvas_height = max(280, int(120 + (max_depth + 1) * 110 * zoom))
		canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

		for edge in edges:
			from_pos = positions[edge["from"]]
			to_pos = positions[edge["to"]]
			line_width = max(1, int(2 * zoom))
			canvas.create_line(
				from_pos[0], from_pos[1] + 14 * zoom,
				to_pos[0], to_pos[1] - 14 * zoom,
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
			change = node.get("change")
			if change == "new":
				fill = "#246b45"
				outline = "#7ee2a8"
			elif change == "modified":
				fill = "#8a5528"
				outline = "#ffb366"
			elif change == "completed":
				fill = "#216e78"
				outline = "#80e5ed"
			elif node.get("active"):
				fill = "#9a6b24"
				outline = "#ffd166"
			else:
				fill = "#263b4a"
				outline = "#4fc3f7"
			node_tag = f"node_{node['id']}"
			box_tag = f"{node_tag}_box"
			canvas.create_rectangle(
				x - node_w // 2,
				y - node_h // 2,
				x + node_w // 2,
				y + node_h // 2,
				fill=fill,
				outline=outline,
				width=max(1, int(2 * zoom)),
				tags=(box_tag, "node_box")
			)
			canvas.create_text(
				x,
				y,
				text=label,
				fill="white",
				font=("Segoe UI", int(10 * zoom), "bold"),
				tags=(node_tag, "node_label")
			)
			if animate and change in {"new", "modified", "completed"}:
				self.animateActiveNode(canvas, box_tag)

	def animateActiveNode(self, canvas, node_tag, frame=0):
		if not canvas.winfo_exists():
			return
		frames = [("#6f5426", "#fff2aa", 3), ("#d9952b", "#ffe08a", 4), ("#ffd166", "#fff2aa", 3), ("#9a6b24", "#ffd166", 2)]
		fill, outline, width = frames[min(frame, len(frames) - 1)]
		canvas.itemconfigure(node_tag, fill=fill, outline=outline, width=width)
		if frame + 1 < len(frames):
			canvas.after(100, self.animateActiveNode, canvas, node_tag, frame + 1)

	def updateVisualization(self, ast, tokens):
		ast_graph = build_ast_graph(ast)
		automaton_graph = build_automaton_graph(tokens)
		self.simulation_graph = ast_graph
		self.simulation_index = 0
		self.stepStatus.configure(text="Simulación lista: pulsa Iniciar simulación")
		self.stepButton.configure(text="Iniciar simulación")
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

# gui.py
import tkinter as tk
from tkinter import ttk
from compiler import JabaiScriptCompiler


class CompilerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("JabaiScript Compiler")
        self.geometry("900x550")
        self.configure(bg="#D9D9D9")  # Light gray background katulad ng wireframe

        # Instance ng compiler
        self.compiler = JabaiScriptCompiler()

        self._setup_styles()
        self._create_layout()

    def _setup_styles(self):
        """Custom style para sa Treeview Accordion."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)

    def _create_layout(self):
        # 1. LEFT SIDEBAR FRAME (Guide)
        self.left_frame = tk.Frame(self, bg="#B0B0B0", width=220)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        self.left_frame.pack_propagate(False)

        # Guide Header Label
        lbl_guide = tk.Label(
            self.left_frame, text="Guide", font=("Arial", 18, "bold"),
            bg="#B0B0B0", fg="#000000"
        )
        lbl_guide.pack(pady=15)

        # Treeview para sa Collapsible Guide (Datatype, If-else, Loops)
        self.guide_tree = ttk.Treeview(self.left_frame, show="tree")
        self.guide_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Paglalagay ng Collapsible Accordion Items
        # === DITO ILALAGAY YUNG SA DATATYPE ===
        dt_node = self.guide_tree.insert("", "end", text=" Datatype", open=True)
        self.guide_tree.insert(dt_node, "end", text="   int = nambai")
        self.guide_tree.insert(dt_node, "end", text="   double = dubol")
        self.guide_tree.insert(dt_node, "end", text="   float = flot")

        # === DITO ILALAGAY YUNG SA IF-ELSE ===
        if_node = self.guide_tree.insert("", "end", text=" If-else", open=False)
        self.guide_tree.insert(if_node, "end", text="   kung (condition) { ... }")

        # === DITO ILALAGAY YUNG SA LOOPS ===
        loop_node = self.guide_tree.insert("", "end", text=" Loops", open=False)
        self.guide_tree.insert(loop_node, "end", text="   habang (condition) { ... }")

        # === IDINAGDAG NA SWITCH SECTION (Kasama ang Bisaya translation) ===
        switch_node = self.guide_tree.insert("", "end", text=" Switch", open=True)
        self.guide_tree.insert(switch_node, "end", text="   pili (expr) { kaso val: ... }")
        self.guide_tree.insert(switch_node, "end", text="   break = undang;")
        self.guide_tree.insert(switch_node, "end", text="   default = lain:")

        # 2. MAIN CONTENT AREA (Right Side)
        self.right_frame = tk.Frame(self, bg="#D9D9D9")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        # Title Header
        lbl_title = tk.Label(
            self.right_frame, text="JabaiScript", font=("Arial", 22, "bold"),
            bg="#D9D9D9", fg="#000000"
        )
        lbl_title.pack(pady=(5, 15))

        # Container para sa Source Code at Output Editors
        self.editors_frame = tk.Frame(self.right_frame, bg="#D9D9D9")
        self.editors_frame.pack(fill=tk.BOTH, expand=True)

        # --- LEFT EDITOR: Source Code ---
        self.source_container = tk.Frame(self.editors_frame, bg="#D9D9D9")
        self.source_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        lbl_source = tk.Label(
            self.source_container, text="Source Code", font=("Arial", 14),
            bg="#D9D9D9", fg="#000000"
        )
        lbl_source.pack(pady=(0, 5))

        self.txt_source = tk.Text(
            self.source_container, bg="black", fg="white",
            insertbackground="white", font=("Consolas", 12), relief=tk.FLAT
        )
        self.txt_source.pack(fill=tk.BOTH, expand=True)

        # --- RIGHT EDITOR: Output ---
        self.output_container = tk.Frame(self.editors_frame, bg="#D9D9D9")
        self.output_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        lbl_output = tk.Label(
            self.output_container, text="Output", font=("Arial", 14),
            bg="#D9D9D9", fg="#000000"
        )
        lbl_output.pack(pady=(0, 5))

        self.txt_output = tk.Text(
            self.output_container, bg="black", fg="white",
            font=("Consolas", 12), relief=tk.FLAT, state=tk.DISABLED
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)

        # 3. RUN BUTTON
        self.btn_run = tk.Button(
            self.right_frame, text="▶ RUN CODE", font=("Arial", 11, "bold"),
            bg="#4CAF50", fg="white", activebackground="#45a049",
            cursor="hand2", command=self._on_run
        )
        self.btn_run.pack(pady=10, fill=tk.X, padx=5)

    def _on_run(self):
        """Kukunin ang text sa Source Code, ipapa-process sa Compiler, at ipapakita sa Output."""
        code_input = self.txt_source.get("1.0", tk.END)
        result = self.compiler.run(code_input)

        # I-enable muna ang Text widget para makapag-insert ng text, tsaka i-disable ulit (Read-Only)
        self.txt_output.config(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, result)
        self.txt_output.config(state=tk.DISABLED)
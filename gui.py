# gui.py
import re
import tkinter as tk
from tkinter import ttk

from compiler import JabaiScriptCompiler
from keywords import GUIDE, KEYWORD_PHRASES, KEYWORDS, TYPES, LITERALS
from samples import SAMPLES

BG = "#D9D9D9"
SIDEBAR_BG = "#B0B0B0"

# One regex for syntax highlighting: multi-word phrases first, longest first.
_KW_WORDS = (
    [p for p, _ in sorted(KEYWORD_PHRASES, key=lambda p: -len(p[0].split()))]
    + sorted(KEYWORDS) + sorted(TYPES, key=len, reverse=True) + sorted(LITERALS)
)
_KW_PATTERN = re.compile(
    r"(?<![\w-])(?:" + "|".join(r"\s+".join(map(re.escape, w.split())) for w in _KW_WORDS)
    + r")(?![\w])")
_STRING_PATTERN = re.compile(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'')
_COMMENT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


class CompilerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("JabaiScript Compiler")
        self.geometry("1150x650")
        self.minsize(900, 450)
        self.configure(bg=BG)

        self.compiler = JabaiScriptCompiler()
        self.snippets = {}          # guide tree item id -> code to insert

        self._setup_styles()
        self._create_layout()
        self._load_sample(next(iter(SAMPLES)))

        self.bind("<Control-Return>", lambda e: self._on_run())
        self.bind("<F5>", lambda e: self._on_run())

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)

    # ------------------------------------------------------------------ layout
    def _create_layout(self):
        self._create_guide()
        self._create_workspace()

    def _create_guide(self):
        """LEFT: dictionary of coding words and their Bisaya equivalent."""
        self.left_frame = tk.Frame(self, bg=SIDEBAR_BG, width=340)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        self.left_frame.pack_propagate(False)

        tk.Label(self.left_frame, text="Guide", font=("Arial", 18, "bold"),
                 bg=SIDEBAR_BG, fg="#000000").pack(pady=(15, 0))
        tk.Label(self.left_frame, text="Double-click ang usa ka linya para ibutang sa code",
                 font=("Arial", 8), bg=SIDEBAR_BG, fg="#222222").pack(pady=(0, 8))

        tree_frame = tk.Frame(self.left_frame, bg=SIDEBAR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.guide_tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.guide_tree.yview)
        self.guide_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.guide_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.guide_tree.column("#0", width=300, stretch=True)

        # Built from keywords.GUIDE so the guide and the compiler never disagree.
        for title, is_open, rows in GUIDE:
            section = self.guide_tree.insert("", "end", text=f" {title}", open=is_open)
            for label, snippet in rows:
                item = self.guide_tree.insert(section, "end", text=f"   {label}")
                if snippet:
                    self.snippets[item] = snippet
        self.guide_tree.bind("<Double-1>", self._on_guide_double_click)

    def _create_workspace(self):
        """RIGHT: the Bisaya source code, and the program output."""
        self.right_frame = tk.Frame(self, bg=BG)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        tk.Label(self.right_frame, text="JabaiScript", font=("Arial", 22, "bold"),
                 bg=BG, fg="#000000").pack(pady=(5, 8))

        # Sample chooser
        bar = tk.Frame(self.right_frame, bg=BG)
        bar.pack(fill=tk.X, padx=5, pady=(0, 8))
        tk.Label(bar, text="Pili og sampol:", font=("Arial", 10), bg=BG).pack(side=tk.LEFT)
        self.sample_var = tk.StringVar()
        self.cmb_samples = ttk.Combobox(bar, textvariable=self.sample_var, state="readonly",
                                        values=list(SAMPLES), width=48)
        self.cmb_samples.pack(side=tk.LEFT, padx=8)
        self.cmb_samples.bind("<<ComboboxSelected>>",
                              lambda e: self._load_sample(self.sample_var.get()))
        tk.Button(bar, text="Clear", command=self._on_clear).pack(side=tk.LEFT)

        self.editors_frame = tk.Frame(self.right_frame, bg=BG)
        self.editors_frame.pack(fill=tk.BOTH, expand=True)

        # --- Source code ---
        self.source_container = tk.Frame(self.editors_frame, bg=BG)
        self.source_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(self.source_container, text="Source Code", font=("Arial", 14),
                 bg=BG, fg="#000000").pack(pady=(0, 5))
        self.txt_source = self._make_text(self.source_container, editable=True)
        self.txt_source.tag_configure("kw", foreground="#FFB454")
        self.txt_source.tag_configure("str", foreground="#9ECE6A")
        self.txt_source.tag_configure("cmt", foreground="#7A8290")
        self.txt_source.bind("<KeyRelease>", lambda e: self._highlight())

        # --- Output ---
        self.output_container = tk.Frame(self.editors_frame, bg=BG)
        self.output_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(self.output_container, text="Output", font=("Arial", 14),
                 bg=BG, fg="#000000").pack(pady=(0, 5))
        self.txt_output = self._make_text(self.output_container, editable=False)
        self.txt_output.tag_configure("error", foreground="#FF6B6B")

        self.btn_run = tk.Button(
            self.right_frame, text="▶ RUN CODE  (Ctrl+Enter)", font=("Arial", 11, "bold"),
            bg="#4CAF50", fg="white", activebackground="#45a049",
            cursor="hand2", command=self._on_run)
        self.btn_run.pack(pady=10, fill=tk.X, padx=5)

    def _make_text(self, parent, editable):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        text = tk.Text(frame, bg="black", fg="white", insertbackground="white",
                       font=("Consolas", 12), relief=tk.FLAT, wrap="none", undo=editable,
                       width=30, state=tk.NORMAL if editable else tk.DISABLED)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return text

    # ---------------------------------------------------------------- actions
    def _highlight(self):
        t = self.txt_source
        for tag in ("kw", "str", "cmt"):
            t.tag_remove(tag, "1.0", tk.END)
        code = t.get("1.0", tk.END)
        # keywords first; strings and comments are painted afterwards and win
        for tag, pattern in (("kw", _KW_PATTERN), ("str", _STRING_PATTERN),
                             ("cmt", _COMMENT_PATTERN)):
            for m in pattern.finditer(code):
                t.tag_add(tag, f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        t.tag_raise("str")
        t.tag_raise("cmt")

    def _load_sample(self, name):
        self.sample_var.set(name)
        self.txt_source.delete("1.0", tk.END)
        self.txt_source.insert("1.0", SAMPLES[name])
        self._highlight()
        self._set_output("")

    def _on_clear(self):
        self.sample_var.set("")
        self.txt_source.delete("1.0", tk.END)
        self._set_output("")

    def _on_guide_double_click(self, event):
        item = self.guide_tree.identify_row(event.y)
        snippet = self.snippets.get(item)
        if snippet:
            self.txt_source.insert(tk.INSERT, snippet)
            self.txt_source.focus_set()
            self._highlight()

    def _set_output(self, text, is_error=False):
        # The Output box is read-only: unlock, write, lock again.
        self.txt_output.config(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, text, "error" if is_error else "")
        self.txt_output.config(state=tk.DISABLED)

    def _on_run(self):
        """Take the Source Code, compile + run it, show the result in Output."""
        code = self.txt_source.get("1.0", tk.END)
        output, error = self.compiler.execute(code)
        self.txt_output.config(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)
        if output:
            self.txt_output.insert(tk.END, output + ("\n" if error else ""))
        if error:
            self.txt_output.insert(tk.END, error, "error")
        elif not output:
            self.txt_output.insert(tk.END, "Code executed successfully (No output).")
        self.txt_output.config(state=tk.DISABLED)

# compiler.py
"""JabaiScript / Bisaya compiler.

Pipeline:  source text --> Lexer --> Parser (AST) --> Interpreter

The whole program is lexed and parsed *before* anything runs, so syntax
errors are reported up front (like a real compiler) and a half-run program
never prints partial output for a typo on the last line.
"""
import re
from collections import namedtuple

from keywords import KEYWORD_PHRASES, KEYWORDS, TYPES, LITERALS

MAX_LOOP_STEPS = 100_000   # guard so an endless loop cannot freeze the GUI


# ===========================================================================
# Errors
# ===========================================================================
class BisayaError(Exception):
    kind = "Sayop"

    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self):
        where = f" (linya {self.line})" if self.line else ""
        return f"{self.kind}{where}: {self.message}"


class BisayaSyntaxError(BisayaError):
    kind = "Sayop sa pagsulat"


class BisayaRuntimeError(BisayaError):
    kind = "Sayop sa pag-run"


# ===========================================================================
# Lexer
# ===========================================================================
Token = namedtuple("Token", "type value line")

_PHRASES = [
    (re.compile(r"\s+".join(map(re.escape, phrase.split())) + r"(?!\w)"), tok)
    for phrase, tok in sorted(KEYWORD_PHRASES, key=lambda p: -len(p[0].split()))
]
_TINUOD_BAKAK = re.compile(r"tinuod-bakak(?!\w)")
_IDENT = re.compile(r"[A-Za-z_]\w*")
_NUMBER = re.compile(r"\d+\.\d+|\d+")
_OPS = ["==", "!=", ">=", "<=", "&&", "||", "++", "--",
        "+=", "-=", "*=", "/=", "%=",
        "+", "-", "*", "/", "%", "<", ">", "=", "!",
        "(", ")", "{", "}", "[", "]", ",", ";", ":", "."]
_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'", "0": "\0"}


def tokenize(src):
    tokens, i, line, n = [], 0, 1, len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
        elif c.isspace():
            i += 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            end = src.find("*/", i + 2)
            if end == -1:
                raise BisayaSyntaxError("Wala natapos ang /* komento */", line)
            line += src.count("\n", i, end)
            i = end + 2
        elif c in "\"'":
            i, text = _read_string(src, i, line)
            tokens.append(Token("STR", text, line))
        elif c.isdigit():
            m = _NUMBER.match(src, i)
            text = m.group()
            tokens.append(Token("NUM", float(text) if "." in text else int(text), line))
            i = m.end()
        elif c.isalpha() or c == "_":
            i = _read_word(src, i, line, tokens)
            line = 1 + src.count("\n", 0, i)   # a phrase may span lines
        else:
            for op in _OPS:
                if src.startswith(op, i):
                    tokens.append(Token(op, op, line))
                    i += len(op)
                    break
            else:
                raise BisayaSyntaxError(f"Dili kaila nga karakter '{c}'", line)
    tokens.append(Token("EOF", None, line))
    return tokens


def _read_string(src, i, line):
    quote, i, out = src[i], i + 1, []
    while i < len(src):
        c = src[i]
        if c == quote:
            return i + 1, "".join(out)
        if c == "\n":
            break
        if c == "\\" and i + 1 < len(src):
            i += 1
            out.append(_ESCAPES.get(src[i], src[i]))
        else:
            out.append(c)
        i += 1
    raise BisayaSyntaxError("Wala natapos ang estorya (kulang ang quote)", line)


def _read_word(src, i, line, tokens):
    """Read a keyword phrase, keyword, literal, type or identifier at src[i]."""
    for rx, tok in _PHRASES:
        m = rx.match(src, i)
        if m:
            tokens.append(Token(tok, m.group(), line))
            return m.end()
    m = _TINUOD_BAKAK.match(src, i)
    if m:
        tokens.append(Token("TYPE", "tinuod-bakak", line))
        return m.end()
    m = _IDENT.match(src, i)
    word = m.group()
    if word in KEYWORDS:
        tokens.append(Token(KEYWORDS[word], word, line))
    elif word in TYPES:
        tokens.append(Token("TYPE", word, line))
    elif word in LITERALS:
        tokens.append(Token("LIT", LITERALS[word], line))
    else:
        tokens.append(Token("ID", word, line))
    return m.end()


# ===========================================================================
# Parser  (recursive descent, builds a tiny AST of Node objects)
# ===========================================================================
class Node:
    def __init__(self, kind, line, **fields):
        self.kind = kind
        self.line = line
        self.__dict__.update(fields)


_ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%="}
_BINARY_LEVELS = [
    {"||"}, {"&&"}, {"==", "!="}, {"<", ">", "<=", ">="},
    {"+", "-"}, {"*", "/", "%"},
]


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    # -- token helpers ------------------------------------------------------
    def peek(self):
        return self.toks[self.pos]

    def next(self):
        tok = self.toks[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def accept(self, ttype):
        if self.peek().type == ttype:
            return self.next()
        return None

    def expect(self, ttype, what=None):
        tok = self.peek()
        if tok.type != ttype:
            found = "katapusan sa code" if tok.type == "EOF" else f"'{tok.value}'"
            raise BisayaSyntaxError(
                f"Gipaabot ang {what or repr(ttype)} apan nakita ang {found}", tok.line)
        return self.next()

    # -- program / statements ----------------------------------------------
    def parse_program(self):
        stmts = []
        while self.peek().type != "EOF":
            stmts.append(self.parse_statement())
        return Node("block", 1, body=stmts)

    def parse_block(self):
        line = self.expect("{", "'{'").line
        stmts = []
        while self.peek().type != "}":
            if self.peek().type == "EOF":
                raise BisayaSyntaxError("Kulang ang '}' sa katapusan", line)
            stmts.append(self.parse_statement())
        self.next()
        return Node("block", line, body=stmts)

    def parse_body(self):
        """A '{ ... }' block, or a single statement without braces."""
        if self.peek().type == "{":
            return self.parse_block()
        stmt = self.parse_statement()
        return Node("block", stmt.line, body=[stmt])

    def parse_statement(self):
        tok = self.peek()
        t = tok.type
        if t == "TYPE":
            return self.parse_decl(semicolon=True)
        if t == "IF":
            return self.parse_if()
        if t == "WHILE":
            return self.parse_while()
        if t == "DO":
            return self.parse_do()
        if t == "FOR":
            return self.parse_for()
        if t in ("FOR_IN", "FOREACH"):
            return self.parse_for_each()
        if t == "SWITCH":
            return self.parse_switch()
        if t in ("BREAK", "CONTINUE"):
            self.next()
            self.expect(";", "';' human sa '%s'" % tok.value)
            return Node(t.lower(), tok.line)
        if t == "{":
            return self.parse_block()
        if t in ("ELIF", "ELSE"):
            raise BisayaSyntaxError(
                f"'{tok.value}' kinahanglan naay 'kung' sa unahan", tok.line)
        if t in ("CASE", "DEFAULT"):
            raise BisayaSyntaxError(
                f"'{tok.value}' pwede ra sulod sa 'pili'", tok.line)
        if t == ";":
            self.next()
            return Node("block", tok.line, body=[])
        expr = self.parse_expr()
        self.expect(";", "';' sa katapusan sa pahayag")
        return Node("expr", tok.line, expr=expr)

    def parse_decl(self, semicolon):
        typ = self.next()
        name = self.expect("ID", "ngalan sa variable")
        init = self.parse_expr() if self.accept("=") else None
        if semicolon:
            self.expect(";", "';' sa katapusan sa pahayag")
        return Node("decl", typ.line, vtype=typ.value, name=name.value, init=init)

    def parse_paren_expr(self):
        self.expect("(", "'('")
        expr = self.parse_expr()
        self.expect(")", "')'")
        return expr

    def parse_if(self):
        line = self.next().line
        branches = [(self.parse_paren_expr(), self.parse_body())]
        while self.peek().type == "ELIF":
            self.next()
            branches.append((self.parse_paren_expr(), self.parse_body()))
        else_body = self.parse_body() if self.accept("ELSE") else None
        return Node("if", line, branches=branches, else_body=else_body)

    def parse_while(self):
        line = self.next().line
        cond = self.parse_paren_expr()
        return Node("while", line, cond=cond, body=self.parse_body())

    def parse_do(self):
        line = self.next().line
        body = self.parse_body()
        self.expect("WHILE", "'habang' human sa 'gawin { ... }'")
        cond = self.parse_paren_expr()
        self.accept(";")
        return Node("do", line, cond=cond, body=body)

    def parse_for(self):
        line = self.next().line
        self.expect("(", "'('")
        init = cond = update = None
        if self.peek().type != ";":
            if self.peek().type == "TYPE":
                init = self.parse_decl(semicolon=False)
            else:
                e = self.parse_expr()
                init = Node("expr", e.line, expr=e)
        self.expect(";", "';' human sa sinugdanan sa 'para sa'")
        if self.peek().type != ";":
            cond = self.parse_expr()
        self.expect(";", "';' human sa kondisyon sa 'para sa'")
        if self.peek().type != ")":
            update = self.parse_expr()
        self.expect(")", "')'")
        return Node("for", line, init=init, cond=cond, update=update,
                    body=self.parse_body())

    def parse_for_each(self):
        tok = self.next()
        self.expect("(", "'('")
        vtype = self.next().value if self.peek().type == "TYPE" else None
        var = self.expect("ID", "ngalan sa variable sa loop").value
        index = self.expect("ID", "ngalan sa index").value if self.accept(",") else None
        self.expect(":", "':' tali sa variable ug sa tapok")
        iterable = self.parse_expr()
        self.expect(")", "')'")
        kind = "for_in" if tok.type == "FOR_IN" else "foreach"
        return Node(kind, tok.line, vtype=vtype, var=var, index=index,
                    iterable=iterable, body=self.parse_body())

    def parse_switch(self):
        line = self.next().line
        subject = self.parse_paren_expr()
        self.expect("{", "'{'")
        cases = []                      # [(value_expr | None for default, [stmts])]
        while self.peek().type != "}":
            tok = self.peek()
            if tok.type == "CASE":
                self.next()
                value = self.parse_expr()
            elif tok.type == "DEFAULT":
                self.next()
                value = None
            else:
                found = "katapusan sa code" if tok.type == "EOF" else f"'{tok.value}'"
                raise BisayaSyntaxError(
                    f"Sulod sa 'pili', gipaabot ang 'kaso' o 'lain' apan nakita ang {found}",
                    tok.line)
            self.expect(":", "':' human sa kaso")
            stmts = []
            while self.peek().type not in ("CASE", "DEFAULT", "}", "EOF"):
                stmts.append(self.parse_statement())
            cases.append((value, stmts))
        self.expect("}", "'}'")
        return Node("switch", line, subject=subject, cases=cases)

    # -- expressions --------------------------------------------------------
    def parse_expr(self):
        left = self.parse_binary(0)
        tok = self.peek()
        if tok.type in _ASSIGN_OPS:
            if left.kind not in ("var", "index", "member"):
                raise BisayaSyntaxError("Dili pwede butangan ang wala sa '='", tok.line)
            self.next()
            return Node("assign", tok.line, target=left, op=tok.type,
                        value=self.parse_expr())
        return left

    def parse_binary(self, level):
        if level == len(_BINARY_LEVELS):
            return self.parse_unary()
        left = self.parse_binary(level + 1)
        while self.peek().type in _BINARY_LEVELS[level]:
            op = self.next()
            right = self.parse_binary(level + 1)
            left = Node("binary", op.line, op=op.type, left=left, right=right)
        return left

    def parse_unary(self):
        tok = self.peek()
        if tok.type in ("!", "-", "+"):
            self.next()
            return Node("unary", tok.line, op=tok.type, operand=self.parse_unary())
        if tok.type in ("++", "--"):
            self.next()
            target = self.parse_unary()
            self._check_lvalue(target, tok)
            return Node("update", tok.line, op=tok.type, target=target, prefix=True)
        return self.parse_postfix()

    def _check_lvalue(self, node, tok):
        if node.kind not in ("var", "index", "member"):
            raise BisayaSyntaxError(f"Dili magamit ang '{tok.type}' dinhi", tok.line)

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            tok = self.peek()
            if tok.type == "(" and node.kind == "var":
                self.next()
                args = []
                if self.peek().type != ")":
                    args.append(self.parse_expr())
                    while self.accept(","):
                        args.append(self.parse_expr())
                self.expect(")", "')'")
                node = Node("call", tok.line, name=node.name, args=args)
            elif tok.type == "[":
                self.next()
                idx = self.parse_expr()
                self.expect("]", "']'")
                node = Node("index", tok.line, obj=node, index=idx)
            elif tok.type == ".":
                self.next()
                key = self.expect("ID", "ngalan human sa '.'")
                node = Node("member", tok.line, obj=node, key=key.value)
            elif tok.type in ("++", "--"):
                self._check_lvalue(node, tok)
                self.next()
                node = Node("update", tok.line, op=tok.type, target=node, prefix=False)
            else:
                return node

    def parse_primary(self):
        tok = self.next()
        t = tok.type
        if t in ("NUM", "STR", "LIT"):
            return Node("lit", tok.line, value=tok.value)
        if t == "ID":
            return Node("var", tok.line, name=tok.value)
        if t == "(":
            expr = self.parse_expr()
            self.expect(")", "')'")
            return expr
        if t == "[":
            items = []
            while self.peek().type != "]":
                items.append(self.parse_expr())
                if not self.accept(","):
                    break
            self.expect("]", "']'")
            return Node("list", tok.line, items=items)
        if t == "{":
            pairs = []
            while self.peek().type != "}":
                key = self.next()
                if key.type not in ("ID", "STR"):
                    raise BisayaSyntaxError("Ngalan sa yawe ang gipaabot sa hugpong", key.line)
                self.expect(":", "':' human sa yawe")
                pairs.append((key.value, self.parse_expr()))
                if not self.accept(","):
                    break
            self.expect("}", "'}'")
            return Node("object", tok.line, pairs=pairs)
        found = "katapusan sa code" if t == "EOF" else f"'{tok.value}'"
        raise BisayaSyntaxError(f"Wala gipaabot nga {found}", tok.line)


# ===========================================================================
# Interpreter
# ===========================================================================
class _Break(Exception):
    def __init__(self, line=None):
        self.line = line


class _Continue(Exception):
    def __init__(self, line=None):
        self.line = line


def fmt(value, nested=False):
    """How a value is displayed by printa()."""
    if value is None:
        return "walaBai"
    if value is True:
        return "tinuod"
    if value is False:
        return "bakak"
    if isinstance(value, str):
        return f'"{value}"' if nested else value
    if isinstance(value, list):
        return "[" + ", ".join(fmt(v, True) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {fmt(v, True)}" for k, v in value.items()) + "}"
    return str(value)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _type_name(v):
    if v is None:
        return "walaBai"
    if isinstance(v, bool):
        return "tinuod-bakak"
    if isinstance(v, int):
        return "tibuok"
    if isinstance(v, float):
        return "bahin"
    if isinstance(v, str):
        return "estorya"
    if isinstance(v, list):
        return "tapok"
    return "hugpong"


_DEFAULTS = {"tibuok": 0, "bahin": 0.0, "estorya": "", "tinuod-bakak": False,
             "titik": None, "tapok": list, "hugpong": dict}


class Interpreter:
    def __init__(self):
        self.out = []
        self.scopes = [{}]
        self.steps = 0

    # -- scopes -------------------------------------------------------------
    def lookup(self, name, line):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise BisayaRuntimeError(f"Wala nahibaloi ang variable '{name}'", line)

    def declare(self, name, vtype, value, line):
        if name in self.scopes[-1]:
            raise BisayaRuntimeError(f"Ang variable '{name}' gideklara na", line)
        self.scopes[-1][name] = [vtype, self.coerce(vtype, value, name, line)]

    def coerce(self, vtype, value, name, line):
        if vtype is None:                       # untyped loop variable
            return value
        ok = {
            "tibuok": isinstance(value, int) and not isinstance(value, bool),
            "bahin": _is_num(value),
            "estorya": value is None or isinstance(value, str),
            "titik": value is None or (isinstance(value, str) and len(value) == 1),
            "tinuod-bakak": isinstance(value, bool),
            "tapok": value is None or isinstance(value, list),
            "hugpong": value is None or isinstance(value, dict),
        }[vtype]
        if not ok:
            raise BisayaRuntimeError(
                f"Ang '{name}' kay {vtype}, apan gibutang ang {_type_name(value)} "
                f"({fmt(value, True)})", line)
        return float(value) if vtype == "bahin" else value

    def tick(self, line):
        self.steps += 1
        if self.steps > MAX_LOOP_STEPS:
            raise BisayaRuntimeError(
                f"Sobra sa {MAX_LOOP_STEPS:,} ka balik sa loop - tingali walay katapusan?",
                line)

    # -- statements ---------------------------------------------------------
    def run(self, program):
        for stmt in program.body:
            self.exec(stmt)

    def exec(self, node):
        getattr(self, "exec_" + node.kind)(node)

    def exec_block(self, node, new_scope=True):
        if new_scope:
            self.scopes.append({})
        try:
            for stmt in node.body:
                self.exec(stmt)
        finally:
            if new_scope:
                self.scopes.pop()

    def exec_expr(self, node):
        self.eval(node.expr)

    def exec_decl(self, node):
        if node.init is not None:
            value = self.eval(node.init)
        else:
            value = _DEFAULTS[node.vtype]
            value = value() if callable(value) else value
        self.declare(node.name, node.vtype, value, node.line)

    def exec_if(self, node):
        for cond, body in node.branches:
            if self.eval(cond):
                return self.exec(body)
        if node.else_body is not None:
            self.exec(node.else_body)

    def run_body(self, body):
        """Run a loop body. Returns True if the loop should stop (undang)."""
        try:
            self.exec(body)
        except _Break:
            return True
        except _Continue:
            pass
        return False

    def exec_while(self, node):
        while self.eval(node.cond):
            self.tick(node.line)
            if self.run_body(node.body):
                break

    def exec_do(self, node):
        while True:
            self.tick(node.line)
            if self.run_body(node.body):
                break
            if not self.eval(node.cond):
                break

    def exec_for(self, node):
        self.scopes.append({})
        try:
            if node.init is not None:
                self.exec(node.init)
            while node.cond is None or self.eval(node.cond):
                self.tick(node.line)
                if self.run_body(node.body):
                    break
                if node.update is not None:
                    self.eval(node.update)
        finally:
            self.scopes.pop()

    def _iterate(self, node):
        """Return ([(index_or_key, value), ...], is_hugpong) for the loop."""
        coll = self.eval(node.iterable)
        if isinstance(coll, (list, str)):
            return list(enumerate(coll)), False
        if isinstance(coll, dict):
            return list(coll.items()), True
        raise BisayaRuntimeError(
            f"Dili ma-loop ang {_type_name(coll)}; tapok, estorya o hugpong ra", node.line)

    def _each(self, node, keys_for_hugpong):
        pairs, is_hugpong = self._iterate(node)
        for key, value in pairs:
            self.tick(node.line)
            self.scopes.append({})
            try:
                item = key if (keys_for_hugpong and is_hugpong) else value
                self.declare(node.var, node.vtype, item, node.line)
                if node.index:
                    self.declare(node.index, None, key, node.line)
                stop = self.run_body(node.body)
            finally:
                self.scopes.pop()
            if stop:
                break

    def exec_for_in(self, node):
        # sa matag usa nga naa sa sulod: values of a tapok/estorya, keys of a hugpong
        self._each(node, keys_for_hugpong=True)

    def exec_foreach(self, node):
        # sa matag usa: always the values (optional second name = index / key)
        self._each(node, keys_for_hugpong=False)

    def exec_switch(self, node):
        subject = self.eval(node.subject)
        start = None
        for i, (value, _) in enumerate(node.cases):
            if value is not None and self._equals(subject, self.eval(value)):
                start = i
                break
        if start is None:
            start = next((i for i, (v, _) in enumerate(node.cases) if v is None), None)
        if start is None:
            return
        self.scopes.append({})
        try:
            for _, stmts in node.cases[start:]:      # falls through until 'undang'
                for stmt in stmts:
                    self.exec(stmt)
        except _Break:
            pass
        finally:
            self.scopes.pop()

    def exec_break(self, node):
        raise _Break(node.line)

    def exec_continue(self, node):
        raise _Continue(node.line)

    # -- expressions --------------------------------------------------------
    def eval(self, node):
        return getattr(self, "eval_" + node.kind)(node)

    def eval_lit(self, node):
        return node.value

    def eval_var(self, node):
        return self.lookup(node.name, node.line)[1]

    def eval_list(self, node):
        return [self.eval(i) for i in node.items]

    def eval_object(self, node):
        return {k: self.eval(v) for k, v in node.pairs}

    def eval_unary(self, node):
        v = self.eval(node.operand)
        if node.op == "!":
            return not v
        if not _is_num(v):
            raise BisayaRuntimeError(f"Dili magamit ang '{node.op}' sa {_type_name(v)}", node.line)
        return -v if node.op == "-" else v

    def eval_binary(self, node):
        op = node.op
        if op == "&&":
            return bool(self.eval(node.left)) and bool(self.eval(node.right))
        if op == "||":
            return bool(self.eval(node.left)) or bool(self.eval(node.right))
        return self.binary(op, self.eval(node.left), self.eval(node.right), node.line)

    @staticmethod
    def _equals(a, b):
        if isinstance(a, bool) != isinstance(b, bool):
            return False
        return a == b

    def binary(self, op, a, b, line):
        if op == "==":
            return self._equals(a, b)
        if op == "!=":
            return not self._equals(a, b)
        if op == "+" and (isinstance(a, str) or isinstance(b, str)):
            return fmt(a) + fmt(b)
        if op == "+" and isinstance(a, list) and isinstance(b, list):
            return a + b
        if op in ("<", ">", "<=", ">=") and isinstance(a, str) and isinstance(b, str):
            pass
        elif not (_is_num(a) and _is_num(b)):
            raise BisayaRuntimeError(
                f"Dili magamit ang '{op}' sa {_type_name(a)} ug {_type_name(b)}", line)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op in ("/", "%"):
            if b == 0:
                raise BisayaRuntimeError("Dili mahimo ang pagbahin sa zero", line)
            both_int = isinstance(a, int) and isinstance(b, int)
            if op == "/":
                if both_int:                       # tibuok / tibuok = tibuok
                    q = abs(a) // abs(b)
                    return q if (a < 0) == (b < 0) else -q
                return a / b
            if both_int:                           # sign follows the dividend
                r = abs(a) % abs(b)
                return -r if a < 0 else r
            return a - b * int(a / b)
        return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]

    def eval_index(self, node):
        obj, idx = self.eval(node.obj), self.eval(node.index)
        if isinstance(obj, (list, str)):
            if not (isinstance(idx, int) and not isinstance(idx, bool)):
                raise BisayaRuntimeError("Tibuok ang kinahanglan nga index", node.line)
            if not 0 <= idx < len(obj):
                raise BisayaRuntimeError(
                    f"Ang index {idx} gawas sa sakup (gidak-on: {len(obj)})", node.line)
            return obj[idx]
        if isinstance(obj, dict):
            return obj.get(idx)
        raise BisayaRuntimeError(f"Dili ma-index ang {_type_name(obj)}", node.line)

    def eval_member(self, node):
        obj = self.eval(node.obj)
        if not isinstance(obj, dict):
            raise BisayaRuntimeError(f"Ang {_type_name(obj)} walay '.{node.key}'", node.line)
        return obj.get(node.key)

    def eval_call(self, node):
        args = [self.eval(a) for a in node.args]
        name = node.name
        if name == "printa":
            self.out.append(" ".join(fmt(a) for a in args))
            return None
        if name == "gitas":
            if len(args) != 1 or not isinstance(args[0], (list, str, dict)):
                raise BisayaRuntimeError("gitas() nagkinahanglan og usa ka tapok, estorya o hugpong", node.line)
            return len(args[0])
        if name == "idugang":
            if len(args) != 2 or not isinstance(args[0], list):
                raise BisayaRuntimeError("idugang(tapok, bili) ang husto nga porma", node.line)
            args[0].append(args[1])
            return None
        raise BisayaRuntimeError(f"Wala nahibaloi ang function '{name}'", node.line)

    def _store(self, target, value):
        if target.kind == "var":
            cell = self.lookup(target.name, target.line)
            cell[1] = self.coerce(cell[0], value, target.name, target.line)
            return cell[1]
        if target.kind == "index":
            obj, idx = self.eval(target.obj), self.eval(target.index)
            if isinstance(obj, list):
                if not (isinstance(idx, int) and 0 <= idx < len(obj)):
                    raise BisayaRuntimeError(f"Ang index {fmt(idx)} gawas sa sakup", target.line)
                obj[idx] = value
            elif isinstance(obj, dict):
                obj[idx] = value
            else:
                raise BisayaRuntimeError(f"Dili ma-index ang {_type_name(obj)}", target.line)
            return value
        obj = self.eval(target.obj)
        if not isinstance(obj, dict):
            raise BisayaRuntimeError(f"Ang {_type_name(obj)} walay '.{target.key}'", target.line)
        obj[target.key] = value
        return value

    def eval_assign(self, node):
        value = self.eval(node.value)
        if node.op != "=":
            value = self.binary(node.op[0], self.eval(node.target), value, node.line)
        return self._store(node.target, value)

    def eval_update(self, node):
        old = self.eval(node.target)
        if not _is_num(old):
            raise BisayaRuntimeError(f"Dili magamit ang '{node.op}' sa {_type_name(old)}", node.line)
        new = self._store(node.target, old + (1 if node.op == "++" else -1))
        return new if node.prefix else old


# ===========================================================================
# Public API used by the GUI
# ===========================================================================
class JabaiScriptCompiler:
    """Compiles and runs JabaiScript (Bisaya keyword) source code."""

    def compile(self, code: str) -> Node:
        return Parser(tokenize(code)).parse_program()

    def execute(self, code: str):
        """Returns (output_text, error_text_or_None)."""
        if not code.strip():
            return "", "Error: Empty code block."
        try:
            program = self.compile(code)
        except BisayaError as err:
            return "", str(err)
        interp = Interpreter()
        try:
            interp.run(program)
        except BisayaError as err:
            return "\n".join(interp.out), str(err)
        except (_Break, _Continue) as stray:
            word = "undang" if isinstance(stray, _Break) else "padayon"
            where = f" (linya {stray.line})" if stray.line else ""
            return "\n".join(interp.out), (
                f"{BisayaRuntimeError.kind}{where}: "
                f"'{word}' pwede ra sulod sa loop" + (" o pili" if word == "undang" else ""))
        except RecursionError:
            return "\n".join(interp.out), "Sayop sa pag-run: sobra ka lawom ang mga ekspresyon"
        return "\n".join(interp.out), None

    def run(self, code: str) -> str:
        output, error = self.execute(code)
        if error:
            return f"{output}\n{error}" if output else error
        return output or "Code executed successfully (No output)."

# keywords.py
"""Single source of truth for the Bisaya keywords.

Both the compiler (lexer/parser) and the GUI (guide panel, syntax
highlighting) read from here, so adding a keyword in one place updates both.
"""

# ---------------------------------------------------------------------------
# Multi-word keywords. The lexer tries these first, longest phrase first,
# so "sa matag usa nga naa sa sulod" is not mistaken for "sa matag usa".
# ---------------------------------------------------------------------------
KEYWORD_PHRASES = [
    ("sa matag usa nga naa sa sulod", "FOR_IN"),   # for in / for of
    ("sa matag usa", "FOREACH"),                   # for each
    ("para sa", "FOR"),                            # for
    ("kaha kung", "ELIF"),                         # else if
    ("kung dili", "ELSE"),                         # else
]

# ---------------------------------------------------------------------------
# Single-word keywords
# ---------------------------------------------------------------------------
KEYWORDS = {
    "kung": "IF",
    "habang": "WHILE",
    "gawin": "DO",
    "undang": "BREAK",
    "padayon": "CONTINUE",
    "pili": "SWITCH",
    "kaso": "CASE",
    "lain": "DEFAULT",
    "default": "DEFAULT",      # old spelling kept so existing programs still run
}

# Datatype keywords
TYPES = {
    "tibuok",          # int
    "bahin",           # double
    "estorya",         # string
    "tinuod-bakak",    # boolean
    "titik",           # char
    "tapok",           # array / list
    "hugpong",         # object
}

# Literal keywords
LITERALS = {
    "tinuod": True,    # true
    "bakak": False,    # false
    "walaBai": None,   # null
}

# Built-in functions
BUILTINS = {
    "printa": "print",
    "gitas": "length",
    "idugang": "append to a tapok",
}

# ---------------------------------------------------------------------------
# GUIDE shown in the left panel.
# (section title, open by default, [(row label, snippet inserted on double-click)])
# A snippet of None means the row is informational only.
# ---------------------------------------------------------------------------
GUIDE = [
    ("Datatype", True, [
        ("int = tibuok", "tibuok edad = 18;\n"),
        ("double = bahin", "bahin presyo = 9.75;\n"),
        ("string = estorya", 'estorya ngalan = "Juan";\n'),
        ("boolean = tinuod-bakak", "tinuod-bakak oo = tinuod;\n"),
        ("char = titik", "titik grado = 'A';\n"),
        ("array/list = tapok", "tapok numero = [1, 2, 3];\n"),
        ("object = hugpong", 'hugpong tawo = {ngalan: "Ana", edad: 20};\n'),
        ("null = walaBai", "estorya wala = walaBai;\n"),
        ("true = tinuod   false = bakak", None),
    ]),
    ("If-else", False, [
        ("if = kung",
         "kung (edad >= 18) {\n    printa(\"Hamtong na\");\n}\n"),
        ("else if = kaha kung",
         "kaha kung (edad >= 13) {\n    printa(\"Tin-edyer\");\n}\n"),
        ("else = kung dili",
         "kung dili {\n    printa(\"Bata pa\");\n}\n"),
    ]),
    ("Loops", True, [
        ("for = para sa",
         "para sa (tibuok i = 1; i <= 5; i++) {\n    printa(i);\n}\n"),
        ("for in / for of = sa matag usa nga naa sa sulod",
         "sa matag usa nga naa sa sulod (estorya p : prutas) {\n"
         "    printa(p);\n}\n"),
        ("for each = sa matag usa",
         "sa matag usa (estorya p, i : prutas) {\n"
         "    printa(i + \": \" + p);\n}\n"),
        ("while = habang",
         "tibuok n = 3;\nhabang (n > 0) {\n    printa(n);\n    n--;\n}\n"),
        ("do = gawin",
         "tibuok k = 0;\ngawin {\n    printa(k);\n    k++;\n} habang (k < 3);\n"),
        ("break = undang", "undang;\n"),
        ("continue = padayon", "padayon;\n"),
    ]),
    ("Switch", False, [
        ("switch = pili",
         "pili (adlaw) {\n    kaso 1:\n        printa(\"Lunes\");\n"
         "        undang;\n    lain:\n        printa(\"Laing adlaw\");\n}\n"),
        ("case = kaso", None),
        ("default = lain", None),
        ("break = undang", "undang;\n"),
    ]),
    ("Operators", False, [
        ("and = &&   or = ||   not = !", None),
        ("== != < > <= >=", None),
        ("+  -  *  /  %   (tibuok / tibuok = tibuok)", None),
        ("+=  -=  *=  /=  %=  ++  --", None),
    ]),
    ("Built-in", False, [
        ("print = printa(...)", 'printa("Kumusta, Kalibutan!");\n'),
        ("length = gitas(x)", "printa(gitas(prutas));\n"),
        ("push = idugang(tapok, x)", 'idugang(prutas, "ubas");\n'),
        ("comment = //  o  /* ... */", None),
    ]),
]

# test_compiler.py  -- run with:  python -m unittest -v
import unittest

from compiler import JabaiScriptCompiler

C = JabaiScriptCompiler()


def out(code):
    output, error = C.execute(code)
    assert error is None, error
    return output


def err(code):
    output, error = C.execute(code)
    assert error is not None, "expected an error"
    return error


class Basics(unittest.TestCase):
    def test_declarations_and_print(self):
        self.assertEqual(out('tibuok x = 5; bahin y = 2.5; estorya s = "hi";'
                             'printa(x); printa(y); printa(s);'), "5\n2.5\nhi")

    def test_all_datatypes(self):
        code = '''
        tibuok a = 1; bahin b = 2; estorya c = "x"; tinuod-bakak d = tinuod;
        titik e = 'z'; tapok f = [1, "a"]; hugpong g = {k: 1}; estorya h = walaBai;
        printa(a, b, c, d, e, f, g, h);'''
        self.assertEqual(out(code), '1 2.0 x tinuod z [1, "a"] {k: 1} walaBai')

    def test_type_checking(self):
        self.assertIn("tibuok", err('tibuok x = "abc";'))
        self.assertIn("tibuok", err('tibuok x = 1; x = 2.5;'))
        self.assertIn("titik", err("titik t = 'ab';"))

    def test_arithmetic(self):
        self.assertEqual(out("printa(7 / 2, -7 / 2, 7 % 3, -7 % 3, 7.0 / 2, 2 + 3 * 4);"),
                         "3 -3 1 -1 3.5 14")

    def test_string_concat(self):
        self.assertEqual(out('printa("n=" + 3 + tinuod);'), "n=3tinuod")

    def test_division_by_zero(self):
        self.assertIn("zero", err("printa(1 / 0);"))

    def test_undefined_variable_reports_line(self):
        e = err("tibuok a = 1;\nprinta(b);")
        self.assertIn("linya 2", e)
        self.assertIn("'b'", e)

    def test_syntax_error_runs_nothing(self):
        output, error = C.execute('printa("a");\nprinta("b")')
        self.assertEqual(output, "")
        self.assertIn("Sayop sa pagsulat", error)

    def test_comments(self):
        self.assertEqual(out("// hi\n/* multi\nline */ printa(1); // end"), "1")

    def test_empty(self):
        self.assertEqual(C.run("   "), "Error: Empty code block.")
        self.assertEqual(C.run("tibuok x = 1;"), "Code executed successfully (No output).")


class IfElse(unittest.TestCase):
    PROG = '''
    tibuok n = %d;
    kung (n > 10) { printa("dako"); }
    kaha kung (n > 5) { printa("tunga"); }
    kung dili { printa("gamay"); }
    '''

    def test_chain(self):
        self.assertEqual(out(self.PROG % 20), "dako")
        self.assertEqual(out(self.PROG % 7), "tunga")
        self.assertEqual(out(self.PROG % 1), "gamay")

    def test_closing_brace_on_same_line(self):
        code = 'tibuok n = 1;\nkung (n == 2) {\n printa("a");\n} kaha kung (n == 1) {\n printa("b");\n} kung dili {\n printa("c");\n}'
        self.assertEqual(out(code), "b")

    def test_nested_and_logic(self):
        code = '''tibuok a = 3; tibuok b = 4;
        kung (a < b && !(a == b)) { kung (a == 3 || b == 0) { printa("ok"); } }'''
        self.assertEqual(out(code), "ok")

    def test_stray_else(self):
        self.assertIn("kung", err("kung dili { printa(1); }"))


class Loops(unittest.TestCase):
    def test_para_sa(self):
        self.assertEqual(out("para sa (tibuok i = 1; i <= 3; i++) { printa(i); }"), "1\n2\n3")

    def test_para_sa_scope(self):
        self.assertIn("'i'", err("para sa (tibuok i = 0; i < 1; i++) { } printa(i);"))

    def test_habang(self):
        self.assertEqual(out("tibuok n = 3; habang (n > 0) { printa(n); n--; }"), "3\n2\n1")

    def test_gawin_runs_at_least_once(self):
        self.assertEqual(out("tibuok k = 10; gawin { printa(k); k++; } habang (k < 3);"), "10")

    def test_gawin_habang(self):
        self.assertEqual(out("tibuok k = 0; gawin { printa(k); k++; } habang (k < 3);"), "0\n1\n2")

    def test_undang(self):
        self.assertEqual(out("para sa (tibuok i = 0; i < 10; i++) { kung (i == 3) { undang; } printa(i); }"),
                         "0\n1\n2")

    def test_padayon(self):
        self.assertEqual(out("para sa (tibuok i = 0; i < 5; i++) { kung (i % 2 == 0) { padayon; } printa(i); }"),
                         "1\n3")

    def test_padayon_in_while_still_updates(self):
        code = "tibuok i = 0; habang (i < 5) { i++; kung (i == 2) { padayon; } printa(i); }"
        self.assertEqual(out(code), "1\n3\n4\n5")

    def test_undang_only_exits_inner_loop(self):
        code = '''para sa (tibuok i = 0; i < 2; i++) {
            para sa (tibuok j = 0; j < 5; j++) { kung (j == 1) { undang; } printa(i, j); } }'''
        self.assertEqual(out(code), "0 0\n1 0")

    def test_for_in_list(self):
        code = 'tapok p = ["a", "b"]; sa matag usa nga naa sa sulod (estorya x : p) { printa(x); }'
        self.assertEqual(out(code), "a\nb")

    def test_for_in_hugpong_gives_keys(self):
        code = 'hugpong h = {x: 1, y: 2}; sa matag usa nga naa sa sulod (k : h) { printa(k); }'
        self.assertEqual(out(code), "x\ny")

    def test_for_in_string(self):
        self.assertEqual(out('sa matag usa nga naa sa sulod (titik c : "abc") { printa(c); }'), "a\nb\nc")

    def test_foreach_with_index(self):
        code = 'tapok p = [10, 20]; sa matag usa (tibuok v, i : p) { printa(i + ":" + v); }'
        self.assertEqual(out(code), "0:10\n1:20")

    def test_foreach_hugpong_values_and_keys(self):
        code = 'hugpong h = {x: 1, y: 2}; sa matag usa (v, k : h) { printa(k, v); }'
        self.assertEqual(out(code), "x 1\ny 2")

    def test_foreach_break_continue(self):
        code = '''tapok n = [1, 2, 3, 4, 5];
        sa matag usa (tibuok v : n) { kung (v == 2) { padayon; } kung (v == 4) { undang; } printa(v); }'''
        self.assertEqual(out(code), "1\n3")

    def test_loop_variable_type_checked(self):
        self.assertIn("tibuok", err('sa matag usa (tibuok v : ["a"]) { }'))

    def test_loop_over_non_collection(self):
        self.assertIn("Dili ma-loop", err("sa matag usa (v : 5) { }"))

    def test_phrase_across_newline_and_spacing(self):
        code = 'tapok p = [1];\nsa   matag\nusa nga naa sa sulod (v : p) { printa(v); }'
        self.assertEqual(out(code), "1")

    def test_endless_loop_is_stopped(self):
        self.assertIn("walay katapusan", err("habang (tinuod) { }"))

    def test_loop_without_braces(self):
        self.assertEqual(out("para sa (tibuok i = 0; i < 2; i++) printa(i);"), "0\n1")

    def test_break_outside_loop(self):
        self.assertIn("linya 2", err('printa(1);\nundang;'))
        self.assertIn("pwede ra sulod sa loop", err("padayon;"))
        self.assertEqual(out("pili (1) { kaso 1: undang; }"), "")   # fine in a switch


class Switch(unittest.TestCase):
    PROG = '''pili (%s) {
        kaso 1: printa("usa"); undang;
        kaso "b": printa("bi"); undang;
        kaso 3: printa("tulo");
        kaso 4: printa("upat"); undang;
        lain: printa("lain");
    }'''

    def test_cases(self):
        self.assertEqual(out(self.PROG % "1"), "usa")
        self.assertEqual(out(self.PROG % '"b"'), "bi")
        self.assertEqual(out(self.PROG % "9"), "lain")

    def test_fallthrough(self):
        self.assertEqual(out(self.PROG % "3"), "tulo\nupat")

    def test_variable_subject(self):
        self.assertEqual(out("tibuok d = 1; " + self.PROG % "d"), "usa")

    def test_break_in_loop_inside_switch(self):
        code = '''para sa (tibuok i = 0; i < 3; i++) { pili (i) { kaso 1: undang; lain: printa(i); } }'''
        self.assertEqual(out(code), "0\n2")


class Collections(unittest.TestCase):
    def test_index_and_assign(self):
        self.assertEqual(out("tapok a = [1, 2]; a[0] = 9; printa(a[0], gitas(a));"), "9 2")

    def test_idugang(self):
        self.assertEqual(out('tapok a = []; idugang(a, 1); idugang(a, "x"); printa(a);'), '[1, "x"]')

    def test_hugpong_member(self):
        self.assertEqual(out('hugpong p = {n: "Ana"}; p.edad = 5; printa(p.n, p.edad, p);'),
                         'Ana 5 {n: "Ana", edad: 5}')

    def test_index_out_of_range(self):
        self.assertIn("gawas sa sakup", err("tapok a = [1]; printa(a[3]);"))

    def test_compound_assign(self):
        self.assertEqual(out("tibuok x = 2; x += 3; x *= 2; x -= 1; printa(x);"), "9")


class OriginalProgram(unittest.TestCase):
    """Programs written for the old line-based interpreter still work."""

    def test_old_if_else_and_switch(self):
        code = '''
        tibuok edad = 20;
        kung (edad >= 18) {
            printa("Hamtong");
        } kung dili {
            printa("Bata");
        }
        tibuok a = 2;
        pili (a) {
            kaso 1:
                printa("Usa");
                undang;
            kaso 2:
                printa("Duha");
                undang;
            lain:
                printa("Lain");
        }'''
        self.assertEqual(out(code), "Hamtong\nDuha")


if __name__ == "__main__":
    unittest.main()

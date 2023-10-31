import unittest

from crdesigner.verification_repairing.verification.hol.parser.parser import Parser


class TestParser(unittest.TestCase):

    def test_binary_expr(self):
        formula = 'true -> false'
        self.assertEqual('(true -> false)', Parser.parse(formula).to_string())

        formula = 'true <-> false'
        self.assertEqual('(true <-> false)', Parser.parse(formula).to_string())

    def test_nary_expr(self):
        formula = 'true & true & true'
        self.assertEqual('(true & true & true)', Parser.parse(formula).to_string())

        formula = 'true | false | false'
        self.assertEqual('(true | false | false)', Parser.parse(formula).to_string())

        formula = 'true ^ false ^ false'
        self.assertEqual('(true ^ false ^ false)', Parser.parse(formula).to_string())

    def test_unary_expr(self):
        formula = '!(true)'
        self.assertEqual('!(true)', Parser.parse(formula).to_string())

        formula = '!(P(x))'
        self.assertEqual('!(P(x))', Parser.parse(formula).to_string())

        formula = 'A x in D. P(x)'
        self.assertEqual('A x in D. P(x)', Parser.parse(formula).to_string())

        formula = 'A x in f(1). P(x)'
        self.assertEqual('A x in f(1). P(x)', Parser.parse(formula).to_string())

        formula = 'E x in D. P(x)'
        self.assertEqual('E x in D. P(x)', Parser.parse(formula).to_string())

        formula = 'C=2 x in D. P(x)'
        self.assertEqual('C=2 x in D. P(x)', Parser.parse(formula).to_string())

        formula = 'A x1, x2 in D1, y1, y2 in D2. P(x1, x2, y1, y2)'
        f = Parser.parse(formula)
        self.assertEqual('A x1 in D1, x2 in D1, y1 in D2, y2 in D2. P(x1, x2, y1, y2)',
                         Parser.parse(formula).to_string())

    def test_atomic_expr(self):
        formula = 'true'
        self.assertEqual('true', Parser.parse(formula).to_string())

        formula = 'false'
        self.assertEqual('false', Parser.parse(formula).to_string())

        formula = 'P(x)'
        self.assertEqual('P(x)', Parser.parse(formula).to_string())

        formula = 'P("x")'
        self.assertEqual('P("x")', Parser.parse(formula).to_string())

        formula = 'P(1)'
        self.assertEqual('P(1)', Parser.parse(formula).to_string())

        formula = 'P(1.)'
        self.assertEqual('P(1.0)', Parser.parse(formula).to_string())

        formula = 'P(1.234)'
        self.assertEqual('P(1.234)', Parser.parse(formula).to_string())

        formula = 'P(f(x))'
        self.assertEqual('P(f(x))', Parser.parse(formula).to_string())

        formula = 'P(x, "x", f(x))'
        self.assertEqual('P(x, "x", f(x))', Parser.parse(formula).to_string())

        formula = 'x1 = x2'
        self.assertEqual('(x1 = x2)', Parser.parse(formula).to_string())

        formula = 'x1 != x2'
        self.assertEqual('(x1 != x2)', Parser.parse(formula).to_string())

        formula = 'x1 < x2'
        self.assertEqual('(x1 < x2)', Parser.parse(formula).to_string())

        formula = 'x1 > x2'
        self.assertEqual('(x1 > x2)', Parser.parse(formula).to_string())

        formula = 'x1 <= x2'
        self.assertEqual('(x1 <= x2)', Parser.parse(formula).to_string())

        formula = 'x1 >= x2'
        self.assertEqual('(x1 >= x2)', Parser.parse(formula).to_string())

    def test_free_vars(self):
        formula = 'P(x) || x in D'
        self.assertEqual('P(x) || x in D', Parser.parse(formula).to_string())

        formula = 'P(x) || x in f(1)'
        f = Parser.parse(formula)
        self.assertEqual('P(x) || x in f(1)', Parser.parse(formula).to_string())

        formula = 'P(x, y, z) || x, y in D1, z in D2'
        self.assertEqual('P(x, y, z) || x in D1, y in D1, z in D2', Parser.parse(formula).to_string())

    def test_mixed_expr(self):
        formula = '(true & P(x)) | (A x in D. P(f(x)))'
        self.assertEqual('((true & P(x)) | A x in D. P(f(x)))', Parser.parse(formula).to_string())

        formula = '(A x in D1. E y in D2. P1(x) & P2(y))'
        self.assertEqual('A x in D1. E y in D2. (P1(x) & P2(y))', Parser.parse(formula).to_string())

        formula = '((A x in D1. P1(x)) -> (C>=2 y in D2. P2(y))) & P3(z)'
        self.assertEqual('((A x in D1. P1(x) -> C>=2 y in D2. P2(y)) & P3(z))', Parser.parse(formula).to_string())

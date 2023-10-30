import unittest
from typing import List

from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.parser.parser import Parser


class TestEvaluation(unittest.TestCase):

    def setUp(self) -> None:
        domain_vals = {'D1': set(range(10)), 'D2': set(range(0, 10, 2)), 'D3': set(range(1, 10, 2))}

        def even(val: int) -> bool:
            return val % 2 == 0

        def odd(val: int) -> bool:
            return val % 2 == 1

        def isupper(string: str) -> bool:
            return string.isupper()

        def islower(string: str) -> bool:
            return string.islower()

        predicate_funcs = {'Even': even, 'Odd': odd, 'Isupper': isupper, 'Islower': islower}

        def inc(val: int) -> int:
            return val + 1

        def dec(val: int) -> int:
            return val - 1

        def upper(string: str) -> str:
            return string.upper()

        def lower(string: str) -> str:
            return string.lower()

        def sum(val_0: int, val_1: int) -> int:
            return val_0 + val_1

        def evens(val_0: int, val_1: int) -> List[int]:
            return list(range(val_0 if val_0 % 2 == 0 else val_0, val_1 + 1, 2))

        def odds(val_0: int, val_1: int) -> List[int]:
            return list(range(val_0 if val_0 % 2 == 1 else val_0 + 1, val_1 + 1, 2))

        function_funcs = {'inc': inc, 'dec': dec, 'upper': upper, 'lower': lower, 'sum': sum,
                          'odds': odds, 'evens': evens}

        self._model = Context(domain_vals, predicate_funcs, function_funcs)

    def test_binary_expr(self):
        formula = 'true -> false'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'false <-> false'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

    def test_nary_expr(self):
        formula = 'true & true & false'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'true | false | false'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'true ^ false ^ false'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

    def test_unary_expr(self):
        formula = '!(true)'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'A x in D2. Even(x)'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'A x in evens(0, 10). Even(x)'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'A x in odds(0, 10). Even(inc(x))'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'A x in D2. Odd(x)'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'C=10 x in D1. (Even(x) ^ Odd(x))'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'C=5 x in D3. Even(inc(dec(inc(x))))'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

    def test_atomic_expr(self):
        formula = 'true'
        self.assertTrue(Parser.parse(formula).evaluate())

        formula = 'false'
        self.assertFalse(Parser.parse(formula).evaluate())

        formula = 'Isupper("STRING")'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = 'Isupper("sTrInG")'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'Islower(lower("STRING"))'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = '"val" = "val"'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = '"val" != "val"'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = '0 < 0'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = '0 <= 0 & 0 >= 0'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

        formula = '1.1 > 1.05'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

    def test_mixed_expr(self):
        formula = 'E x in D3. E x in D3. Even(x)'
        f = self._prepare_formula(formula)
        self.assertFalse(f.evaluate())

        formula = 'A x1 in D2. A x2 in D3. Odd(sum(x1, x2))'
        f = self._prepare_formula(formula)
        self.assertTrue(f.evaluate())

    def _prepare_formula(self, formula: str) -> Formula:
        """
        Prepares a formula.

        :param formula: Unparsed formula.
        :return: Formula.
        """
        parsed_formula = Parser.parse(formula)
        parsed_formula.initialize(self._model)

        return parsed_formula

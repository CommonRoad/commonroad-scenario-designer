from antlr4 import CommonTokenStream, InputStream

from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.parser.gen.FormulaLexer import (
    FormulaLexer,
)
from crdesigner.verification_repairing.verification.hol.parser.gen.FormulaParser import (
    FormulaParser,
)
from crdesigner.verification_repairing.verification.hol.parser.gen.FormulaVisitor import (
    FormulaVisitor,
)


class Parser:
    """
    Class representing a parser.
    """

    @staticmethod
    def parse(formula: str, formula_id: str = "") -> Formula:
        """
        Parses a formula.

        :param formula: Formula in string representation.
        :param formula_id: Formula ID.
        :return: Parsed formula.
        """
        input_stream = InputStream(formula)
        lexer = FormulaLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = FormulaParser(stream)
        tree = parser.formula()

        visitor = FormulaVisitor()
        expr, free_vars, free_var_domains = visitor.visit(tree)

        return Formula(formula_id, expr, free_vars, free_var_domains)

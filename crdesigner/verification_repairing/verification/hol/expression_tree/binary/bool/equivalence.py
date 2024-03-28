from crdesigner.verification_repairing.verification.hol.expression_tree.binary.binary import (
    Binary,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)


class Equivalence(Binary):
    """
    Class representing an equivalence operator.
    """

    def __init__(self, left_expr: Expression, right_expr: Expression):
        super().__init__(Symbol.EQUIVALENCE.value, left_expr, right_expr)

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of equivalence expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        return self._left_expr.evaluate() == self._right_expr.evaluate()

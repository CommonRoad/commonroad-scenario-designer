from typing import List

from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.nary.nary import (
    Nary,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)


class Xor(Nary):
    """
    Class representing a xor operator.
    """

    def __init__(self, exprs: List[Expression]):
        """
        Constructor.

        :param exprs: Expressions.
        """
        super().__init__(Symbol.XOR.value, exprs)

    def evaluate(self) -> str:
        """
        Evaluates satisfiability of xor expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        result = False
        for expr in self._exprs:
            result = result ^ expr.evaluate()
        return result

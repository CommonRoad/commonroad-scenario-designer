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


class And(Nary):
    """
    Class representing a and operator.
    """

    def __init__(self, exprs: List[Expression]):
        """
        Constructor.

        :param exprs: Expressions.
        """
        super().__init__(Symbol.AND.value, exprs)

    def evaluate(self) -> str:
        """
        Evaluates satisfiability of and expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        result = True
        for expr in self._exprs:
            result = result and expr.evaluate()
            if not result:
                break
        return result

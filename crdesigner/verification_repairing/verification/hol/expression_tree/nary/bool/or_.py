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


class Or(Nary):
    """
    Class representing a or operator.
    """

    def __init__(self, exprs: List[Expression]):
        """
        Constructor.

        :param exprs: Expressions.
        """
        super().__init__(Symbol.OR.value, exprs)

    def evaluate(self) -> str:
        """
        Evaluates satisfiability of or expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        result = False
        for expr in self._exprs:
            result = result or expr.evaluate()
            if result:
                break
        return result

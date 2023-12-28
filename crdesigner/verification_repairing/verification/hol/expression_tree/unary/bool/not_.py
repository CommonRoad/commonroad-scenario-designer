from typing import Any, Dict

from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.unary.unary import (
    Unary,
)


class Not(Unary):
    """
    Class representing a not operator.
    """

    def __init__(self, expr: Expression):
        """
        Constructor.

        :param expr: Left expression.
        """
        super().__init__(Symbol.NOT.value, expr)

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of not expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        return not self._expr.evaluate()

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        self.expr.update_variables(var_vals)

from typing import List

from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.variable import (
    Variable,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.unary.first_order.first_order import (
    FirstOrder,
)


class Existential(FirstOrder):
    """
    Class representing an existential quantifier.
    """

    def __init__(self, expr: Expression, vars: List[Variable], domains: List[Domain]):
        """
        Constructor.

        :param expr: Expression.
        :param vars: Variables.
        :param domains: Domains.
        """
        super().__init__(Symbol.EXISTENTIAL.value, expr, vars, domains)

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of existential quantifier expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        self.initial_combinations()

        while self.is_next_combination():
            self.update_variables(self.next_combination())

            if self._expr.evaluate():
                return True

        return False

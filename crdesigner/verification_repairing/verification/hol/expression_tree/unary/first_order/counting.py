import enum
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


class Counting(FirstOrder):
    """
    Class representing a counting quantifier expression.
    """

    class CountType(enum.Enum):
        """
        Enum representing the type of the counting quantifier.
        """

        EQUAL = "="
        LESS_EQUAL = "<="
        GREATER_EQUAL = ">="

    def __init__(
        self,
        expr: Expression,
        vars: List[Variable],
        domains: List[Domain],
        count_type: CountType,
        num: int,
    ):
        """
        Constructor.

        :param expr: Expression.
        :param vars: Variables.
        :param domains: Domains.
        :param count_type: Type of counting.
        :param num: Number.
        """
        super().__init__(Symbol.COUNTING.value, expr, vars, domains)

        self._count_type = count_type
        self._num = num

    @property
    def count_type(self):
        return self._count_type

    @count_type.setter
    def count_type(self, count_type: CountType):
        self._count_type = count_type

    @property
    def num(self):
        return self._num

    @num.setter
    def num(self, num: int):
        self._num = num

    def to_string(self) -> str:
        """
        Converts counting quantifier expression to string representation.

        :return: String.
        """
        string = super().to_string()

        return self._symbol + self._count_type.value + str(self._num) + string[1:]

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of counting quantifier expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        self.initial_combinations()

        true_count = 0
        while self.is_next_combination():
            self.update_variables(self.next_combination())

            if self._expr.evaluate():
                true_count += 1

            if (
                Counting.CountType.LESS_EQUAL == self._count_type
                or Counting.CountType.EQUAL == self._count_type
            ):
                if true_count > self._num:
                    return False
            else:
                if true_count > self._num:
                    return True

        if Counting.CountType.LESS_EQUAL == self._count_type:
            return true_count <= self._num
        elif Counting.CountType.EQUAL == self._count_type:
            return true_count == self._num
        else:
            return true_count >= self._num

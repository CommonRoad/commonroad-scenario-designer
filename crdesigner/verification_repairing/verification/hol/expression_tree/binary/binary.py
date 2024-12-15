from abc import ABC
from typing import Any, Dict

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)


class Binary(Expression, ABC):
    """
    Abstract class representing binary expression.
    """

    def __init__(self, symbol: str, left_expr: Expression, right_expr: Expression):
        """
        Constructor.

        :param symbol: Symbol.
        :param left_expr: Left expression.
        :param right_expr: Right expression.
        """
        super().__init__(symbol)

        self._left_expr = left_expr
        self._right_expr = right_expr

    @property
    def left_expr(self):
        return self._left_expr

    @property
    def right_expr(self):
        return self._right_expr

    @left_expr.setter
    def left_expr(self, left_expr: Expression):
        self._left_expr = left_expr

    @right_expr.setter
    def right_expr(self, right_expr: Expression):
        self._right_expr = right_expr

    def to_string(self) -> str:
        """
        Converts binary expression to string representation.
        """
        return (
            "("
            + self._left_expr.to_string()
            + " "
            + self._symbol
            + " "
            + self._right_expr.to_string()
            + ")"
        )

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        self._left_expr.initialize(model)
        self._right_expr.initialize(model)

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        self._left_expr.update_variables(var_vals)
        self._right_expr.update_variables(var_vals)

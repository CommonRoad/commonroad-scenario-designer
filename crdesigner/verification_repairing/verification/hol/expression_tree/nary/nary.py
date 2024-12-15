from abc import ABC
from typing import Any, Dict, List

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)


class Nary(Expression, ABC):
    """
    Abstract class representing a nary expression.
    """

    def __init__(self, symbol: str, exprs: List[Expression]):
        """
        Constructor.

        :param symbol: Symbol.
        :param exprs: Expressions.
        """
        super().__init__(symbol)

        self._exprs = exprs

    @property
    def exprs(self):
        return self._exprs

    @exprs.setter
    def exprs(self, exprs: List[Expression]):
        self._exprs = exprs

    def to_string(self) -> str:
        """
        Converts nary expression to string representation.

        :return: String.
        """
        string = "("
        for i, expr in enumerate(self._exprs):
            string += expr.to_string() + (
                " " + self._symbol + " " if i < len(self._exprs) - 1 else ")"
            )
        return string

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        for expr in self._exprs:
            expr.initialize(model)

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        for expr in self._exprs:
            expr.update_variables(var_vals)

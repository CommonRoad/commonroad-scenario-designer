from abc import ABC

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)


class Unary(Expression, ABC):
    """
    Abstract class representing a unary expression.
    """

    def __init__(self, symbol: str, expr: Expression):
        """
        Constructor.

        :param symbol: Symbol.
        :param expr: Left expression.
        """
        super().__init__(symbol)

        self._expr = expr

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr: Expression):
        self._expr = expr

    def to_string(self) -> str:
        """
        Converts unary expression to string representation.
        """
        return self._symbol + "(" + self._expr.to_string() + ")"

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        self._expr.initialize(model)

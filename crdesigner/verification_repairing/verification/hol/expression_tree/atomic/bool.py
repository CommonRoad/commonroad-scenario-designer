from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)


class Bool(Expression):
    """
    Class representing a boolean constant, i.e. true or false.
    """

    def __init__(self, value: bool):
        super().__init__("true" if value else "false")

        self._value = value

    @property
    def constant(self):
        return self._value

    @constant.setter
    def constant(self, value: bool):
        self._value = value

    def to_string(self) -> str:
        """
        Converts boolean constant to string representation.
        """
        return self._symbol

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of bool expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        return self._value

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        pass

    def update_variables(self, _):
        """
        Updates values of variables.
        """
        pass

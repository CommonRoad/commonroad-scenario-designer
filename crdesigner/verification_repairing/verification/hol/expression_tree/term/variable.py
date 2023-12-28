from typing import Any, Dict

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.term.term import (
    Term,
)


class Variable(Term):
    """
    Class representing a variable.
    """

    def __init__(self, name: str, val: Any = None):
        """
        Constructor.

        :param name: Name.
        :param val: Value.
        """
        super().__init__(name)

        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, val: Any):
        self._val = val

    def to_string(self) -> str:
        """
        Converts a variable to string representation.
        """
        return self._name

    def initialize(self, model: Context):
        """
        Initializes the term functions that are stored in the model.

        :param model: Model.
        """
        pass

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        if self._name in var_vals.keys():
            self._val = var_vals[self._name]

    def evaluate(self) -> Any:
        """
        Evaluates the term.

        :return: Result.
        """
        return self._val

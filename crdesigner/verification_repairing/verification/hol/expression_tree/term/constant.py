from typing import Any, Dict, Union

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.term.term import (
    Term,
)


class Constant(Term):
    """
    Class representing a constant.
    """

    def __init__(self, val: Union[str, int, float]):
        """
        Constructor.

        :param val: Constant value.
        """
        super().__init__(str(val))

        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, val: Union[str, int, float]):
        self._val = val

    def to_string(self) -> str:
        """
        Converts a constant to string representation.
        """
        return '"' + self._name + '"' if isinstance(self._val, str) else self._name

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
        pass

    def evaluate(self) -> Any:
        """
        Evaluates the term.

        :return: Result.
        """
        return self._val

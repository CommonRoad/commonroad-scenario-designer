from typing import Any, Dict, Union

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.term.term import (
    Term,
)
import numpy as np

class Constant(Term):
    """
    Class representing a constant. the value can be a string, integer, or float.
    """

    # def __init__(self, val: Union[str, int, float]):
    #     """
    #     Constructor.

    #     :param val: Constant value.
    #     """
    #     super().__init__(str(val))

    #     self._val = val
    def __init__(self, val: Any):
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

    def __eq__(self, other: object) -> bool:
        """
        Checks if two constants are equal.
        """
        if not isinstance(other, Constant):
            return False
        a, b = self._val, other._val
        if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
            return np.allclose(a, b)
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return len(a) == len(b) and all(x == y for x, y in zip(a, b))
        return a == b
    
    def __hash__(self) -> int:
        """
        Returns a hash value for the constant.

        :return: Hash value.
        """
        v = self._val
        if isinstance(v, np.ndarray):
             return hash(v.tobytes())
        if isinstance(v, (list, tuple)):
            return hash(tuple(v))
        return hash(v)

    def evaluate(self) -> Any:
        """
        Evaluates the term.

        :return: Result.
        """
        return self._val

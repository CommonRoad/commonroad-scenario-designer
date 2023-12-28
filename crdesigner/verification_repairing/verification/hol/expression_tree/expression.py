from abc import ABC, abstractmethod
from typing import Any, Dict

from crdesigner.verification_repairing.verification.hol.context import Context


class Expression(ABC):
    """
    Abstract class representing an expression.
    """

    def __init__(self, symbol: str):
        """
        Constructor.

        :param symbol: Symbol.
        """
        self._symbol = symbol

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, symbol: str):
        self._symbol = symbol

    @abstractmethod
    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of expression.

        :return: Boolean indicates whether expression is satisfied.
        """
        pass

    @abstractmethod
    def to_string(self) -> str:
        """
        Converts expression to string representation.
        """
        pass

    @abstractmethod
    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        pass

    @abstractmethod
    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        pass

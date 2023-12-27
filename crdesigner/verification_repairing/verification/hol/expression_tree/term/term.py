from abc import ABC, abstractmethod
from typing import Any, Dict

from crdesigner.verification_repairing.verification.hol.context import Context


class Term(ABC):
    """
    Abstract class representing a term.
    """

    def __init__(self, name: str):
        """
        Constructor.

        :param name: Name.
        """
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @abstractmethod
    def to_string(self) -> str:
        """
        Converts term to string representation.
        """
        pass

    @abstractmethod
    def initialize(self, model: Context):
        """
        Initializes the term functions that are stored in the model.

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

    @abstractmethod
    def evaluate(self) -> Any:
        """
        Evaluates the term.

        :return: Result.
        """
        pass

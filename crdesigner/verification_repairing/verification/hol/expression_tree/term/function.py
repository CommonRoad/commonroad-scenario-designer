import warnings
from typing import Any, Callable, Dict, List, Optional

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.term.term import (
    Term,
)


class Function(Term):
    """
    Class representing a function.
    """

    def __init__(
        self, name: str, terms: List[Term], func: Optional[Callable] = None
    ):  # [[Any, ...], Any] = None):
        """
        Constructor.

        :param name: Name.
        :param terms: Terms.
        :param func: Function.
        """
        super().__init__(name)

        self._terms = terms
        self._func = func

    @property
    def terms(self):
        return self._terms

    @terms.setter
    def terms(self, terms: List[Term]):
        self._terms = terms

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, func: Callable):  # [[Any, ...], Any]):
        self._func = func

    def to_string(self) -> str:
        """
        Converts a function to string representation.

        :return: String.
        """
        string = self._name + "("
        for i, term in enumerate(self._terms):
            string += term.to_string() + (", " if i < len(self._terms) - 1 else "")
        return string + ")"

    def initialize(self, model: Context):
        """
        Initializes the term functions that are stored in the model.

        :param model: Model.
        """
        if self._name in model.function_funcs.keys():
            self._func = model.function_funcs[self._name]
        else:
            warnings.warn(
                "Unsuccessful initialization of function of term function {}!".format(self._name)
            )

        for term in self._terms:
            term.initialize(model)

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        for term in self._terms:
            term.update_variables(var_vals)

    def evaluate(self) -> Any:
        """
        Evaluates the term.

        :return: Result.
        """
        args = []
        for term in self._terms:
            args.append(term.evaluate())
        return self._func(*args)

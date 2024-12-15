import warnings
from typing import Any, Callable, Dict, List, Optional

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.term import (
    Term,
)


class Predicate(Expression):
    """
    Class representing a predicate.
    """

    def __init__(
        self, symbol: str, terms: List[Term], func: Optional[Callable] = None
    ):  # [[Any, ...], bool] = None):
        """
        Constructor.

        :param symbol: Symbol.
        :param terms: Terms.
        :param func: Function.
        """
        super().__init__(symbol)

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
    def func(self, func: Callable):  # [[Any, ...], bool]):
        self._func = func

    def to_string(self) -> str:
        """
        Converts a predicate to string representation.

        :return: String.
        """
        if self._symbol in ["=", "!=", "<", ">", "<=", ">="]:
            string = (
                "("
                + self._terms[0].to_string()
                + " "
                + self._symbol
                + " "
                + self._terms[1].to_string()
            )
        else:
            string = self._symbol + "("
            for i, term in enumerate(self._terms):
                string += term.to_string() + (", " if i < len(self._terms) - 1 else "")

        return string + ")"

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of predicate.

        :return: Boolean indicates whether predicate is satisfied.
        """
        args = []
        for term in self._terms:
            args.append(term.evaluate())
        return self._func(*args)

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        if self._symbol in model.predicate_funcs.keys():
            self._func = model.predicate_funcs[self._symbol]
        else:
            warnings.warn(
                "Unsuccessful initialization of function of predicate {}!".format(self._symbol)
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

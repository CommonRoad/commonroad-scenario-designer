import itertools
import warnings
from abc import ABC
from typing import Any, Dict, List

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.dynamic import (
    DynamicDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.fixed import (
    FixedDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.variable import (
    Variable,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.unary.unary import (
    Unary,
)


class FirstOrder(Unary, ABC):
    """
    Abstract class representing a first-order expression.
    """

    def __init__(self, symbol: str, expr: Expression, vars: List[Variable], domains: List[Domain]):
        """
        Constructor.

        :param symbol: Symbol.
        :param expr: Expression.
        :param vars: Variables.
        :param domains: Domains.
        """
        super().__init__(symbol, expr)

        self._vars = vars
        self._domains = domains

        self._combinations = []

    @property
    def vars(self):
        return self._vars

    @vars.setter
    def vars(self, vars: List[Variable]):
        self._vars = vars

    @property
    def domains(self):
        return self._domains

    @domains.setter
    def domains(self, domains: List[Domain]):
        self._domains = domains

    def to_string(self) -> str:
        """
        Converts first-order expression to string representation.

        :return: String.
        """
        string = self._symbol + " "
        for i, (var, domain) in enumerate(zip(self._vars, self._domains)):
            string += (
                var.name
                + " in "
                + domain.to_string()
                + (". " if i == len(self._vars) - 1 else ", ")
            )
        string += self._expr.to_string()
        return string

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """
        for domain in self._domains:
            if isinstance(domain, FixedDomain):
                if domain.domain_id in model.domain_vals.keys():
                    domain.values = model.domain_vals[domain.domain_id]
                else:
                    warnings.warn(
                        "Unsuccessful initialization of values of fixed domain {}".format(
                            domain.domain_id
                        )
                    )
            elif isinstance(domain, DynamicDomain):
                if domain.func.name in model.function_funcs.keys():
                    domain.func.func = model.function_funcs[domain.func.name]
                    domain.initialize(model)
                else:
                    warnings.warn(
                        "Unsuccessful initialization of function of dynamic domain {}".format(
                            domain.func.name
                        )
                    )

        super().initialize(model)

    def update_variables(self, var_vals: Dict[str, Any]):
        """
        Updates values of variables.

        :param var_vals: Values of variables.
        """
        for domain in self._domains:
            if isinstance(domain, DynamicDomain):
                domain.func.update_variables(var_vals)

        self._expr.update_variables(var_vals)

    def is_next_combination(self) -> bool:
        """
        Checks whether a next combination of values exists.

        :return: Boolean indicates whether there is a next combination.
        """
        return bool(self._combinations)

    def next_combination(self) -> Dict[str, Any]:
        """
        Explores a next combination of values that are assigned to the variables.

        :return: Combination.
        """
        values = self._combinations.pop()

        combination = {}
        for i, var in enumerate(self._vars):
            combination[var.name] = values[i]

        return combination

    def initial_combinations(self):
        """
        Initializes all combinations of values that are assigned to the variables.
        """
        value_lists = []
        for domain in self._domains:
            if isinstance(domain, FixedDomain):
                value_lists.append(domain.values)
            elif isinstance(domain, DynamicDomain):
                value_lists.append(domain.func.evaluate())
        self._combinations = list(itertools.product(*value_lists))

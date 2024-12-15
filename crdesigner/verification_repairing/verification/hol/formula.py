import enum
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
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.variable import (
    Variable,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.unary.bool.not_ import (
    Not,
)
from crdesigner.verification_repairing.verification.hol.functions.predicates import (
    builtin_predicates,
)
from crdesigner.verification_repairing.verification.hol.functions.term_functions import (
    builtin_functions,
)


class DomainName(enum.Enum):
    LANELETS = "L"
    TRAFFIC_SIGNS = "TS"
    TRAFFIC_LIGHTS = "TL"
    INTERSECTIONS = "I"
    INCOMING_GROUPS = "IG"
    TRAFFIC_LIGHT_CYCLE_ELEMENTS = "CE"
    OUTGOING_GROUPS = "OG"
    POLYLINES = "P"
    STOP_LINES = "SL"
    AREAS = "AR"
    ALL_ELEMENTS = "M"


class Formula:
    """
    Class representing a formula.
    """

    def __init__(
        self,
        formula_id: str,
        expr: Expression,
        free_vars: List[Variable],
        free_var_domains: List[Domain],
    ):
        """
        Constructor.

        :param formula_id: Formula ID.
        :param expr: Expression.
        :param free_vars: Free variables.
        :param free_var_domains: Domains of free variables.
        """

        self._formula_id = formula_id
        self._expr = expr
        self._free_vars = free_vars
        self._free_var_domains = free_var_domains

    @property
    def formula_id(self):
        return self._formula_id

    @formula_id.setter
    def formula_id(self, formula_id: str):
        self._formula_id = formula_id

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr: Expression):
        self._expr = expr

    @property
    def free_vars(self):
        return self._free_vars

    @free_vars.setter
    def free_vars(self, free_vars: List[Variable]):
        self._free_vars = free_vars

    @property
    def free_var_domains(self):
        return self._free_var_domains

    @free_var_domains.setter
    def free_var_domains(self, free_var_domains: List[Domain]):
        self._free_var_domains = free_var_domains

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """

        # built-in predicates
        for func_name in dir(builtin_predicates):
            predicate_func = getattr(builtin_predicates, func_name)
            if callable(predicate_func) and not func_name.startswith("__"):
                for symbol in Symbol:
                    if func_name == symbol.name.lower():
                        func_name = symbol.value
                model.add_predicate_func(func_name.capitalize(), predicate_func)

        # built-in functions
        for func_name in dir(builtin_functions):
            function_func = getattr(builtin_functions, func_name)
            if callable(function_func) and not func_name.startswith("__"):
                model.add_function_func(func_name, function_func)

        # initializes domains of free variables
        for domain in self._free_var_domains:
            if isinstance(domain, FixedDomain):
                if (
                    domain.domain_id in model.domain_vals.keys()
                    or domain.domain_id == DomainName.ALL_ELEMENTS.value
                ):
                    domain.values = model.domain_vals[domain.domain_id]
            elif isinstance(domain, DynamicDomain):
                if domain.domain_id in model.function_funcs.keys():
                    domain.func.func = model.function_funcs[domain.domain_id]

        self._expr.initialize(model)

    def to_string(self) -> str:
        """
        Converts formula to string representation.

        :return: String.
        """
        string = self._expr.to_string()
        for i, (var, domain) in enumerate(zip(self._free_vars, self._free_var_domains)):
            if i == 0:
                string += " || "
            string += (
                var.name
                + " in "
                + domain.to_string()
                + (", " if i < len(self._free_vars) - 1 else "")
            )

        return string

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of expression of formula.

        :return: Boolean indicates whether expression of formula is satisfied.
        """
        return self._expr.evaluate()

    def negate(self):
        """
        Negates the expression of formula.
        """
        if isinstance(self._expr, Not):
            self._expr = self._expr.expr
        else:
            self._expr = Not(self._expr)

    def update_free_variables(self, free_var_vals: Dict[str, Any]):
        """
        Updates values of free variables.

        :param free_var_vals: Values of free variables.
        """
        for var in self._free_vars:
            if var.name in free_var_vals.keys():
                var.val = free_var_vals[var.name]

        self._expr.update_variables(free_var_vals)

    def extract_free_variables(self) -> List[Variable]:
        """
        Extracts all free variables in formula.

        :return: Free variables.
        """
        pass  # TODO: Implement

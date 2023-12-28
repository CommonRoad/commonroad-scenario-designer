from typing import Any, Tuple, Union

from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.dynamic import (
    DynamicDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.fixed import (
    FixedDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.variable import (
    Variable,
)


class VarDomainIterator:
    """
    Class representing an iterator that computes iteratively the combinations for the variables bounded to
    the fixed or dynamic domains.
    """

    def __init__(self, var: Variable, domain: Domain, next_iter: "VarDomainIterator" = None):
        """
        Constructor.

        :param var: Variable.
        :param domain: Domain.
        :param next_iter: Next domain iterator.
        """
        self._var = var
        self._domain = domain
        self._next_iter = next_iter

        self._values = None
        self._pos = 0

    @property
    def var(self) -> Variable:
        """Variable."""
        return self._var

    @var.setter
    def var(self, var: Variable):
        self._var = var

    @property
    def domain(self) -> Domain:
        """Variable."""
        return self._domain

    @domain.setter
    def domain(self, domain: Domain):
        self._domain = domain

    @property
    def next_iter(self) -> "VarDomainIterator":
        """Next domain iterator."""
        return self._next_iter

    @next_iter.setter
    def next_iter(self, next_iter: "VarDomainIterator"):
        self._next_iter = next_iter

    @property
    def values(self) -> Tuple[Any, ...]:
        """Values of variables."""
        return self._values

    @values.setter
    def values(self, values: Tuple[Any, ...]):
        self._values = values

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, pos: int):
        self._pos = pos

    def update_variable(self, var_id: str, val: Any):
        """
        Updates value of variable.

        :param var_id: Variable ID.
        :param val: Value.
        """
        if isinstance(self._domain, DynamicDomain):
            self._domain.func.update_variables({var_id: val})

        if self._next_iter is not None:
            self._next_iter.update_variable(var_id, val)

    def is_finished(self) -> bool:
        """
        Checks whether the iteration is finished.

        :return: Boolean indicates whether the iteration is finished.
        """
        return self._values is not None and not (self._pos < len(self._values))

    def iteration_step(self) -> Union[Tuple[Any, ...], None]:
        """
        Goes an iteration step.

        :return: Combination; none if step does not result in complete combination.
        """
        if self._values is None or self.is_finished():
            if isinstance(self._domain, FixedDomain):
                self._values = self._domain.values
            elif isinstance(self._domain, DynamicDomain):
                self._values = self._domain.func.evaluate()
            self._values = list(self._values)
            self._pos = 0
            if not self._values:
                self._pos = 1
                return None

        self.update_variable(self._var.name, self._values[self._pos])

        combination = (self._values[self._pos],)
        if self._next_iter is not None:
            step_res = self._next_iter.iteration_step()
            if step_res is None:
                if self._next_iter.is_finished():
                    self._pos += 1
                return None
            combination += step_res

        if self._next_iter is not None and self._next_iter.is_finished():
            self._pos += 1

        if self._next_iter is None:
            self._pos += 1

        return combination

    def next_combination(self) -> Tuple[Any, ...]:
        """
        Returns the next combination.

        :return: Combination; none if there is no combination.
        """
        step_res = None
        while step_res is None and not self.is_finished():
            step_res = self.iteration_step()

        return step_res

from typing import Any, Set

from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)


class FixedDomain(Domain):
    """
    Class representing a fixed domain.
    """

    def __init__(self, domain_id: str, values: Set[Any] = None):
        """
        Constructor.

        :param domain_id: Domain ID.
        :param values: Values.
        """
        super().__init__(domain_id)

        self._values = values

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, values: Set[Any]):
        self._values = values

    def add_value(self, value: Any):
        """
        Adds value to domain.

        :param value: Value.
        """
        self._values.update(value)

    def to_string(self) -> str:
        """
        Converts fixed domain to string representation.

        :return: String.
        """
        return super().to_string()

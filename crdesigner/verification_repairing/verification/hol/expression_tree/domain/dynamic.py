from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.function import (
    Function,
)


class DynamicDomain(Domain):
    """
    Class representing a dynamic domain.
    """

    def __init__(self, domain_id: str, func: Function):
        """
        Constructor.

        :param domain_id: Domain ID.
        :param func: Function.
        """
        super().__init__(domain_id)

        self._func = func

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, func: Function):
        self._func = func

    def initialize(self, model: Context):
        """
        Initializes the terms of the dynamic that are stored in the model.

        :param model: Model.
        """
        self._func.initialize(model)

    def to_string(self) -> str:
        """
        Converts dynamic domain to string representation.

        :return: String.
        """
        return self._func.to_string()

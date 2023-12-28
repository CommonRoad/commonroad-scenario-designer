from typing import Any, Callable, Dict, Set


class Context:
    """
    Class representing a model.
    """

    def __init__(
        self,
        domain_vals: Dict[str, Set[Any]],
        predicate_funcs: Dict[str, Callable],  # [[Any, ...], bool]],
        function_funcs: Dict[str, Callable],
    ):  # [[Any, ...], Any]]):
        """
        Constructor.

        :param domain_vals: Values of domains.
        :param predicate_funcs: Functions of predicates.
        :param function_funcs: Functions of term functions.
        """
        self._domain_vals = domain_vals
        self._predicate_funcs = predicate_funcs
        self._function_funcs = function_funcs

    @property
    def domain_vals(self) -> Dict[str, Set[Any]]:
        """Values of domains."""
        return self._domain_vals

    @domain_vals.setter
    def domain_vals(self, domain_vals: Dict[str, Set[Any]]):
        self._domain_vals = domain_vals

    @property
    def predicate_funcs(self) -> Dict[str, Callable]:  # [[Any, ...], bool]]:
        """Functions of predicates."""
        return self._predicate_funcs

    @predicate_funcs.setter
    def predicate_funcs(self, predicate_funcs: Dict[str, Callable]):  # [[Any, ...], bool]]):
        self._predicate_funcs = predicate_funcs

    @property
    def function_funcs(self) -> Dict[str, Callable]:  # [[Any, ...], Any]]:
        """Functions of term functions."""
        return self._function_funcs

    @function_funcs.setter
    def function_funcs(self, function_funcs: Dict[str, Callable]):  # [[Any, ...], Any]]):
        self._function_funcs = function_funcs

    def add_domain_vals(self, name: str, vals: Set[Any]):
        """
        Adds values of new domain.

        :param name: Name of domain.
        :param vals: Values.
        """
        self._domain_vals.update({name: vals})

    def add_predicate_func(self, name: str, func: Callable):  # :[[Any, ...], bool]):
        """
        Adds function of new predicate.

        :param name: Name of predicate.
        :param func: Function.
        """
        self._predicate_funcs.update({name: func})

    def add_function_func(self, name: str, func: Callable):  # [[Any, ...], Any]):
        """
        Adds function of new term function.

        :param name: Name of term function.
        :param func: Function.
        """
        self._function_funcs.update({name: func})

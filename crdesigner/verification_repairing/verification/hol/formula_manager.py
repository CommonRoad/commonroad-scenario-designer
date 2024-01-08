import warnings
from typing import Any, Dict, List, Set

from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.formula_collection import (
    GeneralFormulas,
    IntersectionFormulas,
    LaneletFormulas,
    TrafficLightFormulas,
    TrafficSignFormulas,
)
from crdesigner.verification_repairing.verification.hol.parser.parser import Parser


class FormulaManager:
    """
    Class representing the management of formulas.
    """

    def __init__(self):
        """
        Constructor.
        """
        self._formulas = []
        self._domains = {}

        self._collect_formulas()

    @property
    def formulas(self) -> List[Formula]:
        return self._formulas

    @formulas.setter
    def formulas(self, formulas: List[Formula]):
        self._formulas = formulas

    @property
    def domains(self) -> Dict[str, Set[Any]]:
        return self._domains

    @domains.setter
    def domains(self, domains: Dict[str, Set[Any]]):
        self._domains = domains

    def add_formula(self, formula: Formula):
        """
        Adds a formula. A formula is not stored if a formula with the same ID is already contained.

        :param formula: Formula.
        """
        for f in self._formulas:
            if f.formula_id == formula.formula_id:
                warnings.warn("Formula with ID {} is already stored!".format(formula.formula_id))
                return
        self._formulas.append(formula)

    def add_domain(self, domain_id: str, values: Set[Any]):
        """
        Adds a domain. A domain is not stored if a domain with the same ID is already contained.

        :param domain_id: Domain ID.
        :param values: Values.
        """
        if domain_id in self._domains.keys():
            warnings.warn("Domain with ID {} is already stored!".format(domain_id))
            return
        self._domains[domain_id] = values

    def _collect_formulas(self):
        for collection in [
            TrafficLightFormulas,
            TrafficSignFormulas,
            IntersectionFormulas,
            LaneletFormulas,
            GeneralFormulas,
        ]:
            for formula_id, formula in collection.formulas.items():
                for subformula_id, subformula in collection.subformulas.items():
                    formula = formula.replace(subformula_id, subformula)
                self._formulas.append(Parser.parse(formula, formula_id))

            for domain_id, values in collection.domains.items():
                self._domains[domain_id] = set(values)

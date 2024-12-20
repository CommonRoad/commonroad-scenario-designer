import logging
import warnings
from typing import List

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign

from crdesigner.verification_repairing.config import VerificationParams
from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    extract_formula_id,
    extract_formula_ids,
)
from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.mapping import HOLMapping
from crdesigner.verification_repairing.verification.hol.var_domain_iterator import (
    VarDomainIterator,
)
from crdesigner.verification_repairing.verification.satisfaction import (
    InvalidStates,
    VerificationChecker,
)


class HOLVerificationChecker(VerificationChecker):
    def __init__(self, mapping: HOLMapping, formula_ids: List[FormulaID] = None):
        """
        Constructor of HOLValidityChecker.

        :param mapping: Mapping of CommonRoad elements to instances.
        :param formula_ids: List of formula IDs which should be evaluated.
        """
        super().__init__(mapping, formula_ids)

        self._invalid_states = {}

    def check_validity(self, config: VerificationParams, manager_results: List[InvalidStates]):
        """
        Checks the network for validity.

        :param config: Verification config parameters.
        :param manager_results: Results.
        """
        model: Context = self._mapping.model

        for domain_id, values in config.formula_manager.domains.items():
            model.add_domain_vals(domain_id, values)

        if self._formula_ids is None:
            formula_ids = extract_formula_ids()
        else:
            formula_ids = self._formula_ids

        for formula in config.formula_manager.formulas:
            for formula_id in formula_ids:
                if formula_id.value == formula.formula_id:
                    logging.debug(f"HOL::check_validity: {formula_id}")
                    self._solve_formula(formula, model)

        manager_results.append(self._invalid_states)

    def _solve_formula(self, formula: Formula, model: Context):
        """
        Solves a formula.

        :param formula: Formula.
        :param model:
        """
        formula.initialize(model)

        iters = []
        for var, domain in zip(formula.free_vars, formula.free_var_domains):
            iters.append(VarDomainIterator(var, domain))

        init_iter = None
        for prev_iter in reversed(iters):
            prev_iter.next_iter = init_iter
            init_iter = prev_iter

        while init_iter is not None:
            combination = init_iter.next_combination()
            if combination is None:
                break
            free_var_vals = {}
            for i, var in enumerate(formula.free_vars):
                free_var_vals[var.name] = combination[i]

            formula.update_free_variables(free_var_vals)

            if not formula.evaluate():
                location = []
                for element in combination:
                    if isinstance(element, Lanelet):
                        location.append(element.lanelet_id)
                    elif isinstance(element, TrafficSign):
                        location.append(element.traffic_sign_id)
                    elif isinstance(element, TrafficLight):
                        location.append(element.traffic_light_id)
                    elif isinstance(element, Intersection):
                        location.append(element.intersection_id)
                    else:
                        warnings.warn("Unsuccessful extraction of ID of element!")
                location = tuple(location)

                formula_id = extract_formula_id(formula.formula_id)
                if formula_id in self._invalid_states.keys():
                    self._invalid_states[formula_id].append(location)
                else:
                    self._invalid_states[formula_id] = [location]

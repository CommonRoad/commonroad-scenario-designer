from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from crdesigner.verification_repairing.config import VerificationParams
from crdesigner.verification_repairing.verification.formula_ids import FormulaID
from crdesigner.verification_repairing.verification.mapping import Mapping

Locations = List[Tuple[Any, ...]]
InvalidStates = Dict[FormulaID, Locations]


class VerificationChecker(ABC):
    """
    The class is responsible for solving the desired formulas. The inferred invalid states are extracted and returned.
    """

    def __init__(self, mapping: Mapping, formula_ids: List[FormulaID]):
        self._mapping = mapping
        self._formula_ids = formula_ids

    @abstractmethod
    def check_validity(self, config: VerificationParams, manager_results: List[InvalidStates]):
        """
        Checks the network for validity.

        :param config: Verification config parameters.
        :param manager_results: List where invalid states are stored.
        """
        pass

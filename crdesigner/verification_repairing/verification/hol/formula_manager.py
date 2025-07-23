from __future__ import annotations

import warnings
from typing import Any, Dict, List, Set, Optional

from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.formula_collection import (
    GeneralFormulas,
    IntersectionFormulas,
    LaneletFormulas,
    TrafficLightFormulas,
    TrafficSignFormulas,
    LaneletFormulas3D,
)
from crdesigner.verification_repairing.verification.hol.parser.parser import Parser


class FormulaManager:
    """
    Central registry that converts all textual HOL‑specifications into
    executable expression trees and stores accompanying domains.
    """

    # ────────────────────────────── ctor ──────────────────────────────
    def __init__(self, lanelet_network: Optional["LaneletNetwork"] = None) -> None:
        """
        :param lanelet_network: CommonRoad LaneletNetwork.  
                               Used only to detect whether 3‑D rules are required.
        """
        # True: # At least one lanelet has a third dimension -> enable 3D rules
        self._enable_3d: bool = (
            lanelet_network is not None
            and any(ll.center_vertices.shape[1] == 3 for ll in lanelet_network.lanelets)
        )

        self._formulas: List[Formula] = []
        self._domains: Dict[str, Set[Any]] = {}

        self._collect_formulas()

    # ─────────────────────────── properties ───────────────────────────
    @property
    def formulas(self) -> List[Formula]:
        return self._formulas

    @formulas.setter
    def formulas(self, value: List[Formula]) -> None:
        self._formulas = value

    @property
    def domains(self) -> Dict[str, Set[Any]]:
        return self._domains

    @domains.setter
    def domains(self, value: Dict[str, Set[Any]]) -> None:
        self._domains = value

    # ────────────────────── public helper api ────────────────────────
    def add_formula(self, formula: Formula) -> None:
        """Add a new formula unless its ID already exists."""
        if any(f.formula_id == formula.formula_id for f in self._formulas):
            warnings.warn(f"Formula with ID {formula.formula_id} is already stored!")
            return
        self._formulas.append(formula)

    def add_domain(self, domain_id: str, values: Set[Any]) -> None:
        """Register a new domain unless it has been defined before."""
        if domain_id in self._domains:
            warnings.warn(f"Domain with ID {domain_id} is already stored!")
            return
        self._domains[domain_id] = set(values)

    # ─────────────────────── internal routines ───────────────────────
    def _collect_formulas(self) -> None:
        """
        Convert every formula string from every collection into
        executable expression trees and gather their domains.
        """
        # 1. decide which collections to load
        collections = [
            TrafficLightFormulas,
            TrafficSignFormulas,
            IntersectionFormulas,
            LaneletFormulas,
            GeneralFormulas,
        ]
        if self._enable_3d:
            # Place 3D formulas first, to detect them early
            collections.insert(0, LaneletFormulas3D)

        # 2. parse all formulas & merge sub‑formulas
        for coll in collections:
            for formula_id, formula_text in coll.formulas.items():
                # substitute sub‑formula placeholders
                for sub_id, sub_text in coll.subformulas.items():
                    formula_text = formula_text.replace(sub_id, sub_text)

                parsed = Parser.parse(formula_text, formula_id)
                self._formulas.append(parsed)

            # merge domains (later collections can overwrite earlier ones,
            # which is useful for specialised versions)
            for dom_id, dom_vals in coll.domains.items():
                self._domains.setdefault(dom_id, set()).update(dom_vals)

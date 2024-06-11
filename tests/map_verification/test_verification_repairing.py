import os
import unittest
from pathlib import Path
from typing import List

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.verification_repairing.config import MapVerParams, VerificationParams
from crdesigner.verification_repairing.map_verification_repairing import (
    collect_scenario_paths,
    verify_and_repair_scenario,
)
from crdesigner.verification_repairing.verification.formula_ids import FormulaID
from crdesigner.verification_repairing.verification.hol.mapping import HOLMapping
from crdesigner.verification_repairing.verification.hol.satisfaction import (
    HOLVerificationChecker,
)


class TestAll(unittest.TestCase):
    def verify(self, formula_ids: List[FormulaID]):
        for sc_name in self.network_names:
            sc, _ = CRDesignerFileReader(str(self.network_path) + "/test_maps/" + sc_name + ".xml").open()
            config = MapVerParams()
            config.verification.formulas = formula_ids
            sc, _ = verify_and_repair_scenario(sc, config)

            self.assertGreater(len(sc.lanelet_network.lanelets), 0)
            self.check_repairing(formula_ids, sc)

    def check_repairing(self, formula_ids, sc):
        mapping = HOLMapping(sc.lanelet_network)
        mapping.map_verification_paras()
        mapping.map_lanelet_network()
        verifier = HOLVerificationChecker(mapping, formula_ids)
        invalid_states = []
        config = VerificationParams()
        config.formulas = formula_ids
        verifier.check_validity(config, invalid_states)
        self.assertEqual(invalid_states, [{}])

    def setUp(self) -> None:
        self.network_names = [
            "paper_test_maps/DEU_BadEssen-3_1_T-1",
            "paper_test_maps/DEU_Guetersloh-20_1_T-1",
            "paper_test_maps/DEU_Reutlingen-1_1_T-1",
            "DEU_AachenBendplatz-1",
            "DEU_TrafficLightTest-1",  # traffic light cycle has no ID-> unique ID check fails if cycle in overall set
            "Garching_bakery_round_3D",
        ]
        self.network_path = Path(__file__).parent
        self.base_formula_ids = []

    def test_compare_real_scenarios(self):
        formula_ids = self.base_formula_ids
        self.verify(formula_ids)

    def test_path_collection(self):
        self.assertEqual(
            10,
            len(
                collect_scenario_paths(
                    Path(f"{os.path.dirname(os.path.realpath(__file__))}/../map_verification/test_maps"), subdir=False
                )
            ),
        )

        self.assertEqual(
            13,
            len(
                collect_scenario_paths(
                    Path(f"{os.path.dirname(os.path.realpath(__file__))}/../map_verification/test_maps"), subdir=True
                )
            ),
        )

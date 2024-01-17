import copy
import unittest
from pathlib import Path

from commonroad.common.writer.file_writer_interface import OverwriteExistingFile

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.file_writer import CRDesignerFileWriter
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_scenario,
)


class TestCRDesignerFileReaderWriter(unittest.TestCase):
    """
    Class to test the CR Designer file reader and writer extension to verify and repair a scenario.
    """

    def test_crdesigner_file_reader(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
            Path(__file__).parent.parent / "map_verification/test_maps/CHN_Merging-1.xml"
        )
        # opening it without verifying and repairing
        scenario = crdesigner_reader.open(verify_repair_scenario=False)[0]
        # opening it with verifying and repairing
        repaired_scenario = crdesigner_reader.open(verify_repair_scenario=True)[0]
        self.assertNotEqual(scenario, repaired_scenario)
        self.assertEqual(repaired_scenario, verify_and_repair_scenario(scenario)[0])

        # opening it with the same projection
        projected_scenario = crdesigner_reader.open(
            target_projection=scenario.location.geo_transformation.geo_reference
        )[0]
        # scenarios should be the same as the proj_string is the same
        self.assertEqual(projected_scenario, scenario)

        # opening it with the different projection
        projected_scenario = crdesigner_reader.open(target_projection="+proj=utm +zone=30 +ellps=WGS84")[0]
        # scenarios should not be the same as the projections are different
        self.assertNotEqual(projected_scenario, scenario)

    def test_crdesigner_file_writer(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
            Path(__file__).parent.parent / "map_verification/test_maps/CHN_Merging-1.xml"
        )
        scenario, pp = crdesigner_reader.open()

        # writing it without verifying and repairing
        CRDesignerFileWriter(scenario, pp).write_to_file(
            str(Path(__file__).parent / "scenario.xml"), overwrite_existing_file=OverwriteExistingFile.ALWAYS
        )
        reader_scenario = CRDesignerFileReader(Path(__file__).parent / "scenario.xml").open()[0]

        # testing non verified and repaired scenarios
        self.assertEqual(scenario, reader_scenario)

        # writing the original scenario with verifying and repairing flag
        CRDesignerFileWriter(scenario, pp).write_to_file(
            str(Path(__file__).parent / "writer_repaired_scenario.xml"),
            verify_repair_scenario=True,
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
        )

        # writing the verified and repaired scenario directly
        verified_and_repaired_scenario = verify_and_repair_scenario(copy.deepcopy(scenario))[0]
        CRDesignerFileWriter(verified_and_repaired_scenario, pp).write_to_file(
            str(Path(__file__).parent / "function_repaired_scenario.xml"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
        )

        # compare the two verified and repaired scenarios
        writer_repaired_scenario = CRDesignerFileReader(Path(__file__).parent / "writer_repaired_scenario.xml").open()[
            0
        ]
        function_repaired_scenario = CRDesignerFileReader(
            Path(__file__).parent / "function_repaired_scenario.xml"
        ).open()[0]
        self.assertNotEqual(scenario, writer_repaired_scenario)
        self.assertNotEqual(scenario, function_repaired_scenario)
        self.assertEqual(writer_repaired_scenario, function_repaired_scenario)

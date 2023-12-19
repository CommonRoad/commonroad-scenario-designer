import os
import unittest
from pathlib import Path

from commonroad.common.writer.file_writer_interface import OverwriteExistingFile

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.file_writer import CRDesignerFileWriter
from crdesigner.verification_repairing.map_verification_repairing import verify_and_repair_scenario


class TestCRDesignerFileReaderWriter(unittest.TestCase):
    """
    Class to test the CR Designer file reader and writer extension to verify and repair a scenario.
    """
    def test_crdesigner_file_reader(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
                Path(__file__).parent.parent/"map_verification/test_maps/CHN_Merging-1.xml")
        print("PATH: ", Path(__file__))
        # opening it without verifying and repairing
        scenario = crdesigner_reader.open(verify_repair_scenario=False)[0]
        # opening it with verifying and repairing
        repaired_scenario = crdesigner_reader.open(verify_repair_scenario=True)[0]

        self.assertNotEqual(scenario, repaired_scenario)
        self.assertEqual(repaired_scenario, verify_and_repair_scenario(scenario)[0])

    def test_crdesigner_file_writer(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
                Path(__file__).parent.parent/"map_verification/test_maps/CHN_Merging-1.xml")
        scenario, pp = crdesigner_reader.open()
        # writing it without verifying and repairing
        CRDesignerFileWriter(scenario, pp).write_to_file(str(Path(__file__).parent/"scenario.xml"),
                                                         overwrite_existing_file=OverwriteExistingFile.ALWAYS)
        # writing it with verifying and repairing, this alters the scenario
        CRDesignerFileWriter(scenario, pp).write_to_file(str(Path(__file__).parent/"repaired_scenario.xml"),
                                                         verify_repair_scenario=True,
                                                         overwrite_existing_file=OverwriteExistingFile.ALWAYS)
        # reading the original scenario
        original_scenario = CRDesignerFileReader(Path(__file__).parent/"scenario.xml").open()[0]

        # reading the verified and repaired scenario
        repaired_scenario, rpp = CRDesignerFileReader(Path(__file__).parent/"repaired_scenario.xml").open()
        self.assertNotEqual(original_scenario, repaired_scenario)

        # writing the repaired original file
        CRDesignerFileWriter(verify_and_repair_scenario(original_scenario)[0], pp).write_to_file(str(
                Path(__file__).parent/"original_repaired_scenario.xml"),
                overwrite_existing_file=OverwriteExistingFile.ALWAYS)
        # reading the repaired original file
        original_repaired_scenario = CRDesignerFileReader(Path(__file__).parent/ "original_repaired_scenario.xml").open()[0]
        self.assertEqual(original_repaired_scenario, repaired_scenario)


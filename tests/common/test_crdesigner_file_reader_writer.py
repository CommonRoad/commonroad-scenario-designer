import copy
import unittest
from datetime import datetime
from pathlib import Path

import pytest
from commonroad.common.util import FileFormat, Time
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.scenario.scenario import Tag

from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.file_writer import CRDesignerFileWriter
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_map,
    verify_and_repair_scenario,
)


class TestCRDesignerFileReader(unittest.TestCase):
    """
    Class to test the CR Designer file reader, a CommonRoad-io FileReader with the extension to optionally
    verify and repair a scenario.
    """

    def setUp(self) -> None:
        self.crdesigner_reader = CRDesignerFileReader()
        self.filename_2020a = (
            Path(__file__).parent.parent / "map_verification/test_maps/CHN_Merging-1.xml"
        )
        self.filename_map = (
            Path(__file__).parent / "test_files_new_format/USA_Peach-1/USA_Peach-1.pb"
        )
        self.filename_dynamic = (
            Path(__file__).parent / "test_files_new_format/USA_Peach-1/USA_Peach-1_1_T-1.pb"
        )
        self.filename_scenario = (
            Path(__file__).parent / "test_files_new_format/USA_Peach-1/USA_Peach-1_1_T-1-SC.pb"
        )

    def test_crdesigner_file_reader_open_2020a(self):
        self.crdesigner_reader.filename_2020a = self.filename_2020a
        time = datetime.now()
        date = Time(time.hour, time.minute, time.day, time.month, time.year)
        # opening it without verifying and repairing
        scenario = self.crdesigner_reader.open(verify_repair_scenario=False)[0]
        scenario.file_information.date = date
        # opening it with verifying and repairing
        repaired_scenario = self.crdesigner_reader.open(verify_repair_scenario=True)[0]
        self.assertNotEqual(scenario, repaired_scenario)
        self.assertEqual(repaired_scenario, verify_and_repair_scenario(scenario)[0])

        # opening it with the same projection
        projected_scenario = self.crdesigner_reader.open(
            target_projection=scenario.lanelet_network.location.geo_transformation.geo_reference
        )[0]
        projected_scenario.file_information.date = date
        # scenarios should be the same as the proj_string is the same
        self.assertEqual(projected_scenario, scenario)

        # opening it with the different projection
        projected_scenario = self.crdesigner_reader.open(
            target_projection="+proj=utm +zone=30 +ellps=WGS84"
        )[0]
        # scenarios should not be the same as the projections are different
        self.assertNotEqual(projected_scenario, scenario)

        # test when the 2020a xml filename is missing
        self.crdesigner_reader.filename_2020a = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open()
        assert str(exc_info.value) == "Filename of the 2020a xml file is missing"

        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_lanelet_network()
        assert str(exc_info.value) == "Filename of the 2020a xml file is missing"

    def test_crdesigner_file_reader_open_map(self):
        self.crdesigner_reader.filename_map = self.filename_map
        map_lanelet_network = self.crdesigner_reader.open_map()[0]

        # asserting that just opening the lanelet network does not verify and repair it
        self.assertNotEqual(map_lanelet_network, verify_and_repair_map(map_lanelet_network)[0])

        # opening the verified and repaired lanelet network
        map_lanelet_network_repaired = self.crdesigner_reader.open_map(
            verify_repair_lanelet_network=True
        )[0]
        # asserting that the verifying and repairing the lanelet network works
        self.assertEqual(
            map_lanelet_network_repaired, verify_and_repair_map(map_lanelet_network)[0]
        )

        # opening the map with the projection
        projected_lanelet_network = self.crdesigner_reader.open_map(
            target_projection="+proj=utm +zone=30 +ellps=WGS84"
        )[0]
        # lanelet networks should be the same as map does not have base projection string
        self.assertEqual(projected_lanelet_network, map_lanelet_network)

        # test when the map is missing
        self.crdesigner_reader.filename_map = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_map()
        assert str(exc_info.value) == "Filename of the 2024 map file is missing"

    def test_crdesigner_file_reader_open_map_dynamic(self):
        self.crdesigner_reader.filename_map = self.filename_map
        self.crdesigner_reader.filename_dynamic = self.filename_dynamic

        # opening the scenario without verify and repair
        scenario = self.crdesigner_reader.open_map_dynamic()

        # asserting that just opening the scenario does not verify and repair it
        self.assertNotEqual(scenario, verify_and_repair_scenario(scenario)[0])

        # opening the verified and repaired scenario
        scenario_repaired = self.crdesigner_reader.open_map_dynamic(
            verify_repair_lanelet_network=True
        )

        # asserting that the verifying and repairing the scenario works
        self.assertEqual(scenario_repaired, verify_and_repair_scenario(scenario)[0])

        # opening the map_dynamic with the projection
        projected_scenario = self.crdesigner_reader.open_map_dynamic(
            target_projection="+proj=utm +zone=30 +ellps=WGS84"
        )
        # scenarios should be the same as the scenario does not have base projection string
        self.assertEqual(projected_scenario, scenario)

        # test when the map is missing
        self.crdesigner_reader.filename_map = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_map_dynamic()
        assert str(exc_info.value) == "Filename of the 2024 map file is missing"

        # test when the dynamic is missing
        self.crdesigner_reader.filename_map = self.filename_map
        self.crdesigner_reader.filename_dynamic = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_map_dynamic()
        assert str(exc_info.value) == "Filename of the 2024 dynamic file is missing"

    def test_crdesigner_file_reader_open_all(self):
        self.crdesigner_reader.filename_map = self.filename_map
        self.crdesigner_reader.filename_dynamic = self.filename_dynamic
        self.crdesigner_reader.filename_scenario = self.filename_scenario

        # opening the scenario without verify and repair
        scenario = self.crdesigner_reader.open_all()[0]

        # asserting that just opening the scenario does not verify and repair it
        self.assertNotEqual(scenario, verify_and_repair_scenario(scenario)[0])

        # opening the verified and repaired scenario
        scenario_repaired = self.crdesigner_reader.open_all(verify_repair_lanelet_network=True)[0]

        # asserting that the verifying and repairing the scenario works
        self.assertEqual(scenario_repaired, verify_and_repair_scenario(scenario)[0])

        # opening all with the projection
        projected_scenario = self.crdesigner_reader.open_all(
            target_projection="+proj=utm +zone=30 +ellps=WGS84"
        )[0]
        # scenarios should be the same as the scenario does not have base projection string
        self.assertEqual(projected_scenario, scenario)

        # test when the map is missing
        self.crdesigner_reader.filename_map = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_map_dynamic()
        assert str(exc_info.value) == "Filename of the 2024 map file is missing"

        # test when the dynamic is missing
        self.crdesigner_reader.filename_map = self.filename_map
        self.crdesigner_reader.filename_dynamic = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_map_dynamic()
        assert str(exc_info.value) == "Filename of the 2024 dynamic file is missing"

        # test when the scenario is missing
        self.crdesigner_reader.filename_map = self.filename_map
        self.crdesigner_reader.filename_dynamic = self.filename_dynamic
        self.crdesigner_reader.filename_scenario = None
        with pytest.raises(NameError) as exc_info:
            self.crdesigner_reader.open_all()
        assert str(exc_info.value) == "Filename of the 2024 scenario file is missing"


class TestCRDesignerFileWriter(unittest.TestCase):
    """
    Class to test the CR Designer file writer, a CommonRoad-io FileWriter with the extension to optionally
    verify and repair a scenario.
    """

    def test_crdesigner_file_write_to_file(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
            Path(__file__).parent.parent / "map_verification/test_maps/CHN_Merging-1.xml"
        )
        scenario, pp = crdesigner_reader.open()

        # writing it without verifying and repairing
        CRDesignerFileWriter(scenario, pp).write_to_file(
            str(Path(__file__).parent / "scenario.xml"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
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
        writer_repaired_scenario = CRDesignerFileReader(
            Path(__file__).parent / "writer_repaired_scenario.xml"
        ).open()[0]
        function_repaired_scenario = CRDesignerFileReader(
            Path(__file__).parent / "function_repaired_scenario.xml"
        ).open()[0]
        self.assertNotEqual(scenario, writer_repaired_scenario)
        self.assertNotEqual(scenario, function_repaired_scenario)
        self.assertEqual(writer_repaired_scenario, function_repaired_scenario)

    def test_crdesigner_write_map_to_file(self):
        # reading a scenario
        crdesigner_reader = CRDesignerFileReader(
            Path(__file__).parent.parent / "map_verification/test_maps/CHN_Merging-1.xml"
        )
        scenario, pp = crdesigner_reader.open()
        crdesigner_writer = CRDesignerFileWriter(scenario, pp, file_format=FileFormat.PROTOBUF)

        # write the unrepaired map
        crdesigner_writer.write_map_to_file(
            str(Path(__file__).parent / "CHN_Merging-1.pb"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
        )
        # write the unrepaired map and repair it in the file writer (flag set to true)
        crdesigner_writer.write_map_to_file(
            str(Path(__file__).parent / "CHN_Merging_Flag_Repaired-1.pb"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
            verify_repair_map=True,
        )
        # read the unrepaired map with the new format map reader
        map_scenario_2024 = CRDesignerFileReader(
            filename_map=Path(__file__).parent / "CHN_Merging-1.pb"
        ).open_map()[0]

        # read the repaired map with the new format map reader
        map_scenario_flag_repaired_2024 = CRDesignerFileReader(
            filename_map=Path(__file__).parent / "CHN_Merging_Flag_Repaired-1.pb"
        ).open_map()[0]

        # check that the repaired and unrepaired maps are not the same
        self.assertNotEqual(map_scenario_2024, map_scenario_flag_repaired_2024)

        # write the already repaired map (flag set to false)
        crdesigner_writer.write_map_to_file(
            str(Path(__file__).parent / "CHN_Merging_Repaired-1.pb"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
        )

        # read the repaired map
        map_scenario_repaired_2023 = CRDesignerFileReader(
            filename_map=Path(__file__).parent / "CHN_Merging_Repaired-1.pb"
        ).open_map()[0]

        # check that the 2 repaired maps are the same
        self.assertEqual(map_scenario_repaired_2023, map_scenario_flag_repaired_2024)

        # read the USA peach protobuf map
        crdesigner_reader = CRDesignerFileReader(
            filename_map=Path(__file__).parent / "test_files_new_format/USA_Peach-1/USA_Peach-1.pb",
            filename_dynamic=Path(__file__).parent
            / "test_files_new_format/USA_Peach-1/USA_Peach-1_1_T-1.pb",
            filename_scenario=Path(__file__).parent
            / "test_files_new_format/USA_Peach-1/USA_Peach-1_1_T-1-SC.pb",
        )
        ll_peach, pps, _ = crdesigner_reader.open_all()
        crdesigner_writer = CRDesignerFileWriter(
            ll_peach, pps, tags={Tag.INTERSTATE}, file_format=FileFormat.PROTOBUF
        )

        # write the map with different projection
        crdesigner_writer.write_map_to_file(
            str(Path(__file__).parent / "USA_DifferentProjectionPeach-1.pb"),
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
            target_projection="+proj=utm +zone=30 +ellps=WGS84",
        )
        different_ll_peach = CRDesignerFileReader(
            filename_map=Path(__file__).parent / "USA_DifferentProjectionPeach-1.pb"
        ).open_map()[0]

        # check that the 2 repaired lanelet networks are not the same
        self.assertNotEqual(different_ll_peach, ll_peach)

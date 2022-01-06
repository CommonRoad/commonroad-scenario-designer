import os
import unittest
import time
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag, Scenario

from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from tests.map_conversion.utils import elements_equal

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.4"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class TestOpenDriveToCommonRoadConversion(unittest.TestCase):
    """Basic test with a junction in the middle."""

    @staticmethod
    def load_and_convert_opendrive(xodr_file_name: str) -> Scenario:
        cwd_path = os.path.dirname(os.path.abspath(__file__))
        out_path = cwd_path + "/.pytest_cache/opendrive"
        if not os.path.isdir(out_path):
            os.makedirs(out_path)
        else:
            for (dir_path, _, filenames) in os.walk(out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dir_path, file))

        return opendrive_to_commonroad(os.path.dirname(os.path.realpath(__file__)) +
                                       "/opendrive_test_files/{}.xodr".format(xodr_file_name))

    def compare_maps(self, file_name: str) -> bool:
        """
        Test if the scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        xml_output_name = file_name

        with open(os.path.dirname(os.path.realpath(__file__))
                  + f"/opendrive_test_files/{xml_output_name}.xml", "r", ) as fh:
            parser = etree.XMLParser(remove_blank_text=True)
            tree_import = etree.parse(fh, parser=parser).getroot()
            writer = CommonRoadFileWriter(scenario=self.load_and_convert_opendrive(file_name),
                                          planning_problem_set=PlanningProblemSet(), author="", affiliation="",
                                          source="CommonRoad Scenario Designer", tags={Tag.URBAN, Tag.HIGHWAY}, )
            writer.write_to_file(
                    os.path.dirname(os.path.abspath(__file__)) + "/.pytest_cache" + "/" + xml_output_name + ".xml",
                    OverwriteExistingFile.ALWAYS)

            # set same date so this won't change the comparison
            date = time.strftime("%Y-%m-%d", time.localtime())
            tree_import.set("date", date)
            writer.root_node.set("date", date)

            generate_unique_id(0)  # reset ID counter for next test case

            # compare both element trees
            return elements_equal(tree_import, writer.root_node)

    def test_basic_opendrive(self):
        """Basic test with a junction in the middle."""
        self.assertTrue(self.compare_maps("opendrive-1"))

    def test_sued_tangente(self):
        """Includes roads with multiple lane sections and
        lane sections with multiple width sections.
        This should be split into multiple tests in the future."""
        self.assertTrue(self.compare_maps("KA-Suedtangente-atlatec"))

    def test_culdesac(self):
        """Two adjacent lanes with same successor should not be mistaken
        as merging lanes!"""
        self.assertTrue(self.compare_maps("CulDeSac"))

    def test_complex_crossing(self):
        self.assertTrue(self.compare_maps("CrossingComplex8Course"))

    def test_roundabout(self):
        self.assertTrue(self.compare_maps("Roundabout8Course"))

    def test_right_width_coefficients(self):
        """Test if algorithm selects the right width index if it is ambiguous.
        This was an error of an github issue for town03.xodr.
        For multiple width coefficients, at the border between the interval of two
        both could apply and it was previously not rightly determined which to select.
        """
        self.assertTrue(self.compare_maps("town03_right_width_coefficient"))

    def test_zero_width_coefficients(self):
        """Test if this converter discards lanes which have zero width everywhere.
        In this case, it is the lane -1 of road 1."""
        self.assertTrue(self.compare_maps("zero_width_lanes_map"))

    def test_poly3_and_border_record(self):
        """Test if the program convert Poly3 Geometry and whether it can handle
        border records instead of width records."""
        self.assertTrue(self.compare_maps("poly3_and_border_record"))

    def test_four_way_signal(self):
        self.assertTrue(self.compare_maps("FourWaySignal"))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-

import os
import unittest
import time
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from crdesigner.conversion.common.utils import generate_unique_id
from crdesigner.conversion.opendrive.opendriveparser.parser import parse_opendrive
from crdesigner.io.opendrive_convert import convert_opendrive
from test.utils import elements_equal

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


def setUp(xodr_file_name):
    """Load the xodr file and create the scenario.

    """
    # if not xml_output_name:
    # xml_output_name = xodr_file_name
    cwd_path = os.path.dirname(os.path.abspath(__file__))
    out_path = cwd_path + "/.pytest_cache"
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
    else:
        for (dirpath, dirnames, filenames) in os.walk(out_path):
            for file in filenames:
                if file.endswith('.xml'):
                    os.remove(os.path.join(dirpath, file))

    with open(
            os.path.dirname(os.path.realpath(__file__))
            + f"/opendrive_test_files/{xodr_file_name}.xodr",
            "r",
    ) as fh:
        opendrive = parse_opendrive(etree.parse(fh).getroot())
    return convert_opendrive(opendrive)


def test_opendrive_scenario(xodr_file_name):
    """Test if the scenario is equal to the loaded xml file.
    Disregard the different dates.

    """
    xml_output_name = xodr_file_name
    generate_unique_id(0)
    with open(
            os.path.dirname(os.path.realpath(__file__))
            + f"/opendrive_test_files/{xml_output_name}.xml",
            "r",
    ) as fh:
        parser = etree.XMLParser(remove_blank_text=True)
        tree_import = etree.parse(fh, parser=parser).getroot()
        writer = CommonRoadFileWriter(
            scenario=setUp(xodr_file_name),
            planning_problem_set=PlanningProblemSet(),
            author="",
            affiliation="",
            source="CommonRoad Scenario Designer",
            tags={Tag.URBAN, Tag.HIGHWAY},
        )
        writer.write_to_file(
            os.path.dirname(os.path.abspath(__file__)) + "/.pytest_cache" + "/" + xml_output_name + ".xml",
            OverwriteExistingFile.ALWAYS)

        # set same date so this won't change the comparison
        date = time.strftime("%Y-%m-%d", time.localtime())
        tree_import.set("date", date)
        writer.root_node.set("date", date)

        # compare both element trees
        return elements_equal(tree_import, writer.root_node)


class TestOpenDrive(unittest.TestCase):
    """Basic test with a junction in the middle."""

    def TestBasicOpenDrive(self):
        """Basic test with a junction in the middle."""

        self.assertTrue(test_opendrive_scenario("opendrive-1"))

    def TestSuedTangente(self):
        """Includes roads with multiple lane sections and
        lane sections with multiple width sections.
        This should be split into multiple tests in the future."""

        self.assertTrue(test_opendrive_scenario("KA-Suedtangente-atlatec"))

    def TestCulDeSac(self):
        """Two adjacent lanes with same successor should not be mistaken
        as merging lanes!"""

        self.assertTrue(test_opendrive_scenario("CulDeSac"))

    def TestComplexCrossing(self):

        self.assertTrue(test_opendrive_scenario("CrossingComplex8Course"))

    def TestRoundabout(self):

        self.assertTrue(test_opendrive_scenario("Roundabout8Course"))

    def TestRightWidthCoefficients(self):
        """Test if algorithm selects the right width index if it is ambiguous.
        This was an error of an github issue for town03.xodr.
        For multiple width coefficients, at the border between the interval of two
        both could apply and it was previously not rightly determined which to select.
        """

        self.assertTrue(test_opendrive_scenario("town03_right_width_coefficient"))

    def TestZeroWidthCoefficients(self):
        """Test if this converter discards lanes which have zero width everywhere.
        In this case, it is the lane -1 of road 1."""

        self.assertTrue(test_opendrive_scenario("zero_width_lanes_map"))
        #xml_output_name = "CulDeSac"

    def TestPoly3AndBorderRecord(self):
        """Test if the program convert Poly3 Geometry and whether it can handle
        border records instead of width records."""

        self.assertTrue(test_opendrive_scenario("poly3_and_border_record"))


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-

"""Test the conversion from an osm file to a CommonRoad xml file."""

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


import os
import unittest
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet

from crdesigner.conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
from test.utils import elements_equal


class TestOSM2CRConversionBaseClass(unittest.TestCase):
    """Test the conversion of a specific osm file by reading it, parsing it
    and then converting it to a CommonRoad file including a scenario.

    This converted scenario should describe the same map as the osm file.
    """

    __test__ = False

    osm_file_name = None
    proj_string = ""
    xml_output_name = None
    cwd_path = None
    out_path = None
    scenario = None

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        if not self.xml_output_name:
            self.xml_output_name = self.osm_file_name
        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        self.out_path = self.cwd_path + "/.pytest_cache"
        if not os.path.isdir(self.out_path):
            os.makedirs(self.out_path)
        else:
            for (dirpath, dirnames, filenames) in os.walk(self.out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dirpath, file))

        file_in = f"{os.path.dirname(os.path.realpath(__file__))}/lanelet_lanelet2_test_files/{self.osm_file_name}.osm"
        parser = Lanelet2Parser(etree.parse(file_in).getroot())
        osm = parser.parse()
        osm2l = Lanelet2CRConverter(proj_string="+proj=utm +zone=32 +ellps=WGS84")
        self.scenario = osm2l(osm)

    def test_osm_scenario(self):
        """Test if converted scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        fh = f"{os.path.dirname(os.path.realpath(__file__))}/lanelet_lanelet2_test_files/{self.xml_output_name}.xml"
        parser = etree.XMLParser(remove_blank_text=True)
        tree_import = etree.parse(fh, parser=parser).getroot()
        writer = CommonRoadFileWriter(
            scenario=self.scenario,
            planning_problem_set=PlanningProblemSet(),
            author="",
            affiliation="",
            source="OpenDRIVE 2 Lanelet Converter",
            tags=set(),
        )
        writer.write_to_file(self.out_path + "/" + self.xml_output_name + ".xml", OverwriteExistingFile.ALWAYS)

        # set same date so this won't change the comparison
        tree_import.set("date", "2020-04-14")
        writer.root_node.set("date", "2020-04-14")

        # compare both element trees
        trees_are_equal = elements_equal(tree_import, writer.root_node)
        self.assertTrue(trees_are_equal)


class TestUrbanLanelets(TestOSM2CRConversionBaseClass):
    """Simple test case file which includes succesors and
    predecessors and adjacencies."""

    __test__ = True
    osm_file_name = "urban-1_lanelets_utm"


class TestMergingLanelets(TestOSM2CRConversionBaseClass):
    """Basic test file including some splits and joins."""

    __test__ = True
    osm_file_name = "merging_lanelets_utm"


class TestFeatureLanelet2Lanelets(TestOSM2CRConversionBaseClass):
    """Basic test file including some splits and joins."""

    __test__ = True
    osm_file_name = "traffic_priority_lanelets_utm"

class TestSpeedLimitConversion(TestOSM2CRConversionBaseClass):
    """Basic test file including some splits and joins."""

    __test__ = True
    osm_file_name = "traffic_speed_limit_utm"
# -*- coding: utf-8 -*-

"""Test the conversion from an osm file to a CommonRoad xml file."""

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.1.3"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


import os
import unittest
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from opendrive2lanelet.osm.parser import OSMParser
from opendrive2lanelet.osm.osm2lanelet import OSM2LConverter
from test.utils import elements_equal


class TestOSM2CRConversionBaseClass:
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

        with open(
            os.path.dirname(os.path.realpath(__file__))
            + f"/osm_xml_test_files/{self.osm_file_name}.osm",
            "r",
        ) as file_in:
            parser = OSMParser(etree.parse(file_in).getroot())
            osm = parser.parse()
        osm2l = OSM2LConverter(proj_string="+proj=utm +zone=32 +ellps=WGS84")
        self.scenario = osm2l(osm)

    def test_osm_scenario(self):
        """Test if converted scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        with open(
                os.path.dirname(os.path.realpath(__file__))
                + f"/osm_xml_test_files/{self.xml_output_name}.xml",
                "r",
        ) as fh:
            parser = etree.XMLParser(remove_blank_text=True)
            tree_import = etree.parse(fh, parser=parser).getroot()
            writer = CommonRoadFileWriter(
                scenario=self.scenario,
                planning_problem_set=PlanningProblemSet(),
                author="",
                affiliation="",
                source="OpenDRIVE 2 Lanelet Converter",
                tags={Tag.URBAN, Tag.HIGHWAY},
            )
            writer.write_to_file(self.out_path + "/" + self.xml_output_name + ".xml", OverwriteExistingFile.ALWAYS)

            # set same date so this won't change the comparison
            tree_import.set("date", "2020-04-14")
            writer.root_node.set("date", "2020-04-14")

            # compare both element trees
            trees_are_equal = elements_equal(tree_import, writer.root_node)
            self.assertTrue(trees_are_equal)


class TestUrbanLanelets(TestOSM2CRConversionBaseClass, unittest.TestCase):
    """Simple test case file which includes succesors and
    predecessors and adjacencies."""

    __test__ = True
    osm_file_name = "urban-1_lanelets_utm"


class TestMergingLanelets(TestOSM2CRConversionBaseClass, unittest.TestCase):
    """Basic test file including some splits and joins."""

    __test__ = True
    osm_file_name = "merging_lanelets_utm"

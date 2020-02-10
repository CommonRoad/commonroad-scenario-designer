# -*- coding: utf-8 -*-

"""Test the conversion from an osm file to a CommonRoad xml file."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.1.1"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


import os
import unittest
from io import StringIO
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter

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

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
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
            + f"/osm_xml_test_files/{self.osm_file_name}.xml",
            "r",
        ) as fh:

            parser = etree.XMLParser(remove_blank_text=True)
            tree_import = etree.parse(fh, parser=parser).getroot()
        string_io = StringIO()
        writer = CommonRoadFileWriter(
            scenario=self.scenario,
            planning_problem_set=None,
            author="",
            affiliation="",
            source="OSM 2 CommonRoad Converter",
            tags="",
        )
        writer.write_scenario_to_file_io(string_io)
        tree_generated = etree.fromstring(string_io.getvalue(), parser=parser)

        # set same date so this won't change the comparison
        tree_import.set("date", "2018-10-26")
        tree_generated.set("date", "2018-10-26")

        # compare both element trees
        trees_are_equal = elements_equal(tree_import, tree_generated)
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

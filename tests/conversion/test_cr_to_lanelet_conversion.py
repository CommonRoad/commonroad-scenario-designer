# -*- coding: utf-8 -*-

"""Test the conversion from an Commonroad file to an OSM file."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


import os
import unittest
from lxml import etree

from commonroad.common.file_reader import CommonRoadFileReader

from crdesigner.conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter
from tests.conversion.utils import elements_equal

# TODO: write osm_convert method analog to opendrive_convert


class TestCR2OSMConversionBaseClass(unittest.TestCase):
    """Test the conversion of a specific osm file by reading it, parsing it
    and then converting it to a CommonRoad file including a scenario.

    This converted scenario should describe the same map as the osm file.
    """

    __test__ = False

    xml_file_name = None
    proj_string = "+proj=utm +zone=32 +ellps=WGS84"

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        try:
            commonroad_reader = CommonRoadFileReader(
                f"{os.path.dirname(os.path.realpath(__file__))}/lanelet_lanelet2_test_files/{self.xml_file_name}.xml"
            )
            scenario, _ = commonroad_reader.open()
            l2osm = CR2LaneletConverter(self.proj_string)
            self.osm = l2osm(scenario)

        except etree.XMLSyntaxError as xml_error:
            print(f"SyntaxERror: {xml_error}")
            print(
                "There was an error during the loading of the selected CommonRoad file.\n"
            )

    def test_cr_scenario(self):
        """Test if converted scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        fh = f"{os.path.dirname(os.path.realpath(__file__))}/lanelet_lanelet2_test_files/{self.xml_file_name}_from_cr.osm"
        parser = etree.XMLParser(remove_blank_text=True)
        tree_import = etree.parse(fh, parser=parser).getroot()

        # set same date so this won't change the comparison
        tree_import.set("generator", "42")
        self.osm.set("generator", "42")

        # compare both element trees
        trees_are_equal = elements_equal(tree_import, self.osm)
        self.assertTrue(trees_are_equal)


class TestUrbanLanelets(TestCR2OSMConversionBaseClass):
    """Simple test case file which includes succesors and
    predecessors and adjacencies."""

    __test__ = True
    xml_file_name = "urban-1_lanelets_utm"


class TestMergingLanelets(TestCR2OSMConversionBaseClass):
    """Basic test file including some splits and joins."""

    __test__ = True
    xml_file_name = "merging_lanelets_utm"

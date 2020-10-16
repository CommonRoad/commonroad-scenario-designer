# -*- coding: utf-8 -*-
"""Test the conversion from an osm file to a CommonRoad Scenario file."""

__author__ = "Max Frühauf, Fabian Höltke"
__copyright__ = "TUM Cyber-Physical Systems Group"

import os
import unittest
from lxml import etree

import crmapconverter.osm2cr.converter_modules.converter as converter
from test.utils import elements_equal, validate


class TestOSM2CRScenarioBaseClass(unittest.TestCase):
    """Test the conversion from an osm file to the respective commonroad scenario
    """

    __test__ = False

    osm_file_name = None
    proj_string = ""
    xml_output_name = None
    cwd_path = None
    out_path = None
    scenario: converter.GraphScenario = None

    xsd_file_name = "documentation_XML_commonRoad_XSD"

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        if not self.xml_output_name:
            self.xml_output_name = self.osm_file_name

        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        self.out_path = self.cwd_path + "/.pytest_cache"

        path = os.path.dirname(os.path.realpath(
            __file__)) + f"/osm_xml_test_files/{self.osm_file_name}.osm"

        #print("input: " + path)
        #print("output: " + self.out_path)
        self.scenario = converter.GraphScenario(path)

    def test_osm2_cr_conversion_equal(self):
        """Test if the converted scenario is equal to the loaded xml file"""

        # Save scenario to xml file, as converter.GraphScenario offers no way
        # to access the underlying CommonRoadfileWriter
        converted_path = os.path.join(
            self.out_path, self.osm_file_name + "_converted_scenario.xml")
        self.scenario.save_as_cr(converted_path)

        ground_truth_path = os.path.dirname(
            os.path.realpath(__file__)
        ) + f"/osm_xml_test_files/{self.osm_file_name}.xml"
        #print("ground truth: "+ground_truth_path)

        # load saved file & compare to ground truth
        with open(ground_truth_path, "r") as gt, open(converted_path,
                                                      "r") as cv:
            parser = etree.XMLParser(remove_blank_text=True)
            ground_truth = etree.parse(gt, parser=parser).getroot()
            converted = etree.parse(cv, parser=parser).getroot()

            # set same date so this won't change the comparison
            ground_truth.set("date", "2020-04-14")
            converted.set("date", "2020-04-14")
            ground_truth.set("benchmarkID", "DEU_test")
            converted.set("benchmarkID", "DEU_test")

            # compare both element trees
            self.assertTrue(elements_equal(ground_truth, converted))

    def test_osm2_cr_conversion_validates(self):
        """Test if XML format is correct and validates against xsd schema """

        converted_path = os.path.join(
            self.out_path, self.osm_file_name + "_converted_scenario.xml")

        xsd_path = path = os.path.dirname(os.path.realpath(
            __file__)) + f"/osm_xml_test_files/{self.xsd_file_name}.xsd"

        xmlschema_doc = etree.parse(xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        xml_doc = etree.parse(converted_path)

        xmlschema.assertValid(xml_doc)



class TestGarchingIntersection(TestOSM2CRScenarioBaseClass):
    """Testing if a single small intersection can be converted without error"""
    # Don't test, currently not able to convert correctly
    __test__ = False
    osm_file_name = "garching_intersection"


class TestEichstaett(TestOSM2CRScenarioBaseClass):
    """Testing if a small town with traffic lights, complicated road networks
    and large osm filesize can be converted on default settings"""

    __test__ = True
    osm_file_name = "eichstaett"


if __name__ == "__main__":
    unittest.main()

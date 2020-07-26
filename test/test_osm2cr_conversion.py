# -*- coding: utf-8 -*-
"""Test the conversion from an osm file to a CommonRoad Scenario file."""

__author__ = "Max Frühauf"
__copyright__ = "TUM Cyber-Physical Systems Group"

import os
import unittest
from lxml import etree

# import crmapconverter.osm2cr.converter_modules.converter as converter
from test.utils import elements_equal


# class TestOSM2CRScenarioBaseClass(unittest.TestCase):
#     """Test the conversion from an osm file to the respective commonroad scenario
#     """

#     __test__ = False

#     osm_file_name = None
#     proj_string = ""
#     xml_output_name = None
#     cwd_path = None
#     out_path = None
#     scenario: converter.GraphScenario = None

#     def setUp(self):
#         """Load the osm file and convert it to a scenario."""
#         if not self.xml_output_name:
#             self.xml_output_name = self.osm_file_name

#         self.cwd_path = os.path.dirname(os.path.abspath(__file__))
#         self.out_path = self.cwd_path + "/.pytest_cache"

#         if not os.path.isdir(self.out_path):
#             os.makedirs(self.out_path)
#         else:
#             for (dirpath, dirnames, filenames) in os.walk(self.out_path):
#                 for file in filenames:
#                     if file.endswith('.xml'):
#                         os.remove(os.path.join(dirpath, file))

#         path = os.path.dirname(os.path.realpath(
#             __file__)) + f"/osm_xml_test_files/{self.osm_file_name}.osm"
#         self.scenario = converter.GraphScenario(path)

#     def test_osm2_cr_conversion(self):
#         """Test if the converted scenario is equal to the loaded xml file"""

#         # Save scenario to xml file, as converter.GraphScenario offers no way
#         # to access the underlying CommonRoadfileWriter
#         converted_path = os.path.join(
#             self.out_path, self.osm_file_name + "_converted_scenario.xml")
#         self.scenario.save_as_cr(converted_path)

#         ground_truth_path = os.path.dirname(
#             os.path.realpath(__file__)
#         ) + f"/osm_xml_test_files/{self.osm_file_name}_osm2cr.xml"

#         # load saved file & compare to ground truth
#         with open(ground_truth_path, "r") as gt, open(converted_path,
#                                                       "r") as cv:
#             parser = etree.XMLParser(remove_blank_text=True)
#             ground_truth = etree.parse(gt, parser=parser).getroot()
#             converted = etree.parse(cv, parser=parser).getroot()

#             # set same date so this won't change the comparison
#             ground_truth.set("date", "2020-04-14")
#             converted.set("date", "2020-04-14")

#             # compare both element trees
#             self.assertTrue(elements_equal(ground_truth, converted))


# class TestUrbanScenario(TestOSM2CRScenarioBaseClass):
#     """Copied to prevent regression from test_osm_to_cr_lanelet_conversion.py"""
#     __test__ = True
#     osm_file_name = "urban-1_lanelets_utm"

# class TestMergingLaneletsScenario(TestOSM2CRScenarioBaseClass):
#     """Copied to prevent regression from test_osm_to_cr_lanelet_conversion.py"""
#     __test__ = True
#     osm_file_name = "merging_lanelets_utm"


# class TestEichstaett(TestOSM2CRScenarioBaseClass):
#     """Testing if a small town with traffic lights, complicated road networks 
#     and large osm filesize can be correctly converted"""

#     __test__ = True
#     osm_file_name = "eichstaett"

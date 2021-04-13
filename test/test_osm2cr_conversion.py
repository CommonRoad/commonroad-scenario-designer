# -*- coding: utf-8 -*-
"""Test the conversion from an osm file to a CommonRoad Scenario file."""

__author__ = "Max Frühauf, Fabian Höltke"
__copyright__ = "TUM Cyber-Physical Systems Group"

import os
import unittest
import math
from lxml import etree

import crdesigner.conversion.osm2cr.converter_modules.converter as converter
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile


class TestOSM2CRScenarioBaseClass(unittest.TestCase):
    """Test the conversion from an osm file to the respective commonroad scenario
    """

    __test__ = False

    osm_file_name = None
    proj_string = ""
    xml_output_name = None
    cwd_path = None
    out_path = None
    converted_path = None
    scenario: converter.GraphScenario = None

    commonRoad_scenario = None
    commonRoad_planning_problem = None

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        if not self.xml_output_name:
            self.xml_output_name = self.osm_file_name

        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        self.out_path = self.cwd_path + "/.pytest_cache/"

        path = os.path.dirname(os.path.realpath(
            __file__)) + f"/osm_test_files/{self.osm_file_name}.osm"

        assert self.out_path is not None
        assert self.osm_file_name is not None
        self.converted_path = os.path.join(
            self.out_path, self.osm_file_name + "_converted_scenario.xml")

        # create and save converter scenario
        self.scenario = converter.GraphScenario(path)
        self.scenario.save_as_cr(self.converted_path)

        self.commonRoad_scenario, self.commonRoad_planning_problem = CommonRoadFileReader(
            self.converted_path).open()

    # def test_osm2cr_conversion_equal(self):
    #     """Test if the converted scenario is equal to the loaded xml file"""
    #         # Don't test, ground truth has still converting errors

    #     ground_truth_path = os.path.dirname(
    #         os.path.realpath(__file__)
    #     ) + f"/osm_test_files/{self.osm_file_name}.xml"

    #     # load saved file & compare to ground truth
    #     with open(ground_truth_path, "r") as gt, open(self.converted_path,
    #                                                   "r") as cv:
    #         parser = etree.XMLParser(remove_blank_text=True)
    #         ground_truth = etree.parse(gt, parser=parser).getroot()
    #         converted = etree.parse(cv, parser=parser).getroot()

    #         # set same date so this won't change the comparison
    #         ground_truth.set("date", "2020-04-14")
    #         converted.set("date", "2020-04-14")
    #         ground_truth.set("benchmarkID", "DEU_test")
    #         converted.set("benchmarkID", "DEU_test")

    #         # compare both element trees
    #         self.assertTrue(elements_equal(ground_truth, converted))

    def test_osm2cr_conversion_ids(self):
        """Test if Scenario IDs are correctly ordered ascending """

        parser = etree.XMLParser(remove_blank_text=True)
        converted = etree.parse(self.converted_path, parser=parser).getroot()

        # test ascending lanelet ids
        id_counter = 0
        for element in converted.iter('lanelet'):
            self.assertGreater(int(element.attrib['id']), id_counter)
            id_counter = int(element.attrib['id'])
        # test ascending traffic sign / traffic light ids
        id_counter = 0
        for element in converted.iter('trafficSign'):
            self.assertGreater(int(element.attrib['id']), id_counter)
            id_counter = int(element.attrib['id'])
        for element in converted.iter('trafficLight'):
            self.assertGreater(int(element.attrib['id']), id_counter)
            id_counter = int(element.attrib['id'])
        # test ascending intersection ids
        id_counter = 0
        for element in converted.iter('intersection'):
            self.assertGreater(int(element.attrib['id']), id_counter)
            id_counter = int(element.attrib['id'])

    def test_osm2cr_conversion_geonames(self):
        """Test if Geonames username is set in config. In default settings, it should be not"""

        parser = etree.XMLParser(remove_blank_text=True)
        converted = etree.parse(self.converted_path, parser=parser).getroot()

        location = converted.find('location')
        # test geonamesID
        self.assertEqual(location.find('geoNameId').text, '-999')
        # test if lat was set
        self.assertNotEqual(location.find('gpsLatitude').text, '999')
        # test if lng was set
        self.assertNotEqual(location.find('gpsLongitude').text, '999')

    def test_osm2cr_conversion_lanewith(self):
        """Test if every lanelet is wider than the given minimum distance of 2.5 meters"""

        min_distance = 2.5

        for lanelet in self.commonRoad_scenario.lanelet_network.lanelets:
            for l_v, r_v in zip(lanelet.left_vertices, lanelet.right_vertices):
                distance = math.sqrt((r_v[0]-l_v[0])**2 + (r_v[1]-l_v[1])**2)
                self.assertGreaterEqual(distance, min_distance)

    def test_osm2cr_scenerio_write_validates(self):
        """Test if created CommonRoad scenario validates"""

        fw = CommonRoadFileWriter(
            scenario=self.commonRoad_scenario,
            planning_problem_set=self.commonRoad_planning_problem)
        fw.write_to_file(
            filename=self.out_path+self.osm_file_name+"_written.xml",
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
            check_validity=True)


class TestGarchingIntersection(TestOSM2CRScenarioBaseClass):
    """Testing if a single small intersection can be converted without error"""
    # Warning, ground truth has mayor converting errors

    __test__ = True
    osm_file_name = "garching_intersection"


class TestHaimhausen(TestOSM2CRScenarioBaseClass):
    """Testing if a small town with traffic lights, complicated road networks
    and large osm filesize can be converted on default settings"""

    __test__ = True
    osm_file_name = "haimhausen"

# class TestMunich(TestOSM2CRScenarioBaseClass):
#     """Testing if a larger intersection with many lanes, traffic lights and signs
#     can be converted on default settings"""
#
#     __test__ = True
#     osm_file_name = "munich"


if __name__ == "__main__":
    unittest.main()

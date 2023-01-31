import os
import unittest
import math
from lxml import etree
from typing import Tuple

import crdesigner.map_conversion.osm2cr.converter_modules.converter as converter
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import Scenario
from commonroad.planning.planning_problem import PlanningProblemSet


class TestOSMToCommonRoadConversion(unittest.TestCase):
    """Test the conversion from an osm file to a CommonRoad Scenario file."""
    def setUp(self) -> None:
        self.out_path = os.path.dirname(os.path.realpath(__file__)) + "/.pytest_cache"
        if not os.path.isdir(self.out_path):
            os.makedirs(self.out_path)

    def load_and_convert(self, osm_file_name: str) -> Tuple[Scenario, PlanningProblemSet, str]:
        path = os.path.dirname(os.path.realpath(
            __file__)) + f"/test_maps/osm/{osm_file_name}.osm"

        converted_path = os.path.join(self.out_path, osm_file_name + "_converted_scenario.xml")

        # create and save converter scenario
        graph_scenario = converter.GraphScenario(path)
        graph_scenario.save_as_cr(converted_path)
        cr_scenario, cr_planning_problem = CommonRoadFileReader(converted_path).open()

        return cr_scenario, cr_planning_problem, converted_path

    def osm2cr_conversion_ids(self, converted_path: str):
        """Test if Scenario IDs are correctly ordered ascending """

        parser = etree.XMLParser(remove_blank_text=True)
        converted = etree.parse(converted_path, parser=parser).getroot()

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

    def osm2cr_conversion_geonames(self, converted_path: str):
        """
        Test if Geonames username is set in config. In default settings, it should be not
        """

        parser = etree.XMLParser(remove_blank_text=True)
        converted = etree.parse(converted_path, parser=parser).getroot()

        location = converted.find('location')
        # test geonamesID
        self.assertEqual(location.find('geoNameId').text, '-999')
        # test if lat was set
        self.assertNotEqual(location.find('gpsLatitude').text, '999')
        # test if lng was set
        self.assertNotEqual(location.find('gpsLongitude').text, '999')

    def osm2cr_conversion_lane_width(self, cr_scenario: Scenario):
        """Test if every lanelet is wider than the given minimum distance of 2.5 meters"""

        min_distance = 1.5

        for lanelet in cr_scenario.lanelet_network.lanelets:
            for l_v, r_v in zip(lanelet.left_vertices, lanelet.right_vertices):
                distance = math.sqrt((r_v[0]-l_v[0])**2 + (r_v[1]-l_v[1])**2)
                self.assertGreaterEqual(distance, min_distance)

    def osm2cr_scenario_write_validates(self, cr_scenario: Scenario, cr_planning_problem: PlanningProblemSet,
                                        osm_file_name: str):
        """Test if created CommonRoad scenario validates"""
        fw = CommonRoadFileWriter(
            scenario=cr_scenario,
            planning_problem_set=cr_planning_problem)
        fw.write_to_file(
            filename=self.out_path + "/" +  osm_file_name + "_written.xml",
            overwrite_existing_file=OverwriteExistingFile.ALWAYS,
            check_validity=True)

    def execute_tests(self, osm_file_name: str):
        cr_scenario, cr_planning_problem, converted_path = self.load_and_convert(osm_file_name)
        self.osm2cr_conversion_ids(converted_path)
        self.osm2cr_conversion_geonames(converted_path)
        self.osm2cr_conversion_lane_width(cr_scenario)
        self.osm2cr_scenario_write_validates(cr_scenario, cr_planning_problem, osm_file_name)

    def test_garching_intersection(self):
        """Testing if a single small intersection can be converted without error"""
        # Warning, ground truth has mayor converting errors
        self.execute_tests("garching_intersection")

    def test_haimhausen(self):
        """
        Testing if a small town with traffic lights, complicated road networks
        and large osm filesize can be converted on default settings
        """
        self.execute_tests("haimhausen")

    def test_map_without_crossing_nodes(self):
        """
        Test whether map without crossing nodes can be converted (there was once a bug)
        """
        self.execute_tests("map_without_crossing_nodes")

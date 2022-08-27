import os
import unittest
import numpy as np

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletType, LineMarking
from commonroad.scenario.traffic_sign import TrafficSignIDZamunda

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.5.1"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class TestOpenDriveToCommonRoadConversion(unittest.TestCase):
    """Performs some basic tests of the conversion by comparing what the converter produced with the content
    of the respective .xodr files."""

    def load_and_convert_opendrive(self, xodr_file_name: str) -> Scenario:
        """ Loads a .xodr file and converts it to the commonroad format.
        """
        scenario = opendrive_to_commonroad(os.path.dirname(os.path.realpath(__file__)) +
                                           "/../test_maps/opendrive/{}.xodr".format(xodr_file_name))

        return scenario

    def test_straight_road(self):
        """Test the file straight_road.xodr"""
        name = "straight_road"
        scenario = self.load_and_convert_opendrive(name)

        # test num of lanelets
        network = scenario.lanelet_network
        self.assertEquals(8, len(network.lanelets))

        # test length of road
        np.testing.assert_almost_equal(99.97, network.find_lanelet_by_id(1).distance[3], 2)

        # test lanelet type
        self.assertEquals({LaneletType.DRIVE_WAY}, network.find_lanelet_by_id(1).lanelet_type)
        self.assertEquals({LaneletType.DRIVE_WAY}, network.find_lanelet_by_id(2).lanelet_type)
        self.assertEquals({LaneletType.SHOULDER}, network.find_lanelet_by_id(3).lanelet_type)
        self.assertEquals({LaneletType.SIDEWALK}, network.find_lanelet_by_id(5).lanelet_type)

        # test driving direction
        self.assertFalse(network.find_lanelet_by_id(1).adj_left_same_direction)
        self.assertFalse(network.find_lanelet_by_id(2).adj_left_same_direction)

    def test_four_way_crossing(self):
        """Test the file four_way_crossing.xodr"""
        name = "four_way_crossing"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of stoplines --> Currently fails, stop lines not parsed correctly.
        # Uncomment when stop lines parsed correctly. See issue #364.
        # num_stop_lines = len([l.stop_line for l in network.lanelets if l.stop_line != None])
        # self.assertEquals(4, num_stop_lines)

        # test length of lanelet
        np.testing.assert_almost_equal(network.find_lanelet_by_id(50).distance[2], 90.7, 1)

        # test num of driving lanes
        num_driving_lanes = len([l for l in network.lanelets if l.lanelet_type == {LaneletType.DRIVE_WAY}])
        self.assertEquals(16, num_driving_lanes)

        # test number of traffic lights
        self.assertEquals(12, len(network.traffic_lights))

        # test position of a traffic light
        np.testing.assert_almost_equal(network.find_traffic_light_by_id(2067).position, [0.145, 8.317], 3)

    def test_roundabout(self):
        """Test the file roundabout.xodr"""
        name = "roundabout"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of junctions
        self.assertEquals(4, len(network.intersections))

        # test vertices
        lanelet = network.find_lanelet_by_id(17)
        np.testing.assert_almost_equal(15.268, np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]), 3)
        self.assertEquals(3, len(lanelet.left_vertices))

        lanelet = network.find_lanelet_by_id(4)
        np.testing.assert_almost_equal(3.500, np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]), 3)

        # test length of lane
        np.testing.assert_almost_equal(network.find_lanelet_by_id(17).inner_distance[2], 21.69863, 5)

    def test_crossing_complex_eight_course(self):
        """Test the file CrossingComplex8Course.xodr"""
        name = "CrossingComplex8Course"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of traffic lights
        self.assertEquals(10, len(network.traffic_lights))

        # test number of traffic signs
        self.assertEquals(4, len(network.traffic_signs))

        # test number of priority traffic signs
        self.assertEquals(2, len([s for s in network.traffic_signs if s.traffic_sign_elements[0].traffic_sign_element_id
                                  == TrafficSignIDZamunda.PRIORITY]))

        # test number of yield traffic signs
        self.assertEquals(2, len([s for s in network.traffic_signs if s.traffic_sign_elements[0].traffic_sign_element_id
                                  == TrafficSignIDZamunda.YIELD]))

        # test position of a traffic sign
        np.testing.assert_almost_equal(network.find_traffic_sign_by_id(1).position, [467.03, 498.24], 2)

        # test line marking of a stop lines
        self.assertEquals(LineMarking.SOLID, network.find_lanelet_by_id(16).stop_line.line_marking)

        # test number of driving lanes
        self.assertEquals(20, len([l for l in network.lanelets if l.lanelet_type == {LaneletType.DRIVE_WAY}]))

    def test_cul_de_sac(self):
        """Test the file CulDeSac.xodr"""
        name = "CulDeSac"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of lanelets
        self.assertEquals(3, len(network.lanelets))

        # test vertices of lanelet 1
        self.assertEquals(3, len(network.find_lanelet_by_id(1).left_vertices))
        np.testing.assert_almost_equal([[-72.84, -5.19], [-20.45, -4.77], [31.93, -4.35]],
                                       network.find_lanelet_by_id(1).left_vertices, 2)

        # test successor / predecessor relation
        self.assertListEqual([2], network.find_lanelet_by_id(1).successor)
        self.assertListEqual([1], network.find_lanelet_by_id(2).predecessor)
        self.assertListEqual([3], network.find_lanelet_by_id(2).successor)
        self.assertEquals([2], network.find_lanelet_by_id(3).predecessor)

    def test_four_way_signal(self):
        """Test the file FourWaySignal.xodr"""
        name = "FourWaySignal"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of traffic lights
        self.assertEquals(10, len(network.traffic_lights))

        # test number of traffic signs
        self.assertEquals(2, len(network.traffic_signs))

        # test type of traffic signs
        self.assertEquals(TrafficSignIDZamunda.U_TURN, network.find_traffic_sign_by_id(1).traffic_sign_elements[0]
                          .traffic_sign_element_id)
        self.assertEquals(TrafficSignIDZamunda.U_TURN, network.find_traffic_sign_by_id(2).traffic_sign_elements[0]
                          .traffic_sign_element_id)

        # test position of a traffic light
        np.testing.assert_almost_equal(network.find_traffic_light_by_id(2093).position, [13.15, 12.32], 2)

    def test_opendrive_1(self):
        """Test the file opendrive-1.xodr"""
        name = "opendrive-1"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of driving lanes
        self.assertEquals(12, len([l for l in network.lanelets if l.lanelet_type == {LaneletType.DRIVE_WAY}]))

        # test number of traffic lights
        self.assertEquals(8, len(network.traffic_lights))

        # test correct traffic signs
        self.assertEquals(4, len(network.traffic_signs))
        self.assertEquals(TrafficSignIDZamunda.PRIORITY, network.find_traffic_sign_by_id(1).traffic_sign_elements[0]
                          .traffic_sign_element_id)
        self.assertEquals(TrafficSignIDZamunda.YIELD, network.find_traffic_sign_by_id(2).traffic_sign_elements[0]
                          .traffic_sign_element_id)
        self.assertEquals(TrafficSignIDZamunda.PRIORITY, network.find_traffic_sign_by_id(3).traffic_sign_elements[0]
                          .traffic_sign_element_id)
        self.assertEquals(TrafficSignIDZamunda.YIELD,
                          network.find_traffic_sign_by_id(4).traffic_sign_elements[0].traffic_sign_element_id)

        # test position of traffic sign
        np.testing.assert_almost_equal(network.find_traffic_sign_by_id(3).position, [5.86, 13.78], 2)

        # test number of intersections
        self.assertEquals(1, len(network.intersections))

    def test_poly3_and_border_record(self):
        """Test the file poly3_and_border_record.xodr"""
        name = "poly3_and_border_record"
        scenario = self.load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of sidewalks
        self.assertEquals(8, len([l for l in network.lanelets if l.lanelet_type == {LaneletType.SIDEWALK}]))
        # test number of driving lanes
        self.assertEquals(14, len([l for l in network.lanelets if l.lanelet_type == {LaneletType.DRIVE_WAY}]))


if __name__ == "__main__":
    unittest.main()
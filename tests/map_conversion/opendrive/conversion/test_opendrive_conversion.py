import os
import unittest
from pathlib import Path
import numpy as np

from commonroad.scenario.scenario import Scenario
from commonroad.scenario.lanelet import LaneletType, LineMarking, RoadUser
from commonroad.scenario.traffic_sign import TrafficSignIDZamunda

from crdesigner.config.opendrive_config import open_drive_config as opendrive_config
from crdesigner.config.gui_config import utm_default
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from crdesigner.map_conversion.common.utils import generate_unique_id


def load_and_convert_opendrive(xodr_file_name: str) -> Scenario:
    """ Loads a .xodr file and converts it to the commonroad format."""
    generate_unique_id(0)  # reset ID counter
    opendrive_config.proj_string_odr = utm_default
    scenario = opendrive_to_commonroad(
        Path(os.path.dirname(os.path.realpath(__file__)) + "/../../test_maps/opendrive/{}.xodr".format(xodr_file_name)))

    return scenario


class TestOpenDriveToCommonRoadConversion(unittest.TestCase):
    """Performs some basic tests of the conversion by comparing what the converter produced with the content
    of the respective .xodr files."""

    def test_straight_road(self):
        """Test the file straight_road.xodr"""
        name = "straight_road"
        scenario = load_and_convert_opendrive(name)

        # test num of lanelets
        network = scenario.lanelet_network
        self.assertEqual(8, len(network.lanelets))

        # test length of road
        # test for calculating the vertices without sampling
        np.testing.assert_almost_equal(1.507, network.find_lanelet_by_id(1).distance[3], 3)
        # test for calculating the vertices with sampling
        # np.testing.assert_almost_equal(99.97, network.find_lanelet_by_id(1).distance[3], 2)

        # test that two virtual traffic signs are correctly created
        np.testing.assert_equal(2, len(network.traffic_signs))
        np.testing.assert_equal(True, network.traffic_signs[0].virtual)
        np.testing.assert_equal(True, network.traffic_signs[1].virtual)
        np.testing.assert_almost_equal(network.find_lanelet_by_id(1).center_vertices[0],
                                       network.traffic_signs[0].position)
        np.testing.assert_almost_equal(network.find_lanelet_by_id(2).center_vertices[0],
                                       network.traffic_signs[1].position)
        np.testing.assert_almost_equal(17.881,
                                       float(network.traffic_signs[0].traffic_sign_elements[0].additional_values[0]), 2)
        np.testing.assert_almost_equal(17.881,
                                       float(network.traffic_signs[1].traffic_sign_elements[0].additional_values[0]), 2)

        # test lanelet type
        self.assertEqual({LaneletType.URBAN}, network.find_lanelet_by_id(1).lanelet_type)
        self.assertEqual({LaneletType.URBAN}, network.find_lanelet_by_id(2).lanelet_type)
        self.assertEqual({LaneletType.BORDER}, network.find_lanelet_by_id(3).lanelet_type)
        self.assertEqual({LaneletType.SIDEWALK}, network.find_lanelet_by_id(5).lanelet_type)

        # test driving direction
        self.assertFalse(network.find_lanelet_by_id(1).adj_left_same_direction)
        self.assertFalse(network.find_lanelet_by_id(2).adj_left_same_direction)

    def test_straight_with_speed_limit(self):
        """Test the file straight_with_speed_limit.xodr"""
        name = "straight_with_speed_limit"
        scenario = load_and_convert_opendrive(name)

        np.testing.assert_equal(4, len(scenario.lanelet_network.traffic_signs))
        # 40mph
        np.testing.assert_almost_equal(17.881, float(
                scenario.lanelet_network.traffic_signs[0].traffic_sign_elements[0].additional_values[0]), 2)
        np.testing.assert_almost_equal(17.881, float(
                scenario.lanelet_network.traffic_signs[2].traffic_sign_elements[0].additional_values[0]), 2)
        # 65 mph
        np.testing.assert_almost_equal(29.057, float(
                scenario.lanelet_network.traffic_signs[1].traffic_sign_elements[0].additional_values[0]), 2)
        np.testing.assert_almost_equal(29.057, float(
                scenario.lanelet_network.traffic_signs[3].traffic_sign_elements[0].additional_values[0]), 2)

        np.testing.assert_almost_equal(scenario.lanelet_network.find_lanelet_by_id(3).center_vertices[0],
                                       scenario.lanelet_network.traffic_signs[1].position)
        np.testing.assert_almost_equal(scenario.lanelet_network.find_lanelet_by_id(7).center_vertices[0],
                                       scenario.lanelet_network.traffic_signs[3].position)

    def test_four_way_crossing(self):
        """Test the file four_way_crossing.xodr"""
        name = "four_way_crossing"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of stoplines --> Currently fails, stop lines not parsed correctly.
        # Uncomment when stop lines parsed correctly. See issue #364.
        # num_stop_lines = len([l.stop_line for l in network.lanelets if l.stop_line != None]
        # self.assertEqual(4, num_stop_lines)

        # test length of lanelet
        # test for calculating the vertices without sampling
        np.testing.assert_almost_equal(network.find_lanelet_by_id(50).distance[2], 0.981, 3)
        # test for calculating the vertices with sampling
        # np.testing.assert_almost_equal(network.find_lanelet_by_id(50).distance[2], 90.7, 1)

        # test num of driving lanes
        self.assertEqual(60, len(network.lanelets))

        # test number of traffic lights
        self.assertEqual(12, len(network.traffic_lights))

        # test position of a traffic light
        np.testing.assert_almost_equal(network.find_traffic_light_by_id(9).position, [0.145, 8.317], 3)

    def test_roundabout(self):
        """Test the file roundabout.xodr"""
        name = "roundabout"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of junctions
        self.assertEqual(4, len(network.intersections))

        # test vertices
        lanelet = network.find_lanelet_by_id(17)
        np.testing.assert_almost_equal(15.268, np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]), 3)

        # test for calculating the vertices without sampling
        self.assertEqual(44, len(lanelet.left_vertices))
        # test for calculating the vertices with sampling
        # self.assertEqual(3, len(lanelet.left_vertices))

        lanelet = network.find_lanelet_by_id(4)
        np.testing.assert_almost_equal(3.500, np.linalg.norm(lanelet.left_vertices[0] - lanelet.right_vertices[0]), 3)

        # test length of lane
        # test for calculating the vertices with sampling
        # np.testing.assert_almost_equal(network.find_lanelet_by_id(17).inner_distance[2], 21.69863, 3)
        # test for calculating the vertices without sampling
        np.testing.assert_almost_equal(network.find_lanelet_by_id(17).inner_distance[2], 1.00900, 3)

    def test_crossing_complex_eight_course(self):
        """Test the file CrossingComplex8Course.xodr"""
        name = "CrossingComplex8Course"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of traffic lights
        self.assertEqual(10, len(network.traffic_lights))

        # test number of traffic signs
        self.assertEqual(4, len(network.traffic_signs))

        # test number of priority traffic signs
        self.assertEqual(2, len([s for s in network.traffic_signs if
                                 s.traffic_sign_elements[0].traffic_sign_element_id == TrafficSignIDZamunda.PRIORITY]))

        # test number of yield traffic signs
        self.assertEqual(2, len([s for s in network.traffic_signs if
                                 s.traffic_sign_elements[0].traffic_sign_element_id == TrafficSignIDZamunda.YIELD]))

        # test position of a traffic sign
        np.testing.assert_almost_equal(network.find_traffic_sign_by_id(1).position, [467.03, 498.24], 2)

        # test line marking of a stop lines
        lanelet_with_stop_line = next(la for la in network.lanelets if la.stop_line is not None)
        self.assertEqual(LineMarking.SOLID, lanelet_with_stop_line.stop_line.line_marking)

        # test number of driving lanes
        self.assertEqual(29, len(network.lanelets))

    def test_cul_de_sac(self):
        """Test the file CulDeSac.xodr"""
        name = "CulDeSac"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of lanelets
        self.assertEqual(3, len(network.lanelets))

        # test vertices of lanelet 1
        # test for calculating the vertices without sampling
        self.assertEqual(210, len(network.find_lanelet_by_id(1).left_vertices))
        np.testing.assert_almost_equal([-72.84, -5.19],
                                       network.find_lanelet_by_id(1).left_vertices[0], 2)
        np.testing.assert_almost_equal([31.93, -4.35],
                                       network.find_lanelet_by_id(1).left_vertices[-1], 2)

        # test for calculating the vertices with sampling
        # self.assertEqual(3, len(network.find_lanelet_by_id(1).left_vertices))
        # np.testing.assert_almost_equal([[-72.84, -5.19], [-20.45, -4.77], [31.93, -4.35]],
        #                                network.find_lanelet_by_id(1).left_vertices, 2)

        # test successor / predecessor relation
        self.assertListEqual([2], network.find_lanelet_by_id(1).successor)
        self.assertListEqual([1], network.find_lanelet_by_id(2).predecessor)
        self.assertListEqual([3], network.find_lanelet_by_id(2).successor)
        self.assertEqual([2], network.find_lanelet_by_id(3).predecessor)

    def test_four_way_signal(self):
        """Test the file FourWaySignal.xodr"""
        name = "FourWaySignal"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of traffic lights
        self.assertEqual(10, len(network.traffic_lights))

        # test number of traffic signs
        self.assertEqual(2, len([t for t in network.traffic_signs if not t.virtual]))
        self.assertEqual(7, len([t for t in network.traffic_signs if t.virtual]))

        # test type of traffic signs
        self.assertEqual(TrafficSignIDZamunda.U_TURN,
                         network.find_traffic_sign_by_id(8).traffic_sign_elements[0].traffic_sign_element_id)
        self.assertEqual(TrafficSignIDZamunda.U_TURN,
                         network.find_traffic_sign_by_id(15).traffic_sign_elements[0].traffic_sign_element_id)

        # test position of a traffic light
        np.testing.assert_almost_equal(network.find_traffic_light_by_id(1).position, [13.15, 12.32], 2)

    def test_opendrive_1(self):
        """Test the file opendrive-1.xodr"""
        name = "opendrive-1"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of driving lanes
        self.assertEqual(19, len(network.lanelets))

        # test number of traffic lights
        self.assertEqual(8, len(network.traffic_lights))

        # test correct traffic signs
        self.assertEqual(4, len(network.traffic_signs))
        self.assertEqual(TrafficSignIDZamunda.PRIORITY,
                         network.find_traffic_sign_by_id(3).traffic_sign_elements[0].traffic_sign_element_id)
        self.assertEqual(TrafficSignIDZamunda.YIELD,
                         network.find_traffic_sign_by_id(6).traffic_sign_elements[0].traffic_sign_element_id)
        self.assertEqual(TrafficSignIDZamunda.PRIORITY,
                         network.find_traffic_sign_by_id(9).traffic_sign_elements[0].traffic_sign_element_id)
        self.assertEqual(TrafficSignIDZamunda.YIELD,
                         network.find_traffic_sign_by_id(12).traffic_sign_elements[0].traffic_sign_element_id)

        # test position of traffic sign
        np.testing.assert_almost_equal(network.find_traffic_sign_by_id(9).position, [5.86, 13.78], 2)

        # test number of intersections
        self.assertEqual(1, len(network.intersections))

    def test_poly3_and_border_record(self):
        """Test the file poly3_and_border_record.xodr"""
        name = "poly3_and_border_record"
        scenario = load_and_convert_opendrive(name)

        network = scenario.lanelet_network

        # test number of sidewalks
        self.assertEqual(8, len([la for la in network.lanelets if la.lanelet_type == {LaneletType.SIDEWALK}]))
        # test number of driving lanes
        self.assertEqual(22, len(network.lanelets))

    def test_access_to_user_allow(self):
        name = "straight_road_lane_access"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.PEDESTRIAN}, scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)

    def test_access_to_user_deny(self):
        name = "straight_road_lane_access_deny"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.VEHICLE, RoadUser.TRAIN},
                         scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)

    def test_access_to_user_allow_bi(self):
        name = "straight_road_lane_access_bi"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.PEDESTRIAN}, scenario.lanelet_network.find_lanelet_by_id(2).user_bidirectional)

    def test_access_to_user_deny_bi(self):
        name = "straight_road_lane_access_deny_bi"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.VEHICLE, RoadUser.TRAIN, RoadUser.BICYCLE},
                         scenario.lanelet_network.find_lanelet_by_id(2).user_bidirectional)

    def test_access_mapping(self):
        name = "straight_road_lane_access_autonomous"  # testing ignored types
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.VEHICLE, RoadUser.BICYCLE, RoadUser.PEDESTRIAN, RoadUser.TRAIN},
                         scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)
        name = "straight_road_lane_access_emergency"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.PRIORITY_VEHICLE}, scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)

        name = "straight_road_lane_access_passengerCar"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.CAR}, scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)

        name = "straight_road_lane_access_trucks"
        scenario = load_and_convert_opendrive(name)
        self.assertEqual({RoadUser.TRUCK}, scenario.lanelet_network.find_lanelet_by_id(2).user_one_way)

    def test_mona_east_projection(self):
        name = "MONAEast"
        scenario = load_and_convert_opendrive(name)
        np.testing.assert_almost_equal(scenario.lanelet_network.find_lanelet_by_id(1).center_vertices[0],
                                       np.array([692933.6754881, 5338901.6846093]))


if __name__ == "__main__":
    unittest.main()
